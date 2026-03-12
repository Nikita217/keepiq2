from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import auth, dashboard, events, inbox, lists, notes, objects, reminders, search, settings, tasks
from db.bootstrap import create_all
from db.session import engine
from utils.logging import configure_logging
from utils.settings import get_settings

configure_logging()
settings_obj = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    await create_all(engine)
    yield


app = FastAPI(title=settings_obj.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings_obj.cors_allowed_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(inbox.router)
app.include_router(tasks.router)
app.include_router(events.router)
app.include_router(reminders.router)
app.include_router(lists.router)
app.include_router(notes.router)
app.include_router(objects.router)
app.include_router(search.router)
app.include_router(settings.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
