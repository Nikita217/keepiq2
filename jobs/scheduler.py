from __future__ import annotations

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select

from db.session import SessionLocal
from models import DailyDigestSettings, IncomingItem, User
from services.digests import DigestService
from services.reminders import ReminderService
from services.telegram_bot import TelegramNotificationService
from utils.time import now_local


class SchedulerService:
    def __init__(self) -> None:
        self.scheduler = AsyncIOScheduler(timezone=now_local().tzinfo)
        self.notifications = TelegramNotificationService()

    def configure(self) -> None:
        self.scheduler.add_job(self.process_due_reminders, "interval", minutes=1, id="due-reminders", replace_existing=True)
        self.scheduler.add_job(self.process_digests, "interval", minutes=1, id="digests", replace_existing=True)

    def start(self) -> None:
        self.configure()
        self.scheduler.start()

    async def process_due_reminders(self) -> None:
        async with SessionLocal() as session:
            service = ReminderService(session)
            reminders = await service.due(now_local())
            for reminder in reminders:
                user = await session.get(User, reminder.user_id)
                source = await session.get(IncomingItem, reminder.source_incoming_item_id) if reminder.source_incoming_item_id else None
                if user is None:
                    continue
                await self.notifications.send_reminder(user, reminder, source)
                reminder.sent_at = now_local()
            await session.commit()

    async def process_digests(self) -> None:
        current = now_local()
        current_hm = current.strftime("%H:%M")
        async with SessionLocal() as session:
            settings_rows = (await session.execute(select(DailyDigestSettings))).scalars().all()
            for digest_settings in settings_rows:
                user = await session.get(User, digest_settings.user_id)
                if user is None:
                    continue
                service = DigestService(session)
                if digest_settings.morning_enabled and digest_settings.morning_time == current_hm:
                    digest = await service.build_morning_digest(user.id, current.date())
                    await self.notifications.send_digest(user, digest_settings, digest.title, digest.lines)
                if digest_settings.evening_enabled and digest_settings.evening_time == current_hm:
                    digest = await service.build_evening_digest(user.id, current.date())
                    await self.notifications.send_digest(user, digest_settings, digest.title, digest.lines)
