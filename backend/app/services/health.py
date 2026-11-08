import logging

from redis import Redis
from sqlalchemy import text

from app.core.config import get_settings
from app.db.session import get_engine
from app.schemas.health import HealthResponse

logger = logging.getLogger(__name__)


def check_health() -> HealthResponse:
    database = postgis = schema = redis = "error"
    try:
        with get_engine().connect() as connection:
            connection.execute(text("SELECT 1"))
            database = "ok"
            connection.execute(text("SELECT PostGIS_Version()"))
            postgis = "ok"
            revision = connection.execute(text("SELECT version_num FROM alembic_version")).scalar()
            if revision == "0001_initial":
                schema = "ok"
    except Exception:
        logger.warning("database_readiness_failed")
    try:
        with Redis.from_url(
            str(get_settings().redis_url), socket_connect_timeout=2, socket_timeout=2
        ) as client:
            if client.ping():
                redis = "ok"
    except Exception:
        logger.warning("redis_readiness_failed")
    return HealthResponse(
        status="ok" if all(v == "ok" for v in (database, postgis, schema, redis)) else "degraded",
        database=database,
        postgis=postgis,
        schema=schema,
        redis=redis,
    )
