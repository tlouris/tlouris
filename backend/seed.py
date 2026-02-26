"""Seed script with synthetic meter and 15-minute flow data."""

from datetime import datetime, timedelta, timezone
import math
import random

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.entities import Meter, TimeSeriesRecord, User
from app.services.capacity import compute_capacity_mgd


def run():
    db = SessionLocal()
    if not db.query(User).filter(User.email == "admin@example.com").first():
        db.add(User(email="admin@example.com", hashed_password=hash_password("admin123"), role="admin"))
    if db.query(Meter).count() > 0:
        db.commit()
        db.close()
        return

    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    for i in range(1, 6):
        meter = Meter(
            meter_id=f"M{i:03d}",
            name=f"Meter {i}",
            basin=f"Basin {((i - 1) % 2) + 1}",
            pipe_diameter_in=24.0,
            slope=0.002,
            mannings_n=0.013,
            status="active",
        )
        meter.capacity_mgd = compute_capacity_mgd(24.0, 0.002, 0.013)
        db.add(meter)
        db.flush()

        for step in range(0, 24 * 14 * 4):
            ts = now - timedelta(minutes=15 * step)
            base = 3.0 + math.sin(step / 12) * 0.4
            storm = 4.5 if 200 < step < 230 and i == 1 else 0.0
            flow = max(0.1, base + storm + random.uniform(-0.15, 0.15))
            db.add(TimeSeriesRecord(meter_id=meter.id, timestamp_utc=ts, flow_mgd=flow))

    db.commit()
    db.close()


if __name__ == "__main__":
    run()
