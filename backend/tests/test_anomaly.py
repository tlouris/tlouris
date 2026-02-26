from datetime import datetime, timedelta, timezone
import pandas as pd

from app.services.anomaly import detect_anomalies


def test_detect_spike():
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    rows = []
    for i in range(96):
        rows.append({"timestamp_utc": start + timedelta(minutes=15 * i), "flow_mgd": 2.0})
    rows[50]["flow_mgd"] = 15.0
    result = detect_anomalies(pd.DataFrame(rows))
    assert any(r["anomaly_type"] == "spike" for r in result)
