# Project Review - AI Dashboard

This report is a read-only audit. No source files were modified while producing it.

Scope reviewed: `app.py`, `config.py`, `ai_service.py`, `analytics.py`, `dashboard_service.py`, templates, static JS/CSS, and repo metadata files (`README.md`, `LICENSE`, `.gitignore`, `.env.example`, `requirements.txt`).

---

## 1. Required-file check

| File | Status |
|---|---|
| `README.md` | ✅ Present - thorough, already covers setup, architecture, API reference, deployment |
| `LICENSE` | ✅ Present - MIT |
| `.gitignore` | ✅ Present - covers Python, venvs, `.env`, data files, VS Code, OS cruft |
| `requirements.txt` | ✅ Present - `Flask`, `python-dotenv`, `openai`, `Werkzeug` |
| `.env.example` | ✅ Present - well-commented, matches `config.py` exactly |
| `pyproject.toml` | ❌ **Missing** |

Since `README.md` already exists and is high quality, no new README was generated (per instructions). All other present files were left untouched.

### Missing: `pyproject.toml`

- **Why it should exist:** `pyproject.toml` is the modern, standardized way to declare a Python project's metadata (name, version, author), dependencies, and tool configuration (e.g. `black`, `ruff`, `mypy`, `pytest`) in one file, as defined by PEP 518/621. Right now the project only has a flat `requirements.txt`, which works for `pip install -r requirements.txt` but has no project metadata and can't be `pip install -e .`'d as a package.
- **Why it's useful here:** it would let contributors install the project as an editable package, pin a Python version requirement (`requires-python = ">=3.12"`), and centralize linter/formatter/test configuration instead of scattering it across `.flake8`, `pytest.ini`, etc. It's also expected by many modern tools (e.g. `uv`, `pip-tools`, `ruff`) and by GitHub's dependency graph / Dependabot in some configurations.
- **Not generated automatically** per your instructions - this section only explains the gap. If you'd like one generated, ask explicitly and specify a project name/version.

---

## 2. Code review

### High severity

