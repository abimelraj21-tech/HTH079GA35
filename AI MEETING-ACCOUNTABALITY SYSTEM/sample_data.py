# Pre-configured sample meetings demonstrating cross-meeting accountability lifecycle

SAMPLE_MEETINGS = [
    {
        "id": "Meeting_01",
        "title": "API Migration Kickoff",
        "date": "2026-10-01",
        "raw_transcript": """[L1] Alex: Welcome team. Let's discuss the API migration.
[L2] Priya: I can take ownership of updating the database schema by October 5th.
[L3] Alex: Great. Rahul, can you handle the frontend integration?
[L4] Rahul: I'm not sure if I have bandwidth, but I can look into it by next week.
[L5] Alex: Okay, let's keep frontend task as unassigned for now until Rahul confirms.
[L6] Priya: What about the security audit?
[L7] Alex: We didn't decide on the security vendor yet. Unresolved.""",
        "extraction": {
            "decisions": [],
            "action_items": [
                {
                    "task": "Update database schema",
                    "owner": "Priya",
                    "deadline": "October 5th",
                    "source_line": "[L2]",
                    "status": "New"
                },
                {
                    "task": "Frontend integration",
                    "owner": "Unassigned",
                    "deadline": "None",
                    "source_line": "[L4]-[L5]",
                    "status": "New"
                }
            ],
            "unresolved_issues": [
                {
                    "text": "Security audit vendor selection",
                    "source_line": "[L7]"
                }
            ]
        }
    },
    {
        "id": "Meeting_02",
        "title": "API Migration Checkpoint 1",
        "date": "2026-10-06",
        "raw_transcript": """[L1] Alex: Follow up on last week's API migration tasks.
[L2] Priya: Database schema update is completed ahead of time.
[L3] Rahul: I checked my bandwidth, I will finish the frontend integration by October 12th.
[L4] Alex: Perfect. Who is taking the security audit?
[L5] Alex: I will personally take the security audit proposal by October 10th.""",
        "extraction": {
            "decisions": [
                {
                    "text": "Database schema update completed ahead of time",
                    "source_line": "[L2]"
                }
            ],
            "action_items": [
                {
                    "task": "Frontend integration",
                    "owner": "Rahul",
                    "deadline": "October 12th",
                    "source_line": "[L3]",
                    "status": "Updated / Carried Over"
                },
                {
                    "task": "Security audit proposal",
                    "owner": "Alex",
                    "deadline": "October 10th",
                    "source_line": "[L5]",
                    "status": "New"
                }
            ],
            "unresolved_issues": []
        }
    },
    {
        "id": "Meeting_03",
        "title": "API Migration Final Review & Release",
        "date": "2026-10-13",
        "raw_transcript": """[L1] Alex: Welcome to the final review for API Migration.
[L2] Rahul: Frontend integration has been completed and verified against the new schema.
[L3] Alex: Decision: We selected SecureCloud as our official security vendor, closing audit proposal.
[L4] Priya: I will coordinate the staging smoke tests by October 16th.
[L5] Alex: Production release target date is finalized for October 20th.""",
        "extraction": {
            "decisions": [
                {
                    "text": "Frontend integration completed and verified",
                    "source_line": "[L2]"
                },
                {
                    "text": "Selected SecureCloud as official security audit vendor",
                    "source_line": "[L3]"
                },
                {
                    "text": "Production release target date finalized for October 20th",
                    "source_line": "[L5]"
                }
            ],
            "action_items": [
                {
                    "task": "Frontend integration",
                    "owner": "Rahul",
                    "deadline": "October 12th",
                    "source_line": "[L2]",
                    "status": "Resolved"
                },
                {
                    "task": "Security audit proposal",
                    "owner": "Alex",
                    "deadline": "October 10th",
                    "source_line": "[L3]",
                    "status": "Resolved"
                },
                {
                    "task": "Coordinate staging smoke tests",
                    "owner": "Priya",
                    "deadline": "October 16th",
                    "source_line": "[L4]",
                    "status": "New"
                }
            ],
            "unresolved_issues": []
        }
    }
]
