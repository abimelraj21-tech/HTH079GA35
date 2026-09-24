import re
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

from engine import MeetingAccountabilityEngine, calculate_similarity

class MeetingAccountabilityTracker(MeetingAccountabilityEngine):
    """
    Enterprise Meeting Accountability Tracker.
    Wraps and extends MeetingAccountabilityEngine to provide an API-friendly interface
    for processing meetings, tracking action items across meetings, maintaining zero-hallucination
    line citations, and managing task resolutions.
    """
    def __init__(self, preload_samples: bool = False):
        super().__init__()
        if preload_samples:
            self.load_sample_data()

    def process_meeting(self, meeting_id: str, extracted_json: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Processes an extracted meeting JSON payload (action items, decisions, unresolved issues).
        Updates existing carried-over tasks or creates new ones, maintaining line citations and audit trails.
        Returns the updated list of all tracked tasks.
        """
        # Auto-register meeting if not already present
        if meeting_id not in self.meetings:
            raw_transcript = extracted_json.get("raw_transcript", "")
            title = extracted_json.get("meeting_title", meeting_id)
            date_str = extracted_json.get("date", datetime.now().strftime("%Y-%m-%d"))
            self.register_meeting(
                meeting_id=meeting_id,
                title=title,
                raw_transcript=raw_transcript,
                date_str=date_str
            )

        # Process decisions, unresolved issues, and action items
        self.process_extraction(meeting_id, extracted_json)
        return self.get_all_tasks()

    def mark_resolved(self, task_keyword: str) -> bool:
        """
        Marks any task matching task_keyword (case-insensitive substring or fuzzy match) as Resolved.
        Appends an audit record to the task's history.
        Returns True if at least one matching task was found and resolved, False otherwise.
        """
        if not task_keyword:
            return False

        keyword = task_keyword.lower().strip()
        matched = False

        # 1. Direct or substring matching
        for task in self.tasks:
            task_title = task.get("task", "").lower()
            task_id = task.get("id", "").lower()
            if keyword in task_title or keyword == task_id:
                task["status"] = "Resolved"
                task["audit_trail"].append({
                    "meeting_id": "API_RESOLVE",
                    "meeting_name": "API Resolution Request",
                    "source_line": "N/A",
                    "source_text": f"Resolved via keyword match '{task_keyword}'",
                    "action": "Resolved",
                    "details": f"Task resolved via API keyword match: '{task_keyword}'",
                    "timestamp": datetime.now().isoformat()
                })
                matched = True

        # 2. Fuzzy similarity matching if no direct substring match
        if not matched:
            for task in self.tasks:
                if calculate_similarity(task.get("task", ""), task_keyword) >= 0.45:
                    task["status"] = "Resolved"
                    task["audit_trail"].append({
                        "meeting_id": "API_RESOLVE",
                        "meeting_name": "API Resolution Request",
                        "source_line": "N/A",
                        "source_text": f"Resolved via fuzzy match '{task_keyword}'",
                        "action": "Resolved",
                        "details": f"Task resolved via fuzzy match: '{task_keyword}'",
                        "timestamp": datetime.now().isoformat()
                    })
                    matched = True

        return matched

    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """
        Returns all tracked action items with their owners, deadlines, statuses, and audit trails.
        """
        return list(self.tasks)

    def load_sample_data(self):
        """
        Loads pre-configured multi-meeting sample data.
        """
        try:
            from sample_data import SAMPLE_MEETINGS
            for sample in SAMPLE_MEETINGS:
                self.register_meeting(
                    meeting_id=sample["id"],
                    title=sample["title"],
                    raw_transcript=sample["raw_transcript"],
                    date_str=sample.get("date")
                )
                self.process_extraction(sample["id"], sample["extraction"])
        except ImportError:
            pass

if __name__ == "__main__":
    tracker = MeetingAccountabilityTracker()
    test_extraction = {
        "decisions": [],
        "action_items": [
            {
                "task": "Update database schema",
                "owner": "Priya",
                "deadline": "October 5th",
                "source_line": "[L2]",
                "status": "New"
            }
        ],
        "unresolved_issues": []
    }
    tasks = tracker.process_meeting("Meeting_01", test_extraction)
    print(f"Processed Meeting_01. Total tasks: {len(tasks)}")
    resolved = tracker.mark_resolved("database schema")
    print(f"Marked 'database schema' resolved: {resolved}")
    print(f"Current tasks: {tracker.get_all_tasks()}")
