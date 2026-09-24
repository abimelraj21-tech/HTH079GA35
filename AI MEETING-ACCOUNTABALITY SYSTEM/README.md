# 🛡️ Enterprise AI Meeting Accountability System

An intelligent auditing and tracking system designed for enterprise meetings. It enforces **Zero-Hallucination Line-Indexed Citations**, tracks **Action Items across consecutive meetings**, and verifies task continuity, owner handoffs, and task resolution.

---

## 🌟 Key Features

1. **Zero-Hallucination Line Citations**
   - Transcripts are indexed line-by-line (`[L1]`, `[L2]`, ...).
   - Every extracted action item, decision, or blocker must cite its source line (e.g. `[L2]`, `[L4]-[L5]`).
   - Clicking any citation in the UI immediately highlights and centers the exact utterance in the transcript viewer.

2. **Cross-Meeting Continuity & State Machine**
   - Detects carried-over tasks across meetings using normalized token similarity.
   - Preserves complete audit trails (e.g. `Meeting_01:[L4]-[L5] ➔ Meeting_02:[L3] ➔ Meeting_03:[L2]`).
   - Tracks status transitions: `New` ➔ `Updated / Carried Over` ➔ `Resolved` or `Blocked`.
   - Handles owner handoffs (e.g., from `Unassigned` to `Rahul`) and deadline extensions.

3. **Decisions & Blockers Auditing**
   - Audits formal commitments, completions, and architectural decisions.
   - Automatically tracks open blockers or unassigned questions.

4. **Modern Split-Screen Dashboard**
   - **Left**: Metrics KPIs, Action Items table with inline status editor, Decisions log, Blockers, and Prompt Inspector.
   - **Right**: Verifiable Transcript Citation Inspector with luminous glow pulse on cited lines.
   - **Export**: Generates formal Markdown Audit Reports and CSV Task Sheets.

---

## 🚀 Quick Start

### Option A: Launch Streamlit Dashboard
Run in terminal or double-click `run_streamlit.bat`:
```bash
streamlit run streamlit_app.py
```

### Option B: Launch FastAPI Full Web Dashboard
Double-click `run_dashboard.bat` or run in terminal:

```bash
python app.py
```

Then visit [http://127.0.0.1:8000](http://127.0.0.1:8000) in your web browser.

---

## 📁 Project Structure

```
├── streamlit_app.py    # Streamlit interactive dashboard (HTH-GA-03 Enterprise Engine)
├── run_streamlit.bat   # 1-click Streamlit launcher
├── app.py              # Full dashboard web server and REST API (FastAPI)
├── tracker_engine.py   # MeetingAccountabilityTracker class for programmatic and API tracking
├── tracker_api.py      # Dedicated lightweight REST API microservice (v1 endpoints)
├── engine.py           # Core accountability engine, indexing, and fuzzy task matching
├── extractor.py        # Strict zero-hallucination prompt and rule-based parser
├── sample_data.py      # Preloaded sample meetings (Meeting 01, 02, and 03)
├── main.py             # CLI standalone demo prototype
├── run_dashboard.bat   # 1-click Windows launcher for FastAPI dashboard
├── static/
│   └── index.html      # Responsive split-screen dashboard UI (Tailwind CSS + Lucide)
└── README.md           # Documentation
```

---

## 📡 REST API Endpoints (v1)

Available on both `app.py` (`:8000`) and standalone `tracker_api.py` (`:8001`):

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Operational health check (on `tracker_api.py`) |
| `POST` | `/api/v1/process-meeting` | Ingest meeting JSON with decisions, action items & line citations |
| `POST` | `/api/v1/resolve-task` | Mark a task as resolved by keyword matching |
| `GET` | `/api/v1/tasks` | Retrieve all tracked tasks with audit trails |

---

## 🔍 The Zero-Hallucination Auditor Prompt

```
You are an Enterprise AI Meeting Auditor.
Extract Decisions, Action Items, and Unresolved Issues from the transcript.

RULES TO PREVENT HALLUCINATION:
1. ONLY extract information explicitly stated in the transcript lines.
2. EVERY extracted item MUST include the exact line identifier (e.g., "[L2]").
3. If an owner or deadline is NOT explicitly stated, mark it as "Unassigned" or "None".
4. Do NOT assume or invent dates/names.
```
