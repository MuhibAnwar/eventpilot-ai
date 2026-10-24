# EventPilot AI

Event registration dashboard for **synthetic demo data only**. Built with Python, FastAPI, SQLite, and a plain HTML/JS frontend (no build step).

## Features

- Upload `.xlsx` participant lists (`name`, `email`) with validation preview before save
- Flag invalid or missing emails, missing names, and duplicate emails (highlighted in red with reasons)
- Searchable dashboard with `pending` / `confirmed` status
- Per-row **Confirm Registration** — sends confirmation email with **QR event pass PDF** attached
- **Send pass** and **Send certificate** (PDF) for confirmed participants via SMTP
- Idempotent confirm (double-click does not confirm or log twice)
- **Action log** visible on the page
- Natural-language queries routed by **Gemma 4** (`gemma-4-26b-a4b-it`) to a fixed allowlist of server tools
- **Load sample data** (~11 synthetic rows) and downloadable sample spreadsheet
- Optional HTTP Basic auth when `APP_PASSWORD` is set

## Setup (Windows)

```powershell
cd D:\mlh
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Edit `.env`:

- `GEMINI_API_KEY` — from [Google AI Studio](https://aistudio.google.com/apikey) (server-side only)
- `APP_PASSWORD` — optional; if set, all routes require HTTP Basic auth (any username, this password)
- **SMTP (optional)** — connect your mailbox to send real confirmation emails:

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=you@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=you@gmail.com
SMTP_USE_TLS=true
```

For Gmail, use an [App Password](https://support.google.com/accounts/answer/185833) (2FA required). The header shows **Email: connected** when SMTP is configured.

Generate a synthetic workbook:

```powershell
python scripts\generate_sample_xlsx.py
```

## Run

```powershell
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/

## Tests

```powershell
pytest
```

Gemma API calls are mocked in tests; no live API key is required for CI/local pytest.

## How Gemma is used

Gemma runs only in `app/agent.py` as a **tool router**. It must return JSON such as `{"tool":"invalid_emails"}`. The server:

1. Calls model `gemma-4-26b-a4b-it` via the `google-genai` SDK
2. Extracts JSON safely (including fenced or noisy replies)
3. Validates the tool name against: `show_all`, `invalid_emails`, `find_duplicates`, `count_participants`, `none`
4. Executes normal Python code for that tool — no arbitrary code from the model

If the API fails, the UI receives `{"error":"AI unavailable"}` without crashing the app.

## Passes & certificates

1. **Confirm** — email **1/3**: registration confirmed (text only).
2. **Send pass** — email **2/3**: `event-pass.pdf` with QR (confirmed only).
3. **Send certificate** — email **3/3**: `certificate.pdf` (confirmed only).

Set event details in `.env`: `EVENT_NAME`, `EVENT_DATE`, `EVENT_VENUE`.

## Safety

- **AI proposes, humans approve** — Gemma only picks a predefined tool; it does not mutate data directly
- **Human confirms before send** — preview in the modal; one real email per idempotent confirm when SMTP is configured
- **Allowlist** — unknown tools become `none` with a friendly message
- **Secrets** — `GEMINI_API_KEY` stays on the server (python-dotenv); never sent to the browser or logged
- **Untrusted input** — spreadsheet cells and chat text are treated as data; HTML output is escaped in the UI
- **Upload limits** — `.xlsx` only, max 2 MB

## Limitations / Planned

Not implemented yet:

- QR **check-in scanner** / attendance marking at the door
- Google Sheets sync

## Deploy on DigitalOcean App Platform

- **Run command:** `uvicorn app.main:app --host 0.0.0.0 --port 8080`
- Set **encrypted environment variables:** `GEMINI_API_KEY`, and optionally `APP_PASSWORD`
- SQLite lives on the container filesystem — data is **ephemeral** unless you attach persistent storage or switch to a managed database

## Documentation

Product notes can live under [`docs/`](docs/).

## License

MIT — see [LICENSE](LICENSE).
