import uuid
from datetime import datetime
from typing import Any

from geoalchemy2 import Geography, WKBElement
from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


def point_column(nullable: bool = True) -> Any:
    return mapped_column(Geography("POINT", srid=4326, spatial_index=False), nullable=nullable)


class Media(Base):
    __tablename__ = "media"
    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    kind: Mapped[str] = mapped_column(Enum("image", "video", name="media_kind"))
    original_filename: Mapped[str] = mapped_column(String(255))
    mime_type: Mapped[str] = mapped_column(String(100))
    storage_path: Mapped[str] = mapped_column(String(1024), unique=True)
    sha256: Mapped[str] = mapped_column(String(64), index=True)
    width: Mapped[int] = mapped_column(Integer)
    height: Mapped[int] = mapped_column(Integer)
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    captured_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    status: Mapped[str] = mapped_column(String(32), server_default="uploaded")
    gps_point: Mapped[WKBElement | None] = point_column()
    location_source: Mapped[str | None] = mapped_column(String(64))
    location_accuracy_m: Mapped[float | None] = mapped_column(Float)
    gps_timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        CheckConstraint("width > 0 AND height > 0", name="ck_media_dimensions"),
        CheckConstraint("duration_ms >= 0", name="ck_media_duration"),
        CheckConstraint("location_accuracy_m >= 0", name="ck_media_accuracy"),
        CheckConstraint("gps_point IS NULL OR location_source IS NOT NULL", name="ck_media_source"),
        Index("ix_media_gps_point", "gps_point", postgresql_using="gist"),
    )


class ProcessingJob(Base):
    __tablename__ = "processing_jobs"
    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    media_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("media.id", ondelete="CASCADE"), index=True
    )
    status: Mapped[str] = mapped_column(
        Enum("queued", "running", "completed", "failed", name="job_status"), server_default="queued"
    )
    progress: Mapped[int] = mapped_column(Integer, server_default="0")
    error_message: Mapped[str | None] = mapped_column(String(2000))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    model_version: Mapped[str] = mapped_column(String(255))
    config_json: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    __table_args__ = (
        CheckConstraint("progress BETWEEN 0 AND 100", name="ck_job_progress"),
        UniqueConstraint("id", "media_id", name="uq_job_media"),
        Index(
            "ix_job_one_active_per_media",
            "media_id",
            unique=True,
            postgresql_where=text("status IN ('queued', 'running')"),
        ),
    )


class Detection(Base):
    __tablename__ = "detections"
    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    media_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("media.id", ondelete="CASCADE"), index=True
    )
    job_id: Mapped[uuid.UUID] = mapped_column(UUID)
    frame_index: Mapped[int | None] = mapped_column(Integer)
    frame_timestamp_ms: Mapped[int | None] = mapped_column(Integer)
    damage_type: Mapped[str] = mapped_column(String(100), index=True)
    original_label: Mapped[str] = mapped_column(String(255))
    confidence: Mapped[float] = mapped_column(Float)
    bbox_x1: Mapped[float] = mapped_column(Float)
    bbox_y1: Mapped[float] = mapped_column(Float)
    bbox_x2: Mapped[float] = mapped_column(Float)
    bbox_y2: Mapped[float] = mapped_column(Float)
    point: Mapped[WKBElement | None] = point_column()
    location_method: Mapped[str | None] = mapped_column(String(64))
    location_accuracy_m: Mapped[float | None] = mapped_column(Float)
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    model_version: Mapped[str] = mapped_column(String(255))
    annotated_image_path: Mapped[str | None] = mapped_column(String(1024))
    __table_args__ = (
        ForeignKeyConstraint(
            ["job_id", "media_id"],
            ["processing_jobs.id", "processing_jobs.media_id"],
            ondelete="CASCADE",
            name="fk_detection_job_media",
        ),
        CheckConstraint("confidence BETWEEN 0 AND 1", name="ck_detection_confidence"),
        CheckConstraint(
            "bbox_x1 >= 0 AND bbox_y1 >= 0 AND bbox_x2 > bbox_x1 AND bbox_y2 > bbox_y1",
            name="ck_detection_bbox",
        ),
        CheckConstraint("frame_index >= 0 AND frame_timestamp_ms >= 0", name="ck_detection_frame"),
        CheckConstraint("location_accuracy_m >= 0", name="ck_detection_accuracy"),
        CheckConstraint("point IS NULL OR location_method IS NOT NULL", name="ck_detection_method"),
        Index("ix_detections_point", "point", postgresql_using="gist"),
    )


class GpsTrackPoint(Base):
    __tablename__ = "gps_track_points"
    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    media_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("media.id", ondelete="CASCADE"))
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    point: Mapped[WKBElement] = point_column(nullable=False)
    accuracy_m: Mapped[float | None] = mapped_column(Float)
    __table_args__ = (
        CheckConstraint("accuracy_m >= 0", name="ck_track_accuracy"),
        Index("ix_track_media_recorded_at", "media_id", "recorded_at"),
        Index("ix_track_point", "point", postgresql_using="gist"),
    )
