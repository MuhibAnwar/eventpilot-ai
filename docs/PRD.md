# Product Requirements Document (PRD)

## EventPilot AI

| Field | Value |
|--------|--------|
| **Product** | EventPilot AI |
| **Version** | 1.0 (hackathon / demo) |
| **Stack** | Python, FastAPI, SQLite, HTML/JS (no frontend build) |
| **Last updated** | October 2026 |

---

## 1. Vision & summary

EventPilot AI is an **event registration control plane** for organizers: import participants from Excel, validate data, confirm registrations, send **three branded transactional emails** (confirm → pass → certificate), track **QR check-in**, and ask **natural-language questions** safely via **Gemma 4** as a tool router—not as an unconstrained agent.

Organizers get one dashboard (UX inspired by modern registration tools) with metrics, audit logs, bulk actions, and CSV export for judges and post-event reporting.

---

## 2. Problem statement

Manual event registration suffers from:

- Dirty spreadsheets (invalid emails, duplicates, missing names)
- No single view of **pending vs confirmed** registrants
- Fragmented communication (confirmations, passes, certificates sent ad hoc)
- No verifiable **check-in** at the door
- Risky “chat with AI” products that expose APIs or run arbitrary model output

EventPilot AI centralizes registration, communication, and check-in with **human-in-the-loop** confirmations and **allowlisted** AI actions.

---

## 3. Target users

| Persona | Needs |
|---------|--------|
| **Event organizer** | Import list, fix bad rows, confirm people, send passes/certs, see logs |
| **Volunteer (check-in)** | Scan QR on pass PDF, see instant valid/invalid |
| **Participant** | Receive clear emails and a scannable pass |
| **Judge / reviewer** | Understand AI safety, see audit trail, export data |

---

## 4. Goals

1. **Reliable registration pipeline** — upload → validate → save → confirm.
2. **Three-email workflow** — separate messages for confirmation, pass (PDF+QR), certificate (PDF).
3. **Safe AI** — Gemma 4 returns only a JSON tool name; server runs fixed Python.
4. **Trust & audit** — action log, idempotent confirm/send, no secret leakage to browser.
5. **Demo-ready UX** — dashboard metrics, judge summary, check-in page, website-matched HTML emails.

---

## 5. Non-goals (out of scope v1)

- Multi-tenant SaaS / billing
- Google Sheets sync
- Mobile native apps
- Real-time collaborative editing of spreadsheets
- Custom WYSIWYG email editor in UI
- Blockchain / NFT tickets
- Automatic certificate send on schedule (manual button only)

---

## 6. Functional requirements

### 6.1 Participant import

- **FR-1** Upload `.xlsx` (max **2 MB**), columns: `name`, `email`; optional `id` (sheet ID).
- **FR-2** Preview before save; flag invalid email, missing name/email, duplicate emails/sheet IDs.
- **FR-3** Save valid rows only, or save all (DB may skip duplicate emails).
- **FR-4** Dashboard sorts by numeric sheet ID when present.

### 6.2 Dashboard

- **FR-5** List participants with search (id, name, email) and filter (pending / confirmed).
- **FR-6** Show pass sent, certificate sent, check-in status, relative join time.
- **FR-7** KPI cards: total, confirmed, pending, email activity %, checked-in count.

### 6.3 Registration confirmation

- **FR-8** **Confirm** opens email preview modal; on approve, mark **confirmed** and send **email 1/3** (HTML + plain text).
- **FR-9** Idempotency: same `idempotency_key` must not double-confirm or double-log.

### 6.4 Pass & certificate

- **FR-10** **Send pass** (confirmed only): email **2/3** with `event-pass.pdf` (QR encodes JSON token).
- **FR-11** **Send certificate** (confirmed only): email **3/3** with `certificate.pdf`.
- **FR-12** **Bulk send passes** for confirmed rows without `pass_sent_at`.
- **FR-13** PDF content uses `EVENT_NAME`, `EVENT_DATE`, `EVENT_VENUE` from environment.

### 6.5 Check-in

- **FR-14** `/check-in` page: camera QR scan or manual JSON paste.
- **FR-15** Server validates `participant_id` + `pass_token`, status confirmed; sets `checked_in_at` (idempotent).

### 6.6 AI assistant (Gemma 4)

- **FR-16** Model **`gemma-4-26b-a4b-it`** only (no `gemini-*` models for routing).
- **FR-17** Router output: JSON `{"tool":"<name>"}`; allowlist: `show_all`, `invalid_emails`, `find_duplicates`, `count_participants`, `none`.
- **FR-18** User text treated as **data**, not instructions; unknown tools → `none`.
- **FR-19** API failures return `{"error":"AI unavailable"}` without crashing UI.

