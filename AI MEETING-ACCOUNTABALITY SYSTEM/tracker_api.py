from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from tracker_engine import MeetingAccountabilityTracker

app = FastAPI(title="AI Meeting Accountability API", version="1.0.0")
tracker = MeetingAccountabilityTracker()

class MeetingProcessRequest(BaseModel):
    meeting_id: str
    extracted_json: Dict[str, Any]

class ResolutionRequest(BaseModel):
    task_keyword: str

@app.get("/")
def home():
    return {"status": "Active", "message": "AI Meeting Accountability Engine Operational"}

@app.post("/api/v1/process-meeting")
def process_meeting(req: MeetingProcessRequest):
    updated_tasks = tracker.process_meeting(req.meeting_id, req.extracted_json)
    return {"status": "success", "tasks": updated_tasks}

@app.post("/api/v1/resolve-task")
def resolve_task(req: ResolutionRequest):
    success = tracker.mark_resolved(req.task_keyword)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"status": "success", "message": f"Task containing '{req.task_keyword}' resolved."}

@app.get("/api/v1/tasks")
def get_tasks():
    return {"tasks": tracker.get_all_tasks()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("tracker_api:app", host="127.0.0.1", port=8001, reload=True)
