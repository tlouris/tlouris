from datetime import datetime

import numpy as np
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import and_, func
from sqlalchemy.orm import Session
import pandas as pd

from app.api.deps import require_roles
from app.core.config import settings
from app.core.security import create_token, verify_password
from app.db.session import get_db
from app.models.entities import Anomaly, FileLoadHistory, Meter, TimeSeriesRecord, User
from app.schemas.common import AnomalyRead, MeterCreate, MeterRead, MeterSummary, SeriesPoint
from app.services.anomaly import detect_anomalies
from app.services.capacity import compute_capacity_mgd, utilization

router = APIRouter()


@router.post("/auth/token")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Bad credentials")
    return {
        "access_token": create_token(user.email, settings.access_token_minutes),
        "refresh_token": create_token(user.email, settings.refresh_token_minutes),
        "token_type": "bearer",
    }


@router.get("/meters", response_model=list[MeterRead])
def list_meters(db: Session = Depends(get_db), _: User = Depends(require_roles("admin", "engineer", "viewer"))):
    return db.query(Meter).order_by(Meter.basin, Meter.meter_id).all()


@router.post("/meters", response_model=MeterRead)
def create_meter(payload: MeterCreate, db: Session = Depends(get_db), _: User = Depends(require_roles("admin"))):
    meter = Meter(**payload.model_dump())
    if not meter.capacity_mgd and meter.pipe_diameter_in and meter.slope and meter.mannings_n:
        meter.capacity_mgd = compute_capacity_mgd(meter.pipe_diameter_in, meter.slope, meter.mannings_n)
    db.add(meter)
    db.commit()
    db.refresh(meter)
    return meter


@router.get("/meters/{meter_id}/series", response_model=list[SeriesPoint])
def meter_series(
    meter_id: int,
    start: datetime,
    end: datetime,
    granularity: str = Query("raw", pattern="^(raw|15m|1h|1d)$"),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin", "engineer", "viewer")),
):
    meter = db.get(Meter, meter_id)
    if not meter:
        raise HTTPException(status_code=404, detail="Meter not found")

    q = db.query(TimeSeriesRecord).filter(
        and_(
            TimeSeriesRecord.meter_id == meter_id,
            TimeSeriesRecord.timestamp_utc >= start,
            TimeSeriesRecord.timestamp_utc <= end,
        )
    )
    rows = q.order_by(TimeSeriesRecord.timestamp_utc).all()
    points = [
        SeriesPoint(
            timestamp_utc=r.timestamp_utc,
            flow_mgd=r.flow_mgd,
            utilization_pct=utilization(r.flow_mgd, meter.capacity_mgd or 1),
            exceedance=utilization(r.flow_mgd, meter.capacity_mgd or 1) > 100,
        )
        for r in rows
    ]
    if granularity == "raw":
        return points
    df = pd.DataFrame([p.model_dump() for p in points])
    if df.empty:
        return []
    df["timestamp_utc"] = pd.to_datetime(df["timestamp_utc"])  # UTC persisted
    rule = {"15m": "15min", "1h": "1h", "1d": "1d"}[granularity]
    agg = df.set_index("timestamp_utc").resample(rule).agg({"flow_mgd": "mean", "utilization_pct": "max", "exceedance": "max"}).dropna().reset_index()
    return [SeriesPoint(**row) for row in agg.to_dict("records")]


@router.get("/meters/{meter_id}/summary", response_model=MeterSummary)
def meter_summary(meter_id: int, start: datetime, end: datetime, db: Session = Depends(get_db), _: User = Depends(require_roles("admin", "engineer", "viewer"))):
    meter = db.get(Meter, meter_id)
    if not meter:
        raise HTTPException(status_code=404, detail="Meter not found")
    rows = db.query(TimeSeriesRecord.flow_mgd).filter(
        and_(TimeSeriesRecord.meter_id == meter_id, TimeSeriesRecord.timestamp_utc >= start, TimeSeriesRecord.timestamp_utc <= end)
    ).all()
    values = np.array([r[0] for r in rows], dtype=float)
    if values.size == 0:
        raise HTTPException(status_code=404, detail="No data")
    util = values / (meter.capacity_mgd or 1) * 100
    return MeterSummary(
        meter_id=meter.meter_id,
        avg_flow_mgd=float(values.mean()),
        min_flow_mgd=float(values.min()),
        max_flow_mgd=float(values.max()),
        p95_flow_mgd=float(np.percentile(values, 95)),
        p99_flow_mgd=float(np.percentile(values, 99)),
        avg_utilization_pct=float(util.mean()),
        peak_utilization_pct=float(util.max()),
        total_volume_mg=float(values.sum() * 0.25),
        count_exceedances=int((util > 100).sum()),
    )


