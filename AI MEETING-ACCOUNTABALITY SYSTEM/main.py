import json
import re
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Optional

# --- STEP 1: Synthetic Transcripts with Line Numbers ---
SYNTHETIC_TRANSCRIPTS = {
    "Meeting_01": """[L1] Alex: Welcome team. Let's discuss the API migration.
[L2] Priya: I can take ownership of updating the database schema by October 5th.
[L3] Alex: Great. Rahul, can you handle the frontend integration?
[L4] Rahul: I'm not sure if I have bandwidth, but I can look into it by next week.
[L5] Alex: Okay, let's keep frontend task as unassigned for now until Rahul confirms.
[L6] Priya: What about the security audit?
[L7] Alex: We didn't decide on the security vendor yet. Unresolved.""",

    "Meeting_02": """[L1] Alex: Follow up on last week's API migration tasks.
[L2] Priya: Database schema update is completed ahead of time.
[L3] Rahul: I checked my bandwidth, I will finish the frontend integration by October 12th.
[L4] Alex: Perfect. Who is taking the security audit?
[L5] Alex: I will personally take the security audit proposal by October 10th."""
}

# --- STEP 2: Strict System Prompt for Zero Hallucination ---
EXTRACTION_PROMPT = """
You are an Enterprise AI Meeting Auditor.
Extract Decisions, Action Items, and Unresolved Issues from the transcript.

RULES TO PREVENT HALLUCINATION:
1. ONLY extract information explicitly stated in the transcript lines.
2. EVERY extracted item MUST include the exact line identifier (e.g., "[L2]").
3. If an owner or deadline is NOT explicitly stated, mark it as "Unassigned" or "None".
4. Do NOT assume or invent dates/names.

OUTPUT FORMAT (JSON):
{
  "decisions": [{"text": "...", "source_line": "..."}],
  "action_items": [
    {
      "task": "...",
      "owner": "...",
      "deadline": "...",
      "source_line": "...",
      "status": "New"
    }
  ],
  "unresolved_issues": [{"text": "...", "source_line": "..."}]
}
"""

# --- STEP 3: Simple Parsing & Tracking Engine ---
class ActionItemTracker:
    def __init__(self):
        self.master_db = []

    def process_meeting(self, meeting_id: str, extracted_json: dict):
        for item in extracted_json.get("action_items", []):
            item["meeting_id"] = meeting_id
            
            # Check if this is a resolution or update to a carried-over task
            existing = next((x for x in self.master_db if x["task"].lower() in item["task"].lower()), None)
            
            if existing:
                existing["status"] = "Updated / Carried Over"
                existing["owner"] = item["owner"] if item["owner"] != "Unassigned" else existing["owner"]
                existing["deadline"] = item["deadline"] if item["deadline"] != "None" else existing["deadline"]
                existing["audit_trail"].append(f"{meeting_id}:{item['source_line']}")
            else:
                item["audit_trail"] = [f"{meeting_id}:{item['source_line']}"]
                self.master_db.append(item)

    def mark_completed(self, task_keyword: str):
        for item in self.master_db:
            if task_keyword.lower() in item["task"].lower():
                item["status"] = "Resolved"

# --- STEP 4: Demo Execution ---
if __name__ == "__main__":
    tracker = ActionItemTracker()

    # Simulated Output from LLM for Meeting 1 based on Prompt
    m1_extracted = {
        "decisions": [],
        "action_items": [
            {"task": "Update database schema", "owner": "Priya", "deadline": "October 5th", "source_line": "[L2]", "status": "New"},
            {"task": "Frontend integration", "owner": "Unassigned", "deadline": "None", "source_line": "[L4]-[L5]", "status": "New"}
        ],
        "unresolved_issues": [{"text": "Security audit vendor selection", "source_line": "[L7]"}]
    }
    
    # Simulated Output from LLM for Meeting 2
    m2_extracted = {
        "decisions": [{"text": "Priya completed schema update", "source_line": "[L2]"}],
        "action_items": [
            {"task": "Frontend integration", "owner": "Rahul", "deadline": "October 12th", "source_line": "[L3]", "status": "Carried-Over"},
            {"task": "Security audit proposal", "owner": "Alex", "deadline": "October 10th", "source_line": "[L5]", "status": "New"}
        ],
        "unresolved_issues": []
    }

    # Process M1
    tracker.process_meeting("Meeting_01", m1_extracted)
    
    # Process M2 & Resolve Schema Task
    tracker.process_meeting("Meeting_02", m2_extracted)
    tracker.mark_completed("database schema")

    # Output State Table
    print("\n=== AI ACCOUNTABILITY DASHBOARD ===")
    print(f"{'TASK':<30} | {'OWNER':<12} | {'DEADLINE':<15} | {'STATUS':<15} | {'AUDIT TRAIL'}")
    print("-" * 90)
    for item in tracker.master_db:
        audit = " -> ".join(item["audit_trail"])
        print(f"{item['task']:<30} | {item['owner']:<12} | {item['deadline']:<15} | {item['status']:<15} | {audit}")
