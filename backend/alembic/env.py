from typing import Any

from sqlalchemy import create_engine, pool

from alembic import context
from app.core.config import get_settings
from app.models import Base


def include_name(name: str | None, type_: str, parent_names: dict[str, Any]) -> bool:
    # PostGIS owns this public reference table; Alembic must never drop it.
    return not (type_ == "table" and name == "spatial_ref_sys")


def run_migrations() -> None:
    url = str(get_settings().database_url)
    if context.is_offline_mode():
        context.configure(url=url, target_metadata=Base.metadata, literal_binds=True)
        with context.begin_transaction():
            context.run_migrations()
    else:
        engine = create_engine(
            url, poolclass=pool.NullPool, connect_args={"options": "-c search_path=public"}
        )
        with engine.connect() as connection:
            context.configure(
                connection=connection,
                target_metadata=Base.metadata,
                compare_type=True,
                include_name=include_name,
            )
            with context.begin_transaction():
                context.run_migrations()
        engine.dispose()


run_migrations()
