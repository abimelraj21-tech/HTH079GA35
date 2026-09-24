# 🎯 AI Meeting-to-Accountability System (HTH-GA-03)

An enterprise-grade, zero-hallucination web application that parses meeting transcripts into structured decisions, action items, assignees, deadlines, and unresolved issues — while tracking follow-through across multiple recurring meetings.

![License](https://img.shields.io/badge/License-MIT-blue.svg)
![Status](https://img.shields.io/badge/Status-Complete_MVP-success)
![UI](https://img.shields.io/badge/UI-TailwindCSS_--_Inter_Font-indigo)

---

## 📌 Problem Statement
Teams frequently lose track of commitments made during meetings, leading to forgotten or misattributed action items. Existing transcript summaries often hallucinate deliverables or fail to trace tasks across consecutive syncs.

## ✨ Core Features

* **Zero-Hallucination Parsing**: Every extracted action item is tied to an explicit source transcript line index and timestamp audit trail.
* **Ambiguous Ownership Resolution**: Detects explicitly assigned tasks versus ambiguous mentions (e.g., *"someone should handle..."*).
* **Cross-Meeting Status Tracker**: Automatically categorizes items as `New`, `Carried-Over`, `Overdue`, or `Completed` across multi-meeting timelines.
* **Stakeholder Digest Generator**: Instant 1-click export to Slack-formatted Markdown or Executive Email drafts.
* **Discussion Tension & Risk Analyzer**: Identifies sentiment triggers, blockers, and project risks discussed in transcripts.

---

## 🚀 Live Demo & Quick Start

### Option 1: Direct Browser Run
1. Clone this repository:
   ```bash
   git clone [https://github.com/YOUR_USERNAME/meeting-accountability-system.git](https://github.com/YOUR_USERNAME/meeting-accountability-system.git)
