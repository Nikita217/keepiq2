from __future__ import annotations

import asyncio

from db.bootstrap import create_all
from db.session import engine
from jobs.scheduler import SchedulerService
from utils.logging import configure_logging


async def main() -> None:
    configure_logging()
    await create_all(engine)
    scheduler = SchedulerService()
    scheduler.start()
    while True:
        await asyncio.sleep(3600)


if __name__ == "__main__":
    asyncio.run(main())