# AI Dashboard

A production-ready, self-hosted **AI analytics admin dashboard** built with Flask and the OpenAI Responses API. It combines a modern SaaS-style admin UI (stat cards, charts, activity timeline, notifications, settings) with a full **AI Chat & Prompt Playground**: streaming chat, saved/favorite prompts, structured JSON output, and live usage analytics (tokens, cost, response time).

![Python](https://img.shields.io/badge/Python-3.12%2B-3776AB?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.x-000000?logo=flask&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-informational)

---

## Table of contents

1. [Features](#features)
2. [Architecture](#architecture)
3. [Folder structure](#folder-structure)
4. [Prerequisites](#prerequisites)
5. [Visual Studio Code setup](#visual-studio-code-setup)
6. [Running locally](#running-locally)
7. [Dashboard overview](#dashboard-overview)
8. [Feature explanation](#feature-explanation)
9. [Environment variables](#environment-variables)
10. [API reference](#api-reference)
11. [Troubleshooting](#troubleshooting)
12. [Deployment](#deployment)
13. [Future improvements](#future-improvements)
14. [License](#license)

---

## Features

**Dashboard**
- Modern admin dashboard with sidebar navigation and top navigation bar
- Stat cards (requests today/week/month, tokens used, estimated cost)
- 5 live Chart.js charts (requests, token usage, cost, categories, response time)
- Activity timeline of recent AI requests
- Notification center with unread badge and "mark all read"
- Settings page (profile, appearance, AI defaults)
- Light mode / Dark mode with persisted preference
- Fully responsive layout, collapsible sidebar, mobile-friendly

**AI**
- Floating AI Chat widget available on every page
- Dedicated AI Chat & Prompt Playground page
- Streaming responses (Server-Sent Events) for the chat tab
- Prompt Playground for single-shot prompt experiments
- Prompt history (per session), saved prompts, favorite prompts, prompt templates
- Structured Output viewer with Markdown / JSON / Raw tabs
- Temperature control and model selection
- Editable system prompt
- Estimated token usage and estimated API cost per request

**Analytics**
- Daily / weekly / monthly request counts
- Token usage (prompt vs. completion) over time
- Estimated API cost over time
- Average response time
- Prompt category distribution
- Most-used prompts leaderboard

---

## Architecture

The project follows a **clean, modular, service-oriented architecture** so the codebase stays easy to test, extend, and reason about:

```
┌──────────────────────┐
│   templates/*.html   │  Presentation layer (Jinja2 + vanilla JS + Chart.js)
└──────────┬───────────┘
           │
┌──────────▼───────────┐
│       app.py         │  HTTP layer - Flask routes only (thin controllers)
└──────────┬───────────┘
           │
   ┌───────┼──────────────────┐
   │       │                  │
┌──▼────┐ ┌▼──────────────┐ ┌─▼───────────────┐
│ai_    │ │dashboard_     │ │analytics.py     │  Domain / service layer
│service│ │service.py     │ │                 │  (business logic, no Flask
│.py    │ │(prompts,      │ │(usage tracking, │   imports)
│(OpenAI│ │ notifications,│ │ aggregation,    │
│wrapper│ │ settings)     │ │ cost estimation)│
└──┬────┘ └───────┬───────┘ └────────┬────────┘
   │              │                  │
   │      ┌───────▼──────────────────▼───────┐
   │      │        data/*.json (JSON store)  │
   │      └──────────────────────────────────┘
   │
┌──▼──────────────┐
│  OpenAI         │
│  Responses API  │
└─────────────────┘
```

Design principles applied throughout:

- **Separation of concerns** - `app.py` only parses requests and serializes responses; all business logic lives in `ai_service.py`, `dashboard_service.py`, and `analytics.py`.
- **Single responsibility per module** - `config.py` owns configuration, `analytics.py` owns usage tracking/statistics, `ai_service.py` owns all OpenAI communication, `dashboard_service.py` owns prompts/notifications/settings persistence.
- **Type hints everywhere** - function signatures and dataclasses use Python 3.12 type hints for editor autocompletion and static analysis.
- **PEP 8** - consistent naming, docstrings, and formatting.
- **Structured logging** - every module logs through the standard `logging` module; the Flask app configures a shared formatter.
- **Environment-driven configuration** - no secrets or environment-specific values are hardcoded; everything flows through `config.py` and `.env`.
- **No external database required** - a lightweight, thread-safe JSON file store (`JsonRepository` / `JsonEventStore`) keeps local setup to zero-config while still being swappable for a real database in production.
- **Graceful degradation** - if `OPENAI_API_KEY` is not configured, the dashboard still runs; AI-dependent UI is disabled with a clear on-screen notice instead of crashing.

---

## Folder structure

```
ai-dashboard/
├── README.md # This file
├── LICENSE # MIT license
├── .gitignore
├── requirements.txt # Python dependencies
├── .env.example # Environment variable template
├── app.py # Flask app & routes (controllers)
├── config.py # Centralized configuration + model pricing table
├── dashboard_service.py # Prompts, notifications, settings persistence
├── ai_service.py # OpenAI Responses API wrapper (chat/playground/streaming)
├── analytics.py # Usage tracking & aggregate statistics engine
├── data/ # JSON-backed local storage (auto-created, gitignored)
├── templates/
│   ├── base.html # Shared layout: sidebar, topbar, chat widget
│   ├── dashboard.html # Overview page (stat cards, charts, timeline)
│   ├── settings.html # Profile, appearance, AI defaults
│   └── chat.html # AI Chat & Prompt Playground
└── static/
    ├── css/
    │   ├── style.css # Design tokens, layout, shared components
    │   └── dashboard.css # Page-specific styles (cards, charts, playground)
    ├── js/
    │   ├── dashboard.js # Page logic (dashboard/settings/chat pages)
    │   ├── charts.js # Chart.js configuration & data loaders
    │   ├── chat.js # Floating AI chat widget
    │   └── theme.js # Theme toggle, sidebar, notifications dropdown
    └── images/# Static image assets
```

---

## Prerequisites

- **Python 3.12+** - [Download Python](https://www.python.org/downloads/)
- **Visual Studio Code** - [Download VS Code](https://code.visualstudio.com/)
- **VS Code Python extension** (`ms-python.python`) - install from the Extensions marketplace
- An **OpenAI API key** - [Get one here](https://platform.openai.com/api-keys) (optional for browsing the dashboard UI, required for AI features)

Verify your Python installation:

```bash
python3 --version
# Python 3.12.x (or newer)
```

> **Windows users:** use `python` instead of `python3` in the commands below if that's how Python is aliased on your system (`py --version` also works via the Python launcher).

---

## Visual Studio Code setup

1. **Clone or download the repository**

   ```bash
   git clone https://github.com/your-username/ai-dashboard.git
   cd ai-dashboard
   ```

2. **Open the folder in VS Code**

   ```bash
   code .
   ```

3. **Create a virtual environment**

   ```bash
   python3 -m venv venv
   ```

4. **Activate the virtual environment**

   - macOS / Linux:
     ```bash
     source venv/bin/activate
     ```
   - Windows (PowerShell):
     ```powershell
     venv\Scripts\Activate.ps1
     ```
   - Windows (cmd.exe):
     ```cmd
     venv\Scripts\activate.bat
     ```

   When active, `(venv)` appears at the start of your terminal prompt. In VS Code, open the Command Palette (`Ctrl/Cmd+Shift+P`) -> **Python: Select Interpreter** -> choose the `venv` interpreter so IntelliSense and debugging use the right environment.

5. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

6. **Create your `.env` file**

   ```bash
   cp .env.example .env        # macOS/Linux
   copy .env.example .env      # Windows
   ```

   Open `.env` in VS Code and set your key:

   ```
   OPENAI_API_KEY=sk-...your-real-key...
   ```

   The dashboard runs without a key - AI features are simply disabled with an on-screen notice until one is added.

7. *(Optional)* **Recommended VS Code extensions**
   - Python (`ms-python.python`)
   - Pylance (`ms-python.vscode-pylance`)
   - Even Better TOML / dotenv syntax highlighting for `.env` files

---

## Running locally

With the virtual environment activated:

```bash
python app.py
```

You should see:

```
2026-07-10 09:00:00 [INFO] ai_dashboard: Starting AI Dashboard on http://127.0.0.1:5000
 * Running on http://127.0.0.1:5000
```

Open **http://127.0.0.1:5000** in your browser.

Alternative ways to run it:

```bash
# Using the Flask CLI
flask --app app run --debug

# On a specific host/port
HOST=0.0.0.0 PORT=8080 python app.py
```

### Running / debugging inside VS Code

Create `.vscode/launch.json` (or use the built-in "Python: Flask" template) with:

```jsonc
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: Flask (AI Dashboard)",
      "type": "debugpy",
      "request": "launch",
      "module": "flask",
      "env": { "FLASK_APP": "app.py", "FLASK_DEBUG": "1" },
      "args": ["run", "--no-debugger", "--no-reload"],
      "jinja": true
    }
  ]
}
```

Then press **F5** to run with full breakpoint debugging support, including inside Jinja templates.

---

## Dashboard overview

| Page | Route | Purpose |
|---|---|---|
| **Overview** | `/` | Stat cards, 5 live charts, activity timeline, most-used prompts |
| **AI Chat & Prompt Playground** | `/chat` | Streaming chat, single-shot playground, prompt library, run settings |
| **Settings** | `/settings` | Profile, light/dark appearance, AI defaults (model, temperature, system prompt) |

Every page shares a **sidebar** (navigation + live monthly-spend widget), a **topbar** (search, theme toggle, notifications, profile), and a **floating AI chat widget** (hidden on the dedicated chat page to avoid duplication).

---

## Feature explanation

### Prompt Playground
Single-shot prompt testing separate from multi-turn chat. Supports:
- **Model selection** - choose from any model in the pricing table (`config.py`)
- **Temperature control** - 0.0–2.0 slider, shared with the Chat tab
- **System prompt editor** - persisted per-session, seeded from your Settings default
- **Structured JSON output** - toggle "Request structured JSON output" to force `response_format: json_object`
- **Output viewer** - switch between **Markdown** (rendered via marked.js), **JSON** (pretty-printed), and **Raw** text

### Prompt library
- **Saved prompts** - save the current playground prompt with a title and category
- **Favorite prompts** - star icon toggles favorite status; filter the list to favorites only
- **Prompt templates** - three example templates are seeded on first run (bug triage, changelog writer, SQL explainer)
- **Prompt history** - the last 12 playground runs in the current browser session are listed with token/time stats; click one to reload it

### Streaming responses
The Chat tab streams tokens as they're generated using **Server-Sent Events** over `POST /api/ai/chat/stream`, parsed client-side with the Fetch API's `ReadableStream`. Toggle "Stream responses" off to use the plain `POST /api/ai/chat` endpoint instead.

### AI usage analytics
Every AI request (chat or playground) is recorded by `analytics.py` with:
- Prompt / completion / total token counts
- Estimated cost (via the per-model pricing table in `config.py`)
- Response time in milliseconds
- Success/failure status and a short prompt preview

These events power all dashboard charts and the sidebar's "Month cost" widget.

---

## Environment variables

All variables live in `.env` (see `.env.example` for the full template with comments):

| Variable | Default | Description |
|---|---|---|
| `OPENAI_API_KEY` | *(none)* | Your OpenAI API key. Required for AI features. |
| `OPENAI_DEFAULT_MODEL` | `gpt-4o-mini` | Default model for new chats/playground runs |
| `OPENAI_DEFAULT_TEMPERATURE` | `0.7` | Default sampling temperature |
| `OPENAI_SYSTEM_PROMPT` | *(assistant persona)* | Default system prompt |
| `SECRET_KEY` | `dev-secret-key` | Flask session secret - **change in production** |
| `FLASK_DEBUG` | `True` | Enables debug mode / auto-reload |
| `HOST` | `127.0.0.1` | Dev server bind address |
| `PORT` | `5000` | Dev server port |
| `DATA_DIR` | `data` | Folder for local JSON storage |
| `APP_NAME` | `AI Dashboard` | Display name shown in the UI |
| `CURRENCY_SYMBOL` | `$` | Currency symbol used in cost displays |

---

## API reference

All endpoints return JSON unless noted otherwise.

### Dashboard
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/dashboard/summary` | Today/week/month/all-time KPI totals |
| GET | `/api/dashboard/charts/requests?days=14` | Daily request counts |
| GET | `/api/dashboard/charts/tokens?days=14` | Daily prompt/completion token counts |
| GET | `/api/dashboard/charts/costs?days=14` | Daily estimated cost |
| GET | `/api/dashboard/charts/response-times?days=14` | Daily average response time |
| GET | `/api/dashboard/charts/categories` | All-time prompt category distribution |
| GET | `/api/dashboard/activity?limit=10` | Recent activity feed |
| GET | `/api/dashboard/most-used-prompts?limit=5` | Most frequently used prompt previews |
| GET | `/api/dashboard/notifications` | List notifications |
| POST | `/api/dashboard/notifications/<id>/read` | Mark one notification as read |
| POST | `/api/dashboard/notifications/read-all` | Mark all notifications as read |

### AI
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/ai/chat` | Non-streaming chat completion |
| POST | `/api/ai/chat/stream` | Streaming chat completion (SSE) |
| POST | `/api/ai/playground` | Single-shot prompt run, optional `json_mode` |
| GET | `/api/ai/models` | List available models + configuration status |

### Prompts
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/prompts` | List saved prompts |
| POST | `/api/prompts` | Create a saved prompt (`title`, `content`, `category`, `favorite`) |
| PATCH | `/api/prompts/<id>` | Update a saved prompt |
| POST | `/api/prompts/<id>/favorite` | Toggle favorite status |
| DELETE | `/api/prompts/<id>` | Delete a saved prompt |

### Settings
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/settings` | Get current settings |
| POST | `/api/settings` | Update settings (partial updates supported) |

---

## Troubleshooting

**`ModuleNotFoundError: No module named 'flask'`**
Your virtual environment isn't activated, or dependencies weren't installed. Run `source venv/bin/activate` (or the Windows equivalent) then `pip install -r requirements.txt`.

**AI features show "not configured" / chat returns a 400 error**
`OPENAI_API_KEY` is missing or still set to the placeholder in `.env`. Add a real key and restart the server (`Ctrl+C` then `python app.py`).

**Charts don't render / console shows a Chart.js error**
Ensure you have an internet connection - Chart.js and marked.js are loaded from a CDN (`cdnjs.cloudflare.com`). To self-host them, download the files into `static/js/vendor/` and update the `<script>` tags in `templates/dashboard.html` and `templates/chat.html`.

**Port already in use**
Another process is bound to port 5000 (common on macOS with AirPlay Receiver). Set a different port: `PORT=5050 python app.py`, or disable AirPlay Receiver in System Settings.

**Streaming responses stop mid-way / hang**
Some reverse proxies buffer streamed responses. The app already sends `X-Accel-Buffering: no`; if you're behind Nginx, also add `proxy_buffering off;` for the `/api/ai/chat/stream` location.

**Changes to `.env` aren't picked up**
`.env` is only read at process startup (`config.py` loads it once). Restart the Flask server after editing `.env`.

**Data resets unexpectedly**
Local state (prompts, notifications, settings, analytics events) lives in `data/*.json`. This folder is gitignored by default - back it up or point `DATA_DIR` at a persistent volume in production.

---

## Deployment

This is a standard Flask application and can be deployed anywhere Python runs. A few notes:

1. **Set production environment variables**
   - `FLASK_DEBUG=False`
   - A strong, random `SECRET_KEY`
   - A real `OPENAI_API_KEY`
   - `DATA_DIR` pointed at a persistent, writable volume

2. **Use a production WSGI server** (the Flask dev server is not production-grade):

   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:8000 app:app
   ```

   On Windows, use `waitress` instead of `gunicorn`:

   ```bash
   pip install waitress
   waitress-serve --listen=0.0.0.0:8000 app:app
   ```

3. **Persist `data/`** - mount it as a volume (Docker) or point `DATA_DIR` at a managed disk; otherwise prompts/analytics reset on redeploy. For serious production use, swap `JsonRepository`/`JsonEventStore` in `dashboard_service.py` / `analytics.py` for a real database (PostgreSQL, SQLite, etc.) - the rest of the app is unaffected since all access goes through those two classes.

4. **Put it behind a reverse proxy** (Nginx, Caddy) for TLS termination, and disable response buffering on the `/api/ai/chat/stream` route so streaming works end-to-end.

5. **Suggested platforms**: Render, Railway, Fly.io, AWS Elastic Beanstalk, Azure App Service, or a plain VM with `systemd` + `gunicorn` + Nginx.

Example minimal `Dockerfile`:

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn
COPY . .
ENV FLASK_DEBUG=False
EXPOSE 8000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "app:app"]
```

---

## Future improvements

- Swap JSON file storage for PostgreSQL/SQLite via SQLAlchemy, with Alembic migrations
- Multi-user authentication (Flask-Login) and per-user prompt/analytics scoping
- Role-based access control for team workspaces
- WebSocket-based live dashboard updates instead of polling
- Export analytics (CSV/PDF) and scheduled email usage reports
- Prompt versioning and diffing in the Prompt Playground
- Function calling / tool use support in the Chat tab
- Rate limiting and per-user API budgets
- Automated test suite (pytest) covering services and API routes
- Dockerized local dev environment with `docker-compose` (app + Postgres)
- Internationalization (i18n) for the dashboard UI

---

## License

Released under the [MIT License](LICENSE).
