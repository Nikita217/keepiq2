# KeepIQ

KeepIQ is a Telegram bot + Mini App for AI-first inbox capture.

The main product idea is simple: send anything to the bot, let AI understand what it is, then either answer immediately or route it into the right object with minimal manual correction.

## What the bot accepts

- Text messages
- Links
- Forwarded messages
- Voice messages
- Audio files
- Photos and screenshots
- Documents

## Current AI triage flow

1. KeepIQ stores the original incoming item first.
2. It builds a unified context for analysis:
   - incoming type
   - filename
   - mime type
   - caption/user text
   - transcript for audio
   - extracted text for plain-text documents
   - forwarded flag
3. AI decides what the item is:
   - `task`
   - `reminder`
   - `event`
   - `note`
   - `list`
   - `reply_later`
   - `saved`
   - `answer`
4. If confidence is high and confirmation is not needed, KeepIQ materializes the result automatically.
5. If the item is ambiguous, it stays in Inbox with AI explanation, clarification question, and override actions.

## Implemented behavior in this version

### 1. AI-first routing

The bot now analyzes all available context, not just the raw text.

Examples:
- A screenshot of a chat can be classified as `reply_later`, `note`, `task`, or `answer`.
- A concert ticket can become `event` plus linked `reminder`.
- A voice note with several action items can become multiple tasks.
- A direct user question can be classified as `answer` and the bot can reply immediately.

### 2. Better confirmation flow

Telegram and Mini App confirmations now resolve the item, not just flip a review flag.

That means:
- `Confirm` now finalizes the AI decision.
- `Save as task/note/list/event/reply_later` reuses the same source item.
- Re-confirming an already materialized item updates linked objects instead of creating duplicates.

### 3. Linked object creation

The object builder now keeps related entities connected:
- reminder text can create both a task and a linked reminder
- ticket/event parsing can create an event and a linked reminder
- `remind_on` is filled from `remind_at`

### 4. Answer mode

If AI decides the incoming item is primarily a question, it can return `answer`.

In this case KeepIQ:
- stores the incoming item
- saves the AI answer in item metadata
- replies to the user directly
- still allows manual re-routing if the user wants to save it as a note or task

### 5. Better file context handling

For files, the bot now includes:
- caption text
- file name
- mime type
- forwarding signal

For plain-text-like documents (`.txt`, `.md`, `.csv`, `.json`, `.log`, `.yaml`, `.yml` and `text/*`) it also extracts text directly for analysis.

### 6. Richer Inbox in Mini App

Inbox items now expose:
- AI answer
- clarification question
- resolved object type
- direct resolve actions

## Important files

Core intake and AI routing:
- `bot/handlers/content.py`
- `services/ingestion.py`
- `services/analysis.py`
- `parsers/text.py`
- `ai/openai_provider.py`

Resolution and object creation:
- `services/inbox_actions.py`
- `services/object_builder.py`
- `repositories/incoming.py`
- `api/routes/inbox.py`

Mini App:
- `mini_app/src/api.ts`
- `mini_app/src/types.ts`
- `mini_app/src/pages/InboxPage.tsx`
- `mini_app/src/pages/TasksPage.tsx`

## Architecture summary

- `bot/`: aiogram handlers and callbacks
- `api/`: FastAPI backend for Mini App
- `services/`: orchestration, ingestion, digests, resolution, reminders
- `ai/`: provider abstraction with OpenAI and heuristic fallback
- `parsers/`: date and heuristic content routing
- `storage/`: file storage abstraction
- `models/`, `repositories/`, `schemas/`, `db/`: persistence layer
- `jobs/`: APScheduler reminder/digest jobs
- `mini_app/`: React/Vite frontend
- `tests/`: local regression coverage

## Local setup

### 1. Prepare environment

- Install Python 3.10+
- Install Node.js 22+
- Copy `.env.example` to `.env`
- Fill at least:
  - `BOT_TOKEN`
  - `OPENAI_API_KEY`

### 2. Python environment

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

Then set:

```env
DATABASE_URL=postgresql+asyncpg://keepiq:keepiq@localhost:5432/keepiq
```

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
.\.venv\Scripts\python.exe -m pytest -q
```

## Deploy shape

Recommended production shape:
- Frontend Mini App: Cloudflare Pages
- Backend API + bot + scheduler: Render
- Git remote: GitHub

## Update GitHub / Render / Cloudflare after code changes

### Push code to GitHub

```powershell
git status
git add .
git commit -m "Improve AI triage and inbox resolution"
git push origin master
```

### Render update

Render services should redeploy from the updated GitHub repo.

Typical services:
- API service
- bot worker
- scheduler worker

Check on Render:
- Python version is compatible with 3.10+
- environment variables are set
- `OPENAI_API_KEY` is present in production
- `BOT_TOKEN` is present
- `MINI_APP_PUBLIC_URL` points to the Cloudflare Pages URL
- `DATABASE_URL` points to production database
- start commands are correct:
  - API: `python -m uvicorn api.app:app --host 0.0.0.0 --port $PORT`
  - bot: `python -m bot.main`
  - scheduler: `python -m jobs.runner`

If Render does not auto-deploy, trigger manual deploy from the dashboard.

### Cloudflare Pages update

Cloudflare Pages should rebuild from the same GitHub repo.

Check on Cloudflare Pages:
- project points to `mini_app/` as the frontend root if configured that way
- build command is `npm run build`
- output directory is `dist`
- environment variable `VITE_API_URL` points to the public Render API URL

After Cloudflare deploys, update BotFather / Mini App settings if the public Pages domain changed.

## Current known limitations

- OCR for arbitrary images is not yet separated into a dedicated pipeline; image understanding currently relies on the AI provider plus any supplied caption/context.
- Binary document formats like PDF/DOCX are not yet parsed into full text in the local fallback path.
- `answer` mode is strongest with OpenAI enabled; heuristic fallback returns a safe generic answer classification.

## Regression coverage added

Tests now explicitly cover:
- reminder text creates linked task + reminder
- question text becomes `answer`
- repeated manual resolve does not duplicate tasks
