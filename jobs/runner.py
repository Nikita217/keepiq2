from __future__ import annotations

import asyncio

from jobs.scheduler import SchedulerService
from utils.logging import configure_logging


async def main() -> None:
    configure_logging()
    scheduler = SchedulerService()
    scheduler.start()
    while True:
        await asyncio.sleep(3600)


if __name__ == "__main__":
    asyncio.run(main())