**H1 - AI-generated Markdown is rendered as raw HTML without sanitization**
`static/js/dashboard.js` (Prompt Playground "Rendered" tab):
```js
outputRendered.innerHTML = window.marked.parse(text || "");
```
- *Why it matters:* `marked.parse()` converts Markdown to HTML but does not sanitize it. Raw HTML/`<script>`/event-handler attributes embedded in the Markdown source pass straight into `innerHTML`. Because the text being rendered is an LLM completion, and LLM completions can be steered by user-supplied prompts (directly, or indirectly if this app is ever pointed at untrusted input), this is a stored/reflected XSS vector: a crafted prompt could get the model to emit `<img src=x onerror=...>` or a `<script>` tag that then executes in the victim's browser session.
- *Recommended improvement:* Run the parsed HTML through a sanitizer before assigning it to `innerHTML` - e.g. [DOMPurify](https://github.com/cure53/DOMPurify) (`outputRendered.innerHTML = DOMPurify.sanitize(window.marked.parse(text))`), or configure `marked` with a strict allowlist renderer. This is a quick, low-risk fix and should be prioritized before any public/multi-user deployment.

### Medium severity

**M1 - No CSRF protection on state-changing endpoints**
All `POST`/`PATCH`/`DELETE` routes in `app.py` (`/api/prompts`, `/api/settings`, `/api/dashboard/notifications/*`, etc.) accept requests with no CSRF token and no `Origin`/`Referer` check.
- *Why it matters:* for a single-user local tool this is low risk, but the README explicitly documents production deployment (Gunicorn/Waitress behind Nginx). Once this runs as a network-reachable service, any authenticated session is vulnerable to cross-site request forgery (a malicious page can silently submit prompts, change settings, or spam notifications on the victim's behalf).
- *Recommended improvement:* add `Flask-WTF`'s CSRF protection or a simple custom-header check (`X-Requested-With`) enforced server-side, especially before multi-user/auth work lands.

**M2 - Unbounded/unvalidated `**updates` merged into persisted settings and prompts**
`dashboard_service.py`:
```python
def update_prompt(self, prompt_id: str, **updates: Any) -> dict[str, Any] | None:
    ...
    p.update({k: v for k, v in updates.items() if v is not None})
```
```python
def update_settings(self, **updates: Any) -> dict[str, Any]:
    settings = self.get_settings()
    settings.update({k: v for k, v in updates.items() if v is not None})
```
Both are called directly with `**request.get_json(force=True)` from `app.py`, so **any key** in the JSON body is written into the stored record - including keys like `id` or `created_at` on a prompt, which callers aren't expected to be able to overwrite.
- *Why it matters:* this is a mass-assignment pattern. It's low-impact today (no auth, no sensitive fields), but it's a landmine for future changes - the moment a sensitive or structural field (auth flags, ownership, permissions) is added to these dataclasses, this code path will silently allow it to be overwritten by any client.
- *Recommended improvement:* explicitly whitelist which fields each endpoint may update (e.g. `{k: v for k, v in updates.items() if k in {"title", "content", "category", "favorite"}}`).

**M3 - JSON file writes are not atomic**
`JsonRepository._write` and `JsonEventStore._write` (`dashboard_service.py`, `analytics.py`) both do a direct `open(path, "w")` + `json.dump`.
- *Why it matters:* if the process is killed (crash, OOM, `kill -9`, power loss) mid-write, the JSON file is left truncated/corrupted, and the next `read()` call will silently fall back to the default/empty dataset - i.e. **silent data loss** for prompts, settings, and analytics history.
- *Recommended improvement:* write to a temp file in the same directory and `os.replace()` it over the target (atomic on POSIX and Windows), e.g.:
  ```python
  tmp = self.path.with_suffix(".tmp")
  with open(tmp, "w", encoding="utf-8") as fh:
      json.dump(data, fh, indent=2)
  os.replace(tmp, self.path)
  ```

**M4 - No request size / rate limiting on AI endpoints**
`/api/ai/chat`, `/api/ai/chat/stream`, and `/api/ai/playground` place no cap on prompt/history size or request frequency before forwarding to OpenAI.
- *Why it matters:* a single client (malicious or buggy) can send unbounded-length prompts or hammer the endpoint in a loop, running up API costs with no server-side guardrail - notable for a tool whose whole purpose is *cost tracking*.
- *Recommended improvement:* add a reasonable max message/history length check and a lightweight rate limiter (e.g. `Flask-Limiter`) on the `/api/ai/*` routes.

**M5 - `model` parameter is passed through to OpenAI without validation**
In `app.py`, `payload.get("model")` is passed straight to `ai_service.complete()`/`stream()`, which forwards it to the OpenAI SDK. `config.py` defines an `AVAILABLE_MODELS` list, but it's only used to populate the UI dropdown - it's never enforced server-side.
- *Why it matters:* mostly a cost-estimation correctness issue: a client can request any model string, including ones not in `MODEL_PRICING`, which silently falls back to `DEFAULT_PRICING` and understates/overstates real cost in the analytics.
- *Recommended improvement:* validate `model in AVAILABLE_MODELS` in the route handlers and reject (400) otherwise.

### Low severity

**L1 - Debug mode defaults to `True`**
`config.py`: `debug: bool = field(default_factory=lambda: _bool_env("FLASK_DEBUG", True))`, and `.env.example` also ships `FLASK_DEBUG=True`.
- *Why it matters:* Flask's interactive debugger, if ever exposed on a non-loopback address, allows arbitrary remote code execution. The README does correctly instruct setting `FLASK_DEBUG=False` for deployment, so this is a documentation-reliant safety net rather than a bug - but a safer default is `False`, with local dev opting in.
- *Recommended improvement:* flip the default to `False` and have the local quick-start explicitly set `FLASK_DEBUG=True` in the generated `.env`.

**L2 - No automated tests**
There is no `tests/` directory or test runner configured (pytest, unittest). The README's "Future improvements" section already acknowledges this.
- *Why it matters:* the service layer (`analytics.py`, `dashboard_service.py`) is pure Python with no Flask dependency and is easy to unit test, but currently has zero coverage - regressions (e.g. in cost/token aggregation math) would only surface manually.
- *Recommended improvement:* add `pytest` + a `tests/` folder with unit tests for `estimate_cost`, `estimate_tokens`, and the `AnalyticsEngine` aggregation methods first, since they're pure functions with clear expected outputs.

**L3 - Generic 404 handler renders the dashboard template**
```python
@app.errorhandler(404)
def not_found(_error):
    return render_template("dashboard.html", error_message="Page not found.")
```
This calls `render_template("dashboard.html", ...)` without passing `settings`, `summary`, `notifications`, `activity`, etc., which the template expects (see the `/` route for comparison).
- *Why it matters:* if `dashboard.html` references any of those variables directly (rather than through Jinja's `|default`), a request to a nonexistent route can itself raise a `UndefinedError`/500 instead of cleanly showing a 404 page.
- *Recommended improvement:* either build a minimal dedicated `404.html` with no data dependencies, or pass the same context the `/` route passes.

**L4 - Unused `field` import in `analytics.py`**
`from dataclasses import asdict, dataclass, field` - `field` is imported but never used in this file (it *is* used in `config.py` and `dashboard_service.py`, so this is specific to `analytics.py`).
- *Why it matters:* purely cosmetic; harmless but is exactly the kind of thing a linter (`ruff`, `flake8`) would flag.
- *Recommended improvement:* remove the unused import, or add `ruff`/`flake8` to CI so lint drift like this gets caught automatically.

**L5 - `estimate_tokens` is a rough heuristic used for real cost figures**
`analytics.py` explicitly documents this ("very rough token estimate ... should not be relied on for billing-grade precision") and only falls back to it when the OpenAI response has no usable `usage` block. This is a reasonable, well-documented trade-off, not a bug - flagged here only so it's visible in one place alongside the other cost-related notes (M5, L1).

### Things done well (worth calling out, not just issues)

- Clean separation of concerns: `app.py` is a thin controller layer; all business logic lives in `ai_service.py` / `analytics.py` / `dashboard_service.py`, as the README's architecture section claims.
- Consistent type hints and dataclasses throughout the service layer.
- Structured logging is configured once in `app.py` and used consistently via `logging.getLogger(__name__)` in each module.
- Graceful degradation when `OPENAI_API_KEY` is absent - the UI stays usable instead of crashing (`ai_service.is_configured` gating).
- Analytics event history is capped (`events[-5000:]`) so the JSON store can't grow unbounded on disk.
- Escaping is done correctly everywhere else in the JS layer (`escapeHtml()` used consistently for prompt titles/categories) - H1 above is the one place it's missing.

---

## 3. GitHub readiness review

| Check | Status | Notes |
|---|---|---|
| Documentation | ✅ Good | README is comprehensive (features, architecture, API reference, deployment, troubleshooting) |
| `.gitignore` coverage | ✅ Good | Correctly excludes `venv/`, `.env`, `data/*.json`, caches, OS files |
| API key exposure | ✅ Clean | `.env` is git-ignored; `.env.example` only contains placeholder values (`sk-your-openai-api-key-here`) |
| Secrets in tracked files | ✅ Clean | No hardcoded keys found in any `.py`/`.js`/`.html` file scanned |
| License | ✅ Present | MIT |
| Generated/cache files present in the zip | ✅ Clean | No `__pycache__`, `.pyc`, or `venv/` folders were included in the uploaded archive |
| Sensitive/temp files | ✅ Clean | Only a `Screenshot 2026.png` (9.6 KB) beyond source - harmless, but see note below |
| Code quality baseline | ⚠️ Fair | No linter/formatter config (`ruff`/`black`) and no CI workflow (`.github/workflows/`) yet |
| Tests | ❌ Missing | No automated tests (see L2 above) |

**Recommendations before making the repo public:**
1. Fix **H1** (Markdown XSS) first - it's the only finding that could affect real users if the app is ever deployed beyond `localhost`.
2. Consider whether `Screenshot 2026.png` should live in the repo root or move to a `docs/` or `.github/` folder - cosmetic, but root-level loose assets are a common nit in OSS reviews.
3. Add a `.github/workflows/ci.yml` that runs `pip install -r requirements.txt` and (once added) `pytest`/`ruff` on push/PR - signals an actively maintained project to visitors.
4. Consider adding a `CONTRIBUTING.md` and a GitHub issue template if you expect external contributors; not required, but a common expectation for public repos with an MIT license.

---

## 4. Repository size audit

| Metric | Value | Within recommended limit? |
|---|---|---|
| Total repo size (excluding any venv/cache - none present) | **248 KB** | ✅ Well under 20 MB |
| Total file count | **26 files** (across `ai-dashboard/` and subfolders) | ✅ Well under 100 files |
| Largest files | `README.md` (20 KB), `static/js/dashboard.js` (20 KB), `static/css/style.css` (20 KB) | ✅ No outliers |

The repository is comfortably within both recommended thresholds - no action needed. If the project grows, the main things to watch for are: committing a `venv/` or `__pycache__/` by accident (already correctly git-ignored), committing real exported `data/*.json` analytics dumps (also git-ignored), or adding large binary assets (screenshots/videos) directly instead of linking them externally or using Git LFS.

---

## Summary

The project is well-structured, documented, and close to GitHub-ready as-is. The one issue worth fixing before any public/networked deployment is **H1** (sanitize AI-generated Markdown before injecting it as HTML). The medium-severity items (CSRF, mass-assignment on settings/prompts, non-atomic JSON writes, missing rate limiting, unvalidated model parameter) matter most once this moves beyond a single trusted local user. Everything else is polish (tests, linting, `pyproject.toml`, minor cleanup) rather than a blocker.
