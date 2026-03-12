# KeepIQ

KeepIQ is a Telegram bot + Mini App for AI-first inbox capture.

The product goal is simple: send anything to the bot, let AI understand what it is, and then either answer immediately or offer the next best actions in a human way.

## What the bot accepts

- text messages
- links
- forwarded messages
- voice messages
- audio files
- photos and screenshots
- documents

## Current intake logic

1. KeepIQ stores the original incoming item first.
2. It builds a unified context for analysis:
   - incoming type
   - filename
   - mime type
   - caption / user text
   - transcript for audio
   - extracted text for plain-text documents
   - forwarded flag
3. AI decides what the item actually is:
   - `task`
   - `reminder`
   - `event`
   - `note`
   - `list`
   - `reply_later`
   - `saved`
   - `answer`
4. Instead of generic buttons, the bot now prepares adaptive next-step actions.
5. The user chooses from those actions, and KeepIQ materializes or updates the correct object.

## What changed in this version

### 1. AI now thinks in next steps, not just labels

The assistant now returns:
- natural Russian response text for the user
- detected object type
- extracted candidates
- adaptive suggested actions

Examples:
- `купить шапку` is treated as a task, not as a generic unknown item
- `напомни завтра позвонить Ване` becomes a reminder flow with concrete time suggestions
- a screenshot of a chat can become `reply_later`, `task`, `note`, or `answer`
- a direct question can be answered immediately as `answer`

### 2. Adaptive action buttons

Telegram buttons are no longer generic by default.

Instead, AI suggests actions that match the detected intent.

Examples:
- for a plain task without a date:
  - `Добавить задачу`
  - `Сегодня к 19:00`
  - `Завтра в 09:00`
  - `В ближайший понедельник`
- for a reminder without an exact time:
  - `Поставить напоминание`
  - `В 09:00`
  - `В 14:00`
  - `В 19:00`
- for a ticket:
  - `Сохранить событие`
  - time-aware options when needed

### 3. Human-style bot replies

The Telegram reply now avoids internal wording such as:
- confidence percentage
- "incoming saved"
- generic type override buttons

Instead the bot answers in plain Russian, for example:
- "Похоже, это задача…"
- "Похоже, это напоминание…"
- "Похоже, здесь нужен ответ…"

### 4. Better reasoning model support

The project now supports reasoning effort for newer OpenAI models.

New config:
- `OPENAI_REASONING_EFFORT=medium`

Recommendation for this project:
- best quality: `gpt-5.2`
- strong balance of quality / speed: `gpt-5.1`
- current fallback / cheaper option: `gpt-4.1-mini`

If `OPENAI_MODEL` or `OPENAI_VISION_MODEL` starts with `gpt-5`, the app automatically passes reasoning settings to the API.

### 5. Russian navigation in Mini App

Main user-facing tabs are now in Russian:
- `Главная`
- `Входящие`
- `Сегодня`
- `Задачи`
- `Календарь`
- `События`
- `Списки`
- `Заметки`
- `Поиск`

### 6. Full task control in Mini App

Tasks can now be managed directly in the app:
- mark as done
- reopen completed tasks
- change deadline
- clear deadline
- delete task
- filter between all tasks and only incomplete tasks

### 7. Calendar view

The Mini App includes a calendar tab that combines:
- tasks by due date or scheduled date
- events by start date
- reminders by reminder date

## Important files

AI and intake:
- `services/ingestion.py`
- `services/analysis.py`
- `parsers/text.py`
- `ai/openai_provider.py`
- `utils/settings.py`

Resolution and object creation:
- `services/inbox_actions.py`
- `services/object_builder.py`
- `api/routes/inbox.py`
- `api/routes/tasks.py`

Telegram UX:
- `bot/handlers/content.py`
- `bot/handlers/common.py`
- `bot/keyboards.py`
- `bot/callbacks.py`

Mini App:
- `mini_app/src/app.tsx`
- `mini_app/src/components/NavBar.tsx`
- `mini_app/src/pages/InboxPage.tsx`
- `mini_app/src/pages/TasksPage.tsx`
- `mini_app/src/pages/CalendarPage.tsx`

## Local setup

### 1. Prepare environment

- install Python 3.10+
- install Node.js 22+
- copy `.env.example` to `.env`
- fill at least:
  - `BOT_TOKEN`
  - `OPENAI_API_KEY`

Recommended model setup for reasoning:

```env
OPENAI_MODEL=gpt-5.1
OPENAI_VISION_MODEL=gpt-5.1
OPENAI_AUDIO_MODEL=gpt-4o-mini-transcribe
OPENAI_REASONING_EFFORT=medium
```

If you want maximum quality and are okay with higher cost/latency, use:

```env
OPENAI_MODEL=gpt-5.2
OPENAI_VISION_MODEL=gpt-5.2
```

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
$env:PYTHONPATH = "C:\Users\user\Desktop\Телеграм бот\keepiq2"
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
- frontend Mini App: Cloudflare Pages
- backend API + bot + scheduler: Render
- source of truth: GitHub

## Deploy update checklist

### GitHub

```powershell
git status
git add .
git commit -m "Improve adaptive AI triage"
git push origin master
```

### Render

Check:
- `OPENAI_API_KEY`
- `OPENAI_MODEL`
- `OPENAI_VISION_MODEL`
- `OPENAI_AUDIO_MODEL`
- `OPENAI_REASONING_EFFORT`
- `BOT_TOKEN`
- `DATABASE_URL`
- `MINI_APP_PUBLIC_URL`

Start commands:
- API: `python -m uvicorn api.app:app --host 0.0.0.0 --port $PORT`
- bot: `python -m bot.main`
- scheduler: `python -m jobs.runner`

### Cloudflare Pages

Check:
- project root: `mini_app`
- build command: `npm run build`
- output directory: `dist`
- `VITE_API_URL` points to the public Render API URL

## Current limitations

- OCR for arbitrary images is still not a separate dedicated local pipeline.
- PDF/DOCX binary parsing is still limited in the local fallback path.
- The heuristic fallback is much simpler than GPT-5 reasoning and exists mainly as a safe backup.

## Regression coverage

Tests currently cover:
- reminder flow with suggested actions before materialization
- explicit task gets adaptive scheduling suggestions
- question becomes `answer`
- repeated resolve does not duplicate tasks