@router.get("/meters/{meter_id}/anomalies", response_model=list[AnomalyRead])
def meter_anomalies(meter_id: int, start: datetime, end: datetime, db: Session = Depends(get_db), _: User = Depends(require_roles("admin", "engineer", "viewer"))):
    return db.query(Anomaly).filter(and_(Anomaly.meter_id == meter_id, Anomaly.start_time >= start, Anomaly.end_time <= end)).all()


@router.get("/basins/summary")
def basin_summary(start: datetime, end: datetime, db: Session = Depends(get_db), _: User = Depends(require_roles("admin", "engineer", "viewer"))):
    rows = (
        db.query(Meter.basin, func.avg(TimeSeriesRecord.flow_mgd), func.max(TimeSeriesRecord.flow_mgd), func.count())
        .join(TimeSeriesRecord, Meter.id == TimeSeriesRecord.meter_id)
        .filter(and_(TimeSeriesRecord.timestamp_utc >= start, TimeSeriesRecord.timestamp_utc <= end))
        .group_by(Meter.basin)
        .all()
    )
    return [{"basin": r[0], "avg_flow_mgd": r[1], "peak_flow_mgd": r[2], "points": r[3]} for r in rows]


@router.post("/meters/{meter_id}/import")
def import_meter_data(meter_id: int, file: UploadFile = File(...), db: Session = Depends(get_db), _: User = Depends(require_roles("admin", "engineer"))):
    content = file.file.read()
    ext = file.filename.split(".")[-1].lower()
    if ext == "csv":
        df = pd.read_csv(pd.io.common.BytesIO(content))
    elif ext in {"xlsx", "xls"}:
        df = pd.read_excel(pd.io.common.BytesIO(content))
    else:
        raise HTTPException(status_code=400, detail="Unsupported file")
    required_cols = {"timestamp_utc", "flow_mgd"}
    if not required_cols.issubset(df.columns):
        raise HTTPException(status_code=400, detail="Missing required columns")

    inserted = 0
    for _, row in df.iterrows():
        flow = max(0.0, float(row["flow_mgd"]))
        ts = pd.to_datetime(row["timestamp_utc"], utc=True).to_pydatetime()
        exists = db.query(TimeSeriesRecord.id).filter(and_(TimeSeriesRecord.meter_id == meter_id, TimeSeriesRecord.timestamp_utc == ts)).first()
        if exists:
            continue
        record = TimeSeriesRecord(meter_id=meter_id, timestamp_utc=ts, flow_mgd=flow, validation_flags={"non_negative": flow >= 0})
        db.add(record)
        inserted += 1

    load = FileLoadHistory(
        filename=file.filename,
        checksum=str(hash(content)),
        rows_received=len(df),
        rows_inserted=inserted,
        missing_pct=float(df["flow_mgd"].isna().mean() * 100),
        status="success",
        uploaded_by="api-user",
    )
    db.add(load)
    db.commit()
    return {"rows_inserted": inserted, "rows_received": len(df)}


@router.post("/meters/{meter_id}/anomalies/run")
def run_anomaly(meter_id: int, db: Session = Depends(get_db), _: User = Depends(require_roles("admin", "engineer"))):
    rows = db.query(TimeSeriesRecord.timestamp_utc, TimeSeriesRecord.flow_mgd).filter(TimeSeriesRecord.meter_id == meter_id).all()
    df = pd.DataFrame(rows, columns=["timestamp_utc", "flow_mgd"])
    results = detect_anomalies(df)
    for result in results:
        db.add(Anomaly(meter_id=meter_id, **result))
    db.commit()
    return {"created": len(results)}
