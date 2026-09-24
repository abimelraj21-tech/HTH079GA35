import re
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

def normalize_tokens(text: str) -> set:
    stop_words = {"the", "a", "an", "of", "to", "in", "on", "for", "by", "with", "at", "is", "are", "and", "or", "task", "update"}
    words = re.findall(r'\b[a-zA-Z0-9_-]+\b', text.lower())
    return {w for w in words if w not in stop_words and len(w) > 2}

def calculate_similarity(text1: str, text2: str) -> float:
    t1 = text1.lower().strip()
    t2 = text2.lower().strip()
    if t1 == t2:
        return 1.0
    if t1 in t2 or t2 in t1:
        return 0.85
    tokens1 = normalize_tokens(t1)
    tokens2 = normalize_tokens(t2)
    if not tokens1 or not tokens2:
        return 0.0
    intersection = tokens1.intersection(tokens2)
    union = tokens1.union(tokens2)
    return len(intersection) / len(union)

class TranscriptIndexer:
    @staticmethod
    def index(raw_text: str) -> str:
        lines = [line.strip() for line in raw_text.strip().split("\n") if line.strip()]
        # Check if already indexed with [L...]
        if all(re.match(r'^\[L\d+\]', line) for line in lines[:min(3, len(lines))]):
            return "\n".join(lines)
        
        indexed_lines = []
        for i, line in enumerate(lines, start=1):
            indexed_lines.append(f"[L{i}] {line}")
        return "\n".join(indexed_lines)

    @staticmethod
    def parse_lines_map(indexed_text: str) -> Dict[str, str]:
        line_map = {}
        for line in indexed_text.split("\n"):
            m = re.match(r'^\[(L\d+)\]\s*(.*)$', line.strip())
            if m:
                line_map[m.group(1)] = m.group(2)
        return line_map

