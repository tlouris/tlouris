from dataclasses import dataclass
from datetime import datetime

import numpy as np
import pandas as pd


@dataclass
class DetectionConfig:
    z_threshold: float = 3.5
    flatline_min_points: int = 8
    change_window: int = 24


def robust_zscore(values: pd.Series) -> pd.Series:
    median = values.median()
    mad = np.median(np.abs(values - median))
    if mad == 0:
        std = values.std()
        if std == 0 or np.isnan(std):
            return pd.Series(np.zeros(len(values)), index=values.index)
        return (values - median) / std
    return 0.6745 * (values - median) / mad


def detect_anomalies(df: pd.DataFrame, config: DetectionConfig | None = None) -> list[dict]:
    """Simple explainable anomaly detector using seasonal median residuals + level shifts."""
    cfg = config or DetectionConfig()
    if df.empty:
        return []

    work = df.sort_values("timestamp_utc").copy()
    work["hour"] = pd.to_datetime(work["timestamp_utc"]).dt.hour
    seasonal = work.groupby("hour")["flow_mgd"].transform("median")
    work["residual"] = work["flow_mgd"] - seasonal
    work["z"] = robust_zscore(work["residual"])

    anomalies: list[dict] = []
    spikes = work[work["z"] > cfg.z_threshold]
    for _, row in spikes.iterrows():
        anomalies.append(
            {
                "anomaly_type": "spike",
                "severity": min(5, int(abs(row.z) // 1)),
                "start_time": row.timestamp_utc,
                "end_time": row.timestamp_utc,
                "peak_value": float(row.flow_mgd),
                "explanation": f"Flow exceeded expected baseline by {row.z:.1f}σ.",
            }
        )

    work["diff"] = work["flow_mgd"].diff().fillna(0)
    flatline_mask = work["diff"].abs() < 1e-4
    run_length = flatline_mask.groupby((flatline_mask != flatline_mask.shift()).cumsum()).transform("size")
    flatlines = work[flatline_mask & (run_length >= cfg.flatline_min_points)]
    if not flatlines.empty:
        anomalies.append(
            {
                "anomaly_type": "dropout_flatline",
                "severity": 4,
                "start_time": flatlines.iloc[0].timestamp_utc,
                "end_time": flatlines.iloc[-1].timestamp_utc,
                "peak_value": float(flatlines.iloc[0].flow_mgd),
                "explanation": "Sensor appears flatlined for sustained interval.",
            }
        )

    rolling_before = work["flow_mgd"].rolling(cfg.change_window).mean()
    rolling_after = work["flow_mgd"].shift(-cfg.change_window).rolling(cfg.change_window).mean()
    level_shift = (rolling_after - rolling_before).abs()
    if level_shift.max(skipna=True) > work["flow_mgd"].std() * 2:
        idx = int(level_shift.idxmax())
        row = work.loc[idx]
        anomalies.append(
            {
                "anomaly_type": "level_shift",
                "severity": 3,
                "start_time": row.timestamp_utc,
                "end_time": row.timestamp_utc,
                "peak_value": float(row.flow_mgd),
                "explanation": "Detected sustained baseline shift via rolling mean delta.",
            }
        )

    return anomalies
