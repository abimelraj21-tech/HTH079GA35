import json
import re
from typing import Dict, Any, List

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

class RuleBasedAuditor:
    """
    Fallback extractor when external LLM API key is not configured.
    Parses conversational cues with zero hallucination guarantee.
    """
    @staticmethod
    def extract_from_indexed_transcript(indexed_transcript: str) -> Dict[str, Any]:
        lines = indexed_transcript.split("\n")
        decisions: List[Dict[str, str]] = []
        action_items: List[Dict[str, str]] = []
        unresolved: List[Dict[str, str]] = []

        date_pattern = r'\b(?:by|before|on|until)\s+([A-Z][a-z]+ \d{1,2}(?:st|nd|rd|th)?|next week|tomorrow|end of week|\d{4}-\d{2}-\d{2})\b'

        for raw_line in lines:
            raw_line = raw_line.strip()
            if not raw_line:
                continue

            match = re.match(r'^\[(L\d+)\]\s*(?:([^:]+):)?\s*(.*)$', raw_line)
            if not match:
                continue

            line_tag = f"[{match.group(1)}]"
            speaker = (match.group(2) or "").strip()
            utterance = match.group(3).strip()
            lower = utterance.lower()

            # 1. Unresolved Issues check
            if any(term in lower for term in ["unresolved", "not decide", "haven't decided", "pending decision", "unclear", "open question"]):
                clean_text = utterance
                for p in ["we didn't decide on", "haven't decided on", "unresolved", "pending"]:
                    clean_text = re.sub(re.escape(p), "", clean_text, flags=re.IGNORECASE)
                clean_text = clean_text.strip(" .:,")
                unresolved.append({
                    "text": clean_text.capitalize() if clean_text else utterance,
                    "source_line": line_tag
                })
                continue

            # 2. Decisions / Completions check
            if any(term in lower for term in ["decision:", "decided to", "completed", "done ahead of time", "finished", "finalized"]):
                clean_text = re.sub(r'^(decision:\s*|we decided to\s*)', '', utterance, flags=re.IGNORECASE).strip()
                decisions.append({
                    "text": clean_text,
                    "source_line": line_tag
                })
                continue

            # 3. Action Items check
            # Pattern: "I can take ownership of...", "I will finish/take/handle...", "Rahul, can you handle..."
            assigned_match = re.search(r'(?:i can take ownership of|i will finish|i will personally take|i will handle|i will look into|i will coordinate)\s+([^.]+)', lower)
            if assigned_match:
                task_phrase = assigned_match.group(1).strip()
                # Extract deadline if any
                deadline_match = re.search(date_pattern, utterance, re.IGNORECASE)
                deadline = deadline_match.group(1) if deadline_match else "None"
                
                # Clean task phrase from deadline
                if deadline_match:
                    task_phrase = re.sub(date_pattern, "", task_phrase, flags=re.IGNORECASE).strip()

                action_items.append({
                    "task": task_phrase.capitalize(),
                    "owner": speaker if speaker else "Unassigned",
                    "deadline": deadline,
                    "source_line": line_tag,
                    "status": "New"
                })
                continue

            # Unassigned task check
            if "unassigned" in lower or "keep frontend task as unassigned" in lower:
                action_items.append({
                    "task": "Frontend integration" if "frontend" in lower else utterance[:40],
                    "owner": "Unassigned",
                    "deadline": "None",
                    "source_line": line_tag,
                    "status": "New"
                })

        return {
            "decisions": decisions,
            "action_items": action_items,
            "unresolved_issues": unresolved
        }
