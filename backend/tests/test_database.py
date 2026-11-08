"""Integration tests use only an explicitly configured disposable PostGIS database."""

import os
import uuid

import pytest
from sqlalchemy import create_engine, text


@pytest.mark.skipif(not os.environ.get("TEST_DATABASE_URL"), reason="TEST_DATABASE_URL required")
def test_postgis_schema_and_unlocated() -> None:
    engine = create_engine(os.environ["TEST_DATABASE_URL"])
    try:
        with engine.connect() as connection, connection.begin():
            assert connection.scalar(text("SELECT PostGIS_Version()"))
            assert (
                connection.scalar(text("SELECT version_num FROM alembic_version")) == "0001_initial"
            )
            for table in ("media", "processing_jobs", "detections", "gps_track_points"):
                assert connection.scalar(text("SELECT to_regclass(:name)"), {"name": table})
            media_id = uuid.uuid4()
            connection.execute(
                text("""
                INSERT INTO media (id, kind, original_filename, mime_type, storage_path,
                                   sha256, width, height)
                VALUES (:id, 'image', 'test.jpg', 'image/jpeg', :path, :sha, 640, 480)
            """),
                {"id": media_id, "path": f"test/{media_id}", "sha": "a" * 64},
            )
            assert connection.scalar(
                text("SELECT gps_point IS NULL FROM media WHERE id=:id"), {"id": media_id}
            )
            connection.rollback()
    finally:
        engine.dispose()
