# KeepIQ

KeepIQ is a local-first Telegram bot + Mini App for personal AI inbox capture.

## What it does

- Accepts text, links, forwarded messages, voice, audio, photos, screenshots, and documents.
- Saves the original incoming item before analysis.
- Runs AI or heuristic classification into task, reminder, event, note, list, reply later, or saved.
- Keeps uncertain items in Inbox for confirmation.
- Exposes a FastAPI backend for the Telegram Mini App.
- Delivers reminders and morning/evening digests through APScheduler.

## Architecture summary

- `bot/`: aiogram bot handlers and inline actions.
- `api/`: FastAPI app and Mini App endpoints.
- `services/`: orchestration for ingestion, analysis, search, digests, reminders.
- `ai/`: provider abstraction with OpenAI and heuristic fallback.
- `parsers/`: date, text, ticket and content helpers.
- `storage/`: file storage abstraction, local adapter for MVP.
- `models/`, `repositories/`, `schemas/`, `db/`: persistence layer.
- `jobs/`: APScheduler runner for reminders and digests.
- `mini_app/`: React/Vite Telegram Mini App frontend.
- `tests/`: key MVP tests.

## User scenarios covered in MVP

1. `напомни завтра позвонить Ване` becomes reminder/task proposal with extracted date when available.
2. `купить батарейки, корм и шампунь` becomes a list. This is better than three separate tasks for a grocery bundle.
3. Voice is stored, transcribed through provider, then analyzed as structured candidates.
4. Screenshot/photo is stored, analyzed through provider, and routed to Inbox with proposed type.
5. Ticket/booking is detected through document name or text hints, proposed as event + reminder.
6. Forwarded message is proposed as `reply_later` when message intent suggests follow-up.
7. Mini App has Dashboard, Inbox, Today, Tasks, Events, Lists, Notes, Search.
8. Manual correction keeps the original source while updating the final object.
9. Reminder delivery includes quick actions for complete and snooze.
10. Morning/evening digests are generated from user data.

## Local setup

### 1. Prepare environment

- Install Python 3.10+.
- Install Node.js 22+.
- Copy `.env.example` to `.env` and fill `BOT_TOKEN` and `OPENAI_API_KEY`.

### 2. Create Python virtual environment

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -e .[dev]
```

### 3. Optional PostgreSQL

```powershell
docker compose up -d postgres
```

Then set `DATABASE_URL=postgresql+asyncpg://keepiq:keepiq@localhost:5432/keepiq` in `.env`.

### 4. Migrations

```powershell
.\.venv\Scripts\alembic.exe upgrade head
```

### 5. Run backend

```powershell
.\.venv\Scripts\python.exe -m uvicorn api.app:app --reload --host 127.0.0.1 --port 8000
```

### 6. Run bot

```powershell
.\.venv\Scripts\python.exe -m bot.main
```

### 7. Run scheduler

```powershell
.\.venv\Scripts\python.exe -m jobs.runner
```

### 8. Run Mini App frontend

```powershell
cd mini_app
cmd /c npm.cmd install
cmd /c npm.cmd run dev
```

### 9. Run tests

```powershell
.\.venv\Scripts\python.exe -m pytest
```

## Publishing Mini App

Telegram Mini Apps require HTTPS. For local development use a public tunnel. For production the recommended shape is static frontend hosting + separate backend API.

Recommended production shape:

- Frontend: Cloudflare Pages or Vercel with a custom HTTPS domain.
- Backend API + bot worker + scheduler: Render, Railway, Fly.io, or your own VPS with Docker.
- Telegram BotFather Mini App URL: the public frontend URL.

## v2 improvements

- Better OCR extraction pipeline with provider selection.
- Semantic search index.
- Duplicate incoming detection.
- Vendor-specific ticket parsers.
- Rich edit flows inside Mini App.
- Background job queue for heavier media processing.
