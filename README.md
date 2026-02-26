# Flow Capacity Monitor

Production-oriented scaffold for wastewater flow capacity monitoring with ingestion, utilization analytics, anomaly detection, alerting, and dashboards.

## Architecture

- `backend/`: FastAPI, SQLAlchemy, Alembic, Celery, anomaly/capacity services, OpenAPI docs.
- `frontend/`: Next.js TypeScript pages for login, overview, meter detail, comparisons, alerts, admin.
- `infra/`: Docker Compose stack (API, worker, frontend, TimescaleDB/Postgres, Redis).

## Key capabilities implemented

- CSV/XLSX ingestion endpoint with dedupe `(meter_id, timestamp_utc)` and file load history logging.
- Meter metadata model + time-series schema with validation flags and quality fields.
- Capacity computations (Manning equation), utilization %, exceedance calculation.
- Aggregated series API via `granularity=raw|15m|1h|1d`.
- Meter summary stats (avg/min/max/p95/p99/utilization/volume/exceedances).
- Explainable anomaly detection (spike, flatline, level shift) with robust z-score + rolling shift checks.
- Alert rule and event schema for threshold/severity/missing-data workflows.
- JWT authentication scaffold with role enforcement (`admin`, `engineer`, `viewer`).

## Local run (one command)

```bash
cd infra
docker compose up --build
```

Services:
- API: http://localhost:8000/docs
- Frontend: http://localhost:3000

## Setup details

### 1) Migrations

```bash
docker compose exec api alembic upgrade head
```

### 2) Seed synthetic data

```bash
docker compose exec api python seed.py
```

Seeded login:
- `admin@example.com`
- `admin123`

## API endpoints

- `POST /auth/token`
- `GET|POST /meters`
- `GET /meters/{id}/series?start&end&granularity`
- `GET /meters/{id}/summary?start&end`
- `GET /meters/{id}/anomalies?start&end`
- `POST /meters/{id}/import` (CSV/XLSX)
- `POST /meters/{id}/anomalies/run`
- `GET /basins/summary?start&end`

## Background jobs

- Celery worker enabled.
- Nightly anomaly job task stub (`run_nightly_anomaly_job`) for scheduler integration.

## Testing

Backend unit tests:

```bash
cd backend
pytest
```

Includes tests for:
- Manning capacity + utilization math.
- Synthetic spike anomaly detection.

## Notes for production hardening

- Move JWT secret + DB credentials to secret manager.
- Add request-id middleware and structured JSON logging sink.
- Configure Timescale hypertables + continuous aggregates for `1h` and `1d` rollups.
- Add SMTP/webhook adapters and alert suppression persistence checks.
- Add frontend API integration, auth flow with refresh tokens, and CSV export controls.
