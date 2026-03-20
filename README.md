# 🔗 Nexus — AI Group Project Manager

> **Solving "Project Amnesia" in student teams using persistent AI memory**

[![Streamlit](https://img.shields.io/badge/Built%20with-Streamlit-FF4B4B?style=flat&logo=streamlit)](https://streamlit.io)
[![Groq](https://img.shields.io/badge/LLM-Groq%20LLaMA%203.3-00A67E?style=flat)](https://groq.com)
[![Hindsight](https://img.shields.io/badge/Memory-Hindsight-6C63FF?style=flat)](https://hindsight.vectorize.io)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat&logo=python)](https://python.org)

---

## 🧠 The Problem — Project Amnesia

Every student hackathon team faces the same frustration:

- *"Wait, why did we choose React again?"*
- *"Who was supposed to do the backend?"*
- *"Didn't we already set a deadline for this?"*

Decisions get lost in chat threads. Roles get forgotten. Deadlines get missed.
**Nexus fixes this.**

---

## 💡 What is Nexus?

Nexus is an **AI-powered group project manager** that acts as your team's permanent memory. It remembers every decision, assignment, and update — and lets you ask questions about your project in plain English.

---

## ✨ Key Features

### 🧠 1. Persistent Contextual Memory
Every team decision, role assignment, and task update is saved permanently using **Hindsight SDK**. Every entry is tagged with author, category, and timestamp — so nothing is ever lost.

### 🔍 2. Smart AI Chat
Ask anything about your project in natural language. Nexus retrieves the top 5 most relevant memories and answers using your team's actual data — not generic AI knowledge.

> *"Who is handling the frontend?"* → Nexus answers: *"Priya was assigned Frontend Developer on Mar 20 by the Team Leader."*

### ⚠️ 3. Conflict Alert System
Before saving any new decision, Nexus checks existing memories for contradictions. If a conflict is detected (e.g. changing a deadline that was already set), it shows a warning:

> *"⚠️ This contradicts a decision made on Mar 20, 2026 — Deadline was set to March 30th."*

### 👥 4. Team Management
- Leaders can **create teams** with a project name and description
- Members can **join teams** using the team name
- Leaders can **assign roles** (Frontend, Backend, DevOps, ML Engineer, etc.)

### 🎓 5. Teacher Dashboard
Teachers get an exclusive view showing:
- All teams and their members
- Role assignments
- Progress tracker per team
- Full activity logbook — like a digital project diary

### 🕰️ 6. Truth Timeline
A real-time feed of all team decisions, tasks, and updates — color-coded by category, with author and timestamp on every entry.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | Streamlit (Python) |
| **LLM** | Groq — LLaMA 3.3 70B Versatile |
| **Memory** | Hindsight SDK (`hindsight-client`) |
| **Language** | Python 3.10+ |
| **Fonts** | Inter + IBM Plex Sans + IBM Plex Mono |
| **Deployment** | Streamlit Cloud |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────┐
│              Nexus — app.py                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │  Login   │  │Dashboard │  │ AI Chat  │  │
│  │  System  │  │& Stats   │  │          │  │
│  └──────────┘  └──────────┘  └──────────┘  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │  Team    │  │Timeline  │  │ Teacher  │  │
│  │ Manager  │  │          │  │  View    │  │
│  └──────────┘  └──────────┘  └──────────┘  │
└──────────────────┬──────────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
   ┌────▼────┐          ┌─────▼─────┐
   │  Groq   │          │ Hindsight │
   │ LLaMA   │          │  Memory   │
   │  3.3    │          │   SDK     │
   └─────────┘          └───────────┘
```

---

## 📁 Project Structure

```
nexus/
├── app.py                  ← Main Streamlit app (UI + routing)
├── config.py               ← Environment variables & constants
├── requirements.txt        ← Python dependencies
├── .env.example            ← Environment variable template
└── utils/
    ├── __init__.py
    ├── groq_agent.py       ← Groq LLM + conflict detection + chat
    ├── hindsight_helper.py ← Hindsight memory (retain/recall)
    └── styles.py           ← Complete CSS theme
```

---

## 🚀 Run Locally

### 1. Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/nexus.git
cd nexus
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set up environment variables
```bash
cp .env.example .env
```
Edit `.env` and add your keys:
```
GROQ_API_KEY=your_groq_key_here
HINDSIGHT_API_URL=http://localhost:8888
HINDSIGHT_BANK_ID=nexus-project
HINDSIGHT_API_KEY=
```

### 4. Get a free Groq API key
👉 [console.groq.com](https://console.groq.com)

### 5. Run the app
```bash
streamlit run app.py
```

---

## 🌐 Live Demo

👉 **[nexus-app.streamlit.app](https://YOUR_USERNAME-nexus.streamlit.app)**

---

## 🎯 Demo Walkthrough

| Step | Action | Feature Shown |
|---|---|---|
| 1 | Login as **Team Leader** | Login system |
| 2 | Create team "Team Phoenix" | Team creation |
| 3 | Open new tab → login as **Student** → join team | Team joining |
| 4 | Leader assigns roles (Frontend/Backend/Docs) | Role management |
| 5 | Log: *"We chose React for frontend"* | Memory retention |
| 6 | Log: *"Deadline is March 30th"* | Decision logging |
| 7 | Ask chat: *"Who handles the frontend?"* | AI smart recall |
| 8 | Log: *"Deadline is now April 15th"* | **⚠️ Conflict alert fires** |
| 9 | Login as **Teacher** → view Teacher Dashboard | Progress monitoring |

---

## 👥 User Roles

| Role | Capabilities |
|---|---|
| 🧑‍💻 **Student / Member** | Join teams, log events, use AI chat |
| 👑 **Team Leader** | Create teams, assign roles, all member features |
| 🎓 **Teacher / Mentor** | View all teams, monitor progress, full logbook access |

---

## 🔮 Future Roadmap

- [ ] Real-time team collaboration with WebSockets
- [ ] File attachments in memory entries
- [ ] Email/Slack notifications for conflict alerts
- [ ] Export project history as PDF report
- [ ] Voice-to-memory via speech recognition

---

## 🙏 Acknowledgements

- [Groq](https://groq.com) — Ultra-fast LLM inference
- [Hindsight](https://hindsight.vectorize.io) — Persistent AI memory SDK
- [Streamlit](https://streamlit.io) — Rapid Python UI framework

---

## 📄 License

MIT License — free to use, modify and distribute.

---

<div align="center">
  <strong>Built with ❤️ for Hackathon 2026</strong><br>
  <em>Nexus — Never lose a team decision again.</em>
</div>