### 6.7 Operations & demo

- **FR-20** System activity log (newest first), terminal-style on dashboard.
- **FR-21** **Judge summary** API: narrative + highlights + metrics for pitches.
- **FR-22** Export participants **CSV**.
- **FR-23** Optional **HTTP Basic auth** when `APP_PASSWORD` is set (all routes).

### 6.8 Email

- **FR-24** SMTP configurable via `.env`; HTML theme aligned with dashboard (sidebar dark bar, EP mark, Inter, indigo/green accents).
- **FR-25** Multipart: `text/plain` + `text/html`; PDF attachments on pass/certificate emails.
- **FR-26** `GEMINI_API_KEY` and SMTP secrets **never** exposed to frontend or logs.

---

## 7. User flows

### 7.1 Happy path (organizer)

1. Import `.xlsx` → preview → save valid rows.
2. Confirm participant → email 1 sent.
3. Send pass → email 2 with PDF.
4. Event day: volunteer scans QR on `/check-in`.
5. Send certificate → email 3 with PDF.
6. Export CSV for records.

### 7.2 AI query

1. Organizer types: “How many participants?” or “Show invalid emails”.
2. Gemma returns tool name → server executes → JSON result in UI.

---

## 8. Technical architecture

```
Browser (HTML/JS)
    ↓ REST
FastAPI (app/main.py)
    ├── SQLite (participants, logs, idempotency)
    ├── app/agent.py (Gemma router)
    ├── app/services.py (business logic)
    ├── app/email_service.py + email_templates.py (SMTP)
    ├── app/documents.py (PDF pass + certificate)
    └── app/hackathon.py (export, judge summary)
```

**Run:** `uvicorn app.main:app --reload`  
**Deploy (example):** `uvicorn app.main:app --host 0.0.0.0 --port 8080` (SQLite ephemeral on PaaS unless volume attached).

---

## 9. Data model (participants)

| Field | Description |
|--------|-------------|
| `id` | Internal primary key |
| `sheet_id` | Optional ID from Excel |
| `name`, `email` | Registrant |
| `status` | `pending` \| `confirmed` |
| `pass_token` | Secret for QR validation |
| `pass_sent_at`, `certificate_sent_at` | Email tracking |
| `checked_in_at` | QR check-in timestamp |
| `confirmed_at`, `created_at` | Timestamps |

Supporting tables: `action_logs`, `confirm_idempotency`, `pass_idempotency`, `certificate_idempotency`.

---

## 10. Security & safety

- Spreadsheet cells and chat input = **untrusted data**; HTML escaped in UI.
- AI **cannot** invoke arbitrary code; allowlist enforced server-side.
- Upload: `.xlsx` only, size cap.
- Secrets in `.env` only (see `.env.example`).
- Optional Basic auth for public demos.

---

## 11. Environment variables

| Variable | Purpose |
|----------|---------|
| `GEMINI_API_KEY` | Gemma API (server only) |
| `SMTP_*`, `SMTP_FROM_NAME` | Outbound email |
| `EVENT_NAME`, `EVENT_DATE`, `EVENT_VENUE` | PDFs & emails |
| `ORGANIZER_NAME` | Dashboard display |
| `APP_PASSWORD` | Optional Basic auth |

---

## 12. Success metrics (hackathon / pilot)

- Time to import 100 rows and confirm first participant **< 5 minutes**
- **0** duplicate confirm log entries under double-click (idempotency tests pass)
- Check-in validates wrong token **100%** rejection
- Judge can complete demo script in **≤ 3 minutes** using dashboard + `/check-in`
- All **`pytest`** tests green (validation, AI allowlist, check-in, email templates)

---

## 13. Roadmap (post-v1)

| Priority | Feature |
|----------|---------|
| P1 | Scheduled / automatic certificate after check-in |
| P2 | Google Sheets import sync |
| P3 | Multi-event support |
| P4 | Resend API or dedicated ESP webhooks (delivery analytics) |
| P5 | Organizer roles & SSO |
| P6 | Wallet pass (Apple/Google) |

---

## 14. Open questions

1. Should certificates send only if `checked_in_at` is set?
2. Per-event SMTP vs global organizer mailbox?
3. Persist SQLite to managed Postgres for production?

---

## 15. References

- Application README: [`../README.md`](../README.md)
- Runbook & safety: README sections *Passes & certificates*, *Safety*, *Limitations*
- Tests: `tests/` (validation, agent, check-in, email)

---

*This PRD describes the implemented demo unless marked as roadmap or open question.*