class MeetingAccountabilityEngine:
    def __init__(self):
        self.meetings: Dict[str, Dict[str, Any]] = {}
        self.tasks: List[Dict[str, Any]] = []
        self.decisions: List[Dict[str, Any]] = []
        self.unresolved_issues: List[Dict[str, Any]] = []

    def register_meeting(self, meeting_id: str, title: str, raw_transcript: str, date_str: Optional[str] = None):
        indexed = TranscriptIndexer.index(raw_transcript)
        line_map = TranscriptIndexer.parse_lines_map(indexed)
        self.meetings[meeting_id] = {
            "id": meeting_id,
            "title": title or meeting_id,
            "date": date_str or datetime.now().strftime("%Y-%m-%d"),
            "raw_transcript": raw_transcript,
            "indexed_transcript": indexed,
            "lines": line_map
        }

    def process_extraction(self, meeting_id: str, extraction: Dict[str, Any]):
        meeting = self.meetings.get(meeting_id)
        meeting_name = meeting["title"] if meeting else meeting_id

        # 1. Process Decisions
        for dec in extraction.get("decisions", []):
            dec_id = str(uuid.uuid4())[:8]
            dec_record = {
                "id": dec_id,
                "meeting_id": meeting_id,
                "meeting_name": meeting_name,
                "text": dec.get("text", "").strip(),
                "source_line": dec.get("source_line", "").strip(),
                "source_text": self._get_source_text(meeting_id, dec.get("source_line", "")),
                "timestamp": datetime.now().isoformat()
            }
            self.decisions.append(dec_record)
            
            # Auto-check if decision resolves any open tasks
            self._auto_resolve_tasks(dec_record)

        # 2. Process Unresolved Issues
        for issue in extraction.get("unresolved_issues", []):
            issue_id = str(uuid.uuid4())[:8]
            issue_record = {
                "id": issue_id,
                "meeting_id": meeting_id,
                "meeting_name": meeting_name,
                "text": issue.get("text", "").strip(),
                "source_line": issue.get("source_line", "").strip(),
                "source_text": self._get_source_text(meeting_id, issue.get("source_line", "")),
                "status": "Open",
                "timestamp": datetime.now().isoformat()
            }
            self.unresolved_issues.append(issue_record)

        # 3. Process Action Items
        for item in extraction.get("action_items", []):
            task_text = item.get("task", "").strip()
            owner = item.get("owner", "Unassigned").strip()
            deadline = item.get("deadline", "None").strip()
            source_line = item.get("source_line", "").strip()
            source_text = self._get_source_text(meeting_id, source_line)
            incoming_status = item.get("status", "New").strip()

            # Find matching existing task
            existing = self._find_matching_task(task_text)

            if existing:
                # Update existing task
                changes = []
                if owner not in ("Unassigned", "None") and owner != existing["owner"]:
                    changes.append(f"Owner changed from '{existing['owner']}' to '{owner}'")
                    existing["owner"] = owner
                elif existing["owner"] in ("Unassigned", "None") and owner not in ("Unassigned", "None"):
                    existing["owner"] = owner
                    changes.append(f"Assigned to '{owner}'")

                if deadline not in ("None", "TBD", "") and deadline != existing["deadline"]:
                    changes.append(f"Deadline updated from '{existing['deadline']}' to '{deadline}'")
                    existing["deadline"] = deadline

                if incoming_status.lower() in ["resolved", "completed", "done"]:
                    existing["status"] = "Resolved"
                    changes.append("Marked Resolved")
                elif existing["status"] != "Resolved":
                    existing["status"] = "Updated / Carried Over"
                    changes.append("Carried over with updates")

                existing["audit_trail"].append({
                    "meeting_id": meeting_id,
                    "meeting_name": meeting_name,
                    "source_line": source_line,
                    "source_text": source_text,
                    "action": "Updated / Carried Over" if existing["status"] != "Resolved" else "Resolved",
                    "details": "; ".join(changes) if changes else "Follow-up discussion in meeting",
                    "timestamp": datetime.now().isoformat()
                })
                existing["last_updated_meeting"] = meeting_id
            else:
                # Create brand new task
                new_task = {
                    "id": f"TASK-{len(self.tasks) + 1:03d}",
                    "task": task_text,
                    "owner": owner if owner else "Unassigned",
                    "deadline": deadline if deadline else "None",
                    "status": incoming_status if incoming_status in ["New", "In Progress", "Resolved", "Blocked"] else "New",
                    "initial_meeting_id": meeting_id,
                    "last_updated_meeting": meeting_id,
                    "source_line": source_line,
                    "source_text": source_text,
                    "audit_trail": [
                        {
                            "meeting_id": meeting_id,
                            "meeting_name": meeting_name,
                            "source_line": source_line,
                            "source_text": source_text,
                            "action": "Created",
                            "details": f"Originated in {meeting_name}",
                            "timestamp": datetime.now().isoformat()
                        }
                    ]
                }
                self.tasks.append(new_task)

    def _find_matching_task(self, task_name: str) -> Optional[Dict[str, Any]]:
        best_match = None
        best_score = 0.0
        for task in self.tasks:
            score = calculate_similarity(task["task"], task_name)
            if score > best_score:
                best_score = score
                best_match = task
        if best_score >= 0.5:
            return best_match
        return None

    def _auto_resolve_tasks(self, decision: Dict[str, Any]):
        dec_text = decision["text"].lower()
        if any(w in dec_text for w in ["completed", "finished", "resolved", "delivered", "done"]):
            for task in self.tasks:
                if task["status"] != "Resolved" and calculate_similarity(task["task"], decision["text"]) >= 0.45:
                    task["status"] = "Resolved"
                    task["audit_trail"].append({
                        "meeting_id": decision["meeting_id"],
                        "meeting_name": decision["meeting_name"],
                        "source_line": decision["source_line"],
                        "source_text": decision["source_text"],
                        "action": "Resolved by Decision",
                        "details": f"Decision noted: {decision['text']}",
                        "timestamp": datetime.now().isoformat()
                    })

    def _get_source_text(self, meeting_id: str, line_ref: str) -> str:
        meeting = self.meetings.get(meeting_id)
        if not meeting or not line_ref:
            return ""
        
        lines_dict = meeting.get("lines", {})
        # Check range e.g. [L4]-[L5]
        range_match = re.findall(r'L\d+', line_ref)
        if not range_match:
            return ""
        
        extracted_lines = []
        for l_num in range_match:
            if l_num in lines_dict:
                extracted_lines.append(f"[{l_num}] {lines_dict[l_num]}")
        return " | ".join(extracted_lines)

    def update_task_manual(self, task_id: str, status: Optional[str] = None, owner: Optional[str] = None, deadline: Optional[str] = None, note: Optional[str] = None):
        for task in self.tasks:
            if task["id"] == task_id:
                details = []
                if status and status != task["status"]:
                    details.append(f"Status changed to {status}")
                    task["status"] = status
                if owner and owner != task["owner"]:
                    details.append(f"Owner changed to {owner}")
                    task["owner"] = owner
                if deadline and deadline != task["deadline"]:
                    details.append(f"Deadline changed to {deadline}")
                    task["deadline"] = deadline
                if note:
                    details.append(f"Note: {note}")

                if details:
                    task["audit_trail"].append({
                        "meeting_id": "MANUAL",
                        "meeting_name": "Manual Dashboard Override",
                        "source_line": "User Action",
                        "source_text": "Manual adjustment by dashboard auditor",
                        "action": "Manual Override",
                        "details": "; ".join(details),
                        "timestamp": datetime.now().isoformat()
                    })
                return task
        return None

    def get_dashboard_summary(self) -> Dict[str, Any]:
        total_tasks = len(self.tasks)
        resolved_count = sum(1 for t in self.tasks if t["status"] == "Resolved")
        carried_over_count = sum(1 for t in self.tasks if "Carried Over" in t["status"])
        unassigned_count = sum(1 for t in self.tasks if t["owner"] in ("Unassigned", "None", ""))
        blocked_count = sum(1 for t in self.tasks if t["status"] == "Blocked")
        active_count = sum(1 for t in self.tasks if t["status"] not in ("Resolved", "Abandoned"))

        return {
            "metrics": {
                "total_tasks": total_tasks,
                "resolved_tasks": resolved_count,
                "active_tasks": active_count,
                "carried_over_tasks": carried_over_count,
                "unassigned_tasks": unassigned_count,
                "blocked_tasks": blocked_count,
                "total_meetings": len(self.meetings),
                "total_decisions": len(self.decisions),
                "total_unresolved": sum(1 for u in self.unresolved_issues if u["status"] == "Open")
            },
            "tasks": self.tasks,
            "decisions": self.decisions,
            "unresolved_issues": self.unresolved_issues,
            "meetings": [
                {
                    "id": m["id"],
                    "title": m["title"],
                    "date": m["date"],
                    "line_count": len(m["lines"]),
                    "raw_transcript": m["raw_transcript"],
                    "indexed_transcript": m["indexed_transcript"]
                }
                for m in self.meetings.values()
            ]
        }
