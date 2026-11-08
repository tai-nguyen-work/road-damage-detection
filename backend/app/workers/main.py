from redis import Redis
from rq import Queue, Worker

from app.core.config import get_settings
from app.core.logging import configure_logging


def main() -> None:
    configure_logging()
    with Redis.from_url(str(get_settings().redis_url)) as connection:
        worker = Worker([Queue("processing", connection=connection)], connection=connection)
        worker.work(with_scheduler=True, logging_level="INFO")


if __name__ == "__main__":
    main()
