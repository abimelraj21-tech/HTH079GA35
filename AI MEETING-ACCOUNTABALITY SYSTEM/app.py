import os
import io
import csv
from datetime import datetime
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, HTTPException, Body
from fastapi.responses import HTMLResponse, FileResponse, PlainTextResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from tracker_engine import MeetingAccountabilityTracker
from engine import MeetingAccountabilityEngine, TranscriptIndexer
from sample_data import SAMPLE_MEETINGS
from extractor import RuleBasedAuditor, EXTRACTION_PROMPT

app = FastAPI(
    title="AI Meeting Accountability Dashboard",
    description="Enterprise AI Meeting Auditor & Cross-Meeting Action Item Tracker with Zero Hallucination Line Citations",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global engine / tracker instance
engine = MeetingAccountabilityTracker()

def load_sample_dataset():
    engine.meetings.clear()
    engine.tasks.clear()
    engine.decisions.clear()
    engine.unresolved_issues.clear()
    for sample in SAMPLE_MEETINGS:
        engine.register_meeting(
            meeting_id=sample["id"],
            title=sample["title"],
            raw_transcript=sample["raw_transcript"],
            date_str=sample.get("date")
        )
        engine.process_extraction(sample["id"], sample["extraction"])

# Initialize with sample meetings
load_sample_dataset()

class NewMeetingRequest(BaseModel):
    id: Optional[str] = None
    title: str
    date: Optional[str] = None
    raw_transcript: str
    auto_extract: bool = True
    custom_extraction: Optional[Dict[str, Any]] = None

class TaskUpdateRequest(BaseModel):
    status: Optional[str] = None
    owner: Optional[str] = None
    deadline: Optional[str] = None
    note: Optional[str] = None

class ExtractionProcessRequest(BaseModel):
    custom_extraction: Optional[Dict[str, Any]] = None

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_file = os.path.join(os.path.dirname(__file__), "static", "index.html")
    if os.path.exists(index_file):
        with open(index_file, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse("<h1>Dashboard HTML loading...</h1>")

@app.get("/api/dashboard")
async def get_dashboard():
    return engine.get_dashboard_summary()

@app.get("/api/meetings")
async def get_meetings():
    return list(engine.meetings.values())

@app.get("/api/meetings/{meeting_id}")
async def get_meeting(meeting_id: str):
    if meeting_id not in engine.meetings:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return engine.meetings[meeting_id]

@app.post("/api/meetings")
async def create_meeting(req: NewMeetingRequest):
    meeting_id = req.id.strip() if req.id else f"Meeting_{len(engine.meetings) + 1:02d}"
    
    # Register and index transcript
    engine.register_meeting(
        meeting_id=meeting_id,
        title=req.title,
        raw_transcript=req.raw_transcript,
        date_str=req.date or datetime.now().strftime("%Y-%m-%d")
    )

    extraction = None
    if req.custom_extraction:
        extraction = req.custom_extraction
    elif req.auto_extract:
        indexed_text = engine.meetings[meeting_id]["indexed_transcript"]
        extraction = RuleBasedAuditor.extract_from_indexed_transcript(indexed_text)

    if extraction:
        engine.process_extraction(meeting_id, extraction)

    return {
        "status": "success",
        "meeting_id": meeting_id,
        "meeting": engine.meetings[meeting_id],
        "extracted": extraction
    }

@app.post("/api/meetings/{meeting_id}/process")
async def process_meeting(meeting_id: str, req: ExtractionProcessRequest):
    if meeting_id not in engine.meetings:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    extraction = req.custom_extraction
    if not extraction:
        indexed_text = engine.meetings[meeting_id]["indexed_transcript"]
        extraction = RuleBasedAuditor.extract_from_indexed_transcript(indexed_text)

    engine.process_extraction(meeting_id, extraction)
    return {"status": "processed", "extraction": extraction}

@app.patch("/api/tasks/{task_id}")
async def update_task(task_id: str, req: TaskUpdateRequest):
    task = engine.update_task_manual(
        task_id=task_id,
        status=req.status,
        owner=req.owner,
        deadline=req.deadline,
        note=req.note
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"status": "success", "task": task}

# --- v1 REST API Endpoints ---
class MeetingProcessV1Request(BaseModel):
    meeting_id: str
    extracted_json: Dict[str, Any]

class ResolutionV1Request(BaseModel):
    task_keyword: str

@app.post("/api/v1/process-meeting")
def process_meeting_v1(req: MeetingProcessV1Request):
    updated_tasks = engine.process_meeting(req.meeting_id, req.extracted_json)
    return {"status": "success", "tasks": updated_tasks}

@app.post("/api/v1/resolve-task")
def resolve_task_v1(req: ResolutionV1Request):
    success = engine.mark_resolved(req.task_keyword)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"status": "success", "message": f"Task containing '{req.task_keyword}' resolved."}

@app.get("/api/v1/tasks")
def get_tasks_v1():
    return {"tasks": engine.get_all_tasks()}

@app.post("/api/reset")
async def reset_dataset():
    load_sample_dataset()
    return {"status": "reset_to_default", "summary": engine.get_dashboard_summary()["metrics"]}

@app.get("/api/prompt")
async def get_extraction_prompt():
    return {"prompt": EXTRACTION_PROMPT}

@app.get("/api/export/markdown", response_class=PlainTextResponse)
async def export_markdown():
    summary = engine.get_dashboard_summary()
    md = []
    md.append("# 📋 AI Meeting Accountability & Audit Report")
    md.append(f"*Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")
    
    md.append("## Executive Metrics")
    m = summary["metrics"]
    md.append(f"- **Total Meetings Tracked:** {m['total_meetings']}")
    md.append(f"- **Total Action Items:** {m['total_tasks']}")
    md.append(f"- **Resolved Items:** {m['resolved_tasks']}")
    md.append(f"- **Active Items:** {m['active_tasks']}")
    md.append(f"- **Carried Over / Updated:** {m['carried_over_tasks']}")
    md.append(f"- **Unassigned Items:** {m['unassigned_tasks']}")
    md.append(f"- **Open Unresolved Issues:** {m['total_unresolved']}\n")

    md.append("## Action Items & Audit Trails")
    md.append("| Task ID | Task Description | Owner | Deadline | Status | Verifiable Audit Trail |")
    md.append("|---|---|---|---|---|---|")
    for t in summary["tasks"]:
        trail = " ➔ ".join([f"{a['meeting_id']}:{a['source_line']}" for a in t["audit_trail"]])
        md.append(f"| {t['id']} | {t['task']} | {t['owner']} | {t['deadline']} | {t['status']} | {trail} |")
    md.append("")

    md.append("## Logged Decisions")
    for d in summary["decisions"]:
        md.append(f"- **[{d['meeting_name']} | {d['source_line']}]** {d['text']}")
    md.append("")

    md.append("## Unresolved Issues / Open Blockers")
    for u in summary["unresolved_issues"]:
        md.append(f"- **[{u['meeting_name']} | {u['source_line']}]** {u['text']} (Status: {u['status']})")

    return PlainTextResponse("\n".join(md), media_type="text/markdown")

@app.get("/api/export/csv")
async def export_csv():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Task ID", "Task", "Owner", "Deadline", "Status", "Initial Meeting", "Audit Trail Citations"])
    for t in engine.tasks:
        citations = " -> ".join([f"{a['meeting_id']}:{a['source_line']}" for a in t["audit_trail"]])
        writer.writerow([t["id"], t["task"], t["owner"], t["deadline"], t["status"], t["initial_meeting_id"], citations])
    
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=meeting_accountability_tasks.csv"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
