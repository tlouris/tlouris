"""initial schema"""

from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("role", sa.String(32), nullable=False, server_default="viewer"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )
    op.create_table(
        "meters",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("meter_id", sa.String(64), nullable=False, unique=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("basin", sa.String(128), nullable=False),
        sa.Column("gis_link", sa.String(512)),
        sa.Column("pipe_diameter_in", sa.Float()),
        sa.Column("slope", sa.Float()),
        sa.Column("mannings_n", sa.Float()),
        sa.Column("capacity_mgd", sa.Float()),
        sa.Column("install_date", sa.Date()),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
    )
    op.create_table(
        "timeseries_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("meter_id", sa.Integer(), sa.ForeignKey("meters.id", ondelete="CASCADE"), nullable=False),
        sa.Column("timestamp_utc", sa.DateTime(timezone=True), nullable=False),
        sa.Column("flow_mgd", sa.Float(), nullable=False),
        sa.Column("flow_cfs", sa.Float()),
        sa.Column("velocity_fps", sa.Float()),
        sa.Column("level", sa.Float()),
        sa.Column("rainfall_in", sa.Float()),
        sa.Column("quality_flags", sa.JSON()),
        sa.Column("validation_flags", sa.JSON()),
        sa.UniqueConstraint("meter_id", "timestamp_utc", name="uq_meter_ts"),
    )
    op.create_index("ix_meter_ts", "timeseries_records", ["meter_id", "timestamp_utc"])

    op.create_table(
        "file_load_history",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("checksum", sa.String(128), nullable=False),
        sa.Column("rows_received", sa.Integer(), nullable=False),
        sa.Column("rows_inserted", sa.Integer(), nullable=False),
        sa.Column("missing_pct", sa.Float(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("error_message", sa.Text()),
        sa.Column("uploaded_by", sa.String(255), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_table(
        "anomalies",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("meter_id", sa.Integer(), sa.ForeignKey("meters.id", ondelete="CASCADE"), nullable=False),
        sa.Column("anomaly_type", sa.String(64), nullable=False),
        sa.Column("severity", sa.Integer(), nullable=False),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("peak_value", sa.Float()),
        sa.Column("explanation", sa.Text(), nullable=False),
    )
    op.create_index("ix_anomaly_meter_start", "anomalies", ["meter_id", "start_time"])

    op.create_table(
        "alert_rules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("meter_id", sa.Integer(), sa.ForeignKey("meters.id", ondelete="CASCADE")),
        sa.Column("rule_type", sa.String(64), nullable=False),
        sa.Column("threshold", sa.Float(), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("severity_threshold", sa.Integer()),
        sa.Column("suppression_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )
    op.create_table(
        "alert_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("rule_id", sa.Integer(), sa.ForeignKey("alert_rules.id", ondelete="CASCADE"), nullable=False),
        sa.Column("meter_id", sa.Integer(), sa.ForeignKey("meters.id", ondelete="CASCADE")),
        sa.Column("triggered_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="open"),
        sa.Column("acknowledged_by", sa.String(255)),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True)),
        sa.Column("payload", sa.JSON()),
    )


def downgrade() -> None:
    op.drop_table("alert_events")
    op.drop_table("alert_rules")
    op.drop_index("ix_anomaly_meter_start", table_name="anomalies")
    op.drop_table("anomalies")
    op.drop_table("file_load_history")
    op.drop_index("ix_meter_ts", table_name="timeseries_records")
    op.drop_table("timeseries_records")
    op.drop_table("meters")
    op.drop_table("users")
