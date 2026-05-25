# 🩺 MediAssist AI — Healthcare Triage Platform

An end-to-end AI-powered healthcare triage solution built with Flask + Claude API. Patients describe their symptoms and receive an intelligent assessment including urgency level, possible conditions, recommended care pathway, and next steps.

---

## ✨ Features

- **AI Symptom Triage** — Powered by Claude (claude-sonnet-4)
- **Urgency Classification** — EMERGENCY / URGENT / MODERATE / SELF-CARE
- **Care Pathway Routing** — ER, Urgent Care, Primary Care, Telehealth, Home Care
- **Possible Conditions** — AI-suggested differential list
- **Follow-up Chat** — Ask clarifying questions in context
- **Responsible AI** — Built-in disclaimers, emergency escalation, ethical guardrails

---

## 🚀 Deploy to Render (5 minutes)

### 1. Push to GitHub
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/mediassist-ai.git
git push -u origin main
```

### 2. Create Render Web Service
1. Go to [render.com](https://render.com) → **New** → **Web Service**
2. Connect your GitHub repo
3. Render auto-detects `render.yaml` — just click **Deploy**

### 3. Set Environment Variable
In Render dashboard → **Environment** → Add:
```
ANTHROPIC_API_KEY = your_anthropic_api_key_here
```

### 4. Done! 🎉
Your app will be live at `https://mediassist-ai.onrender.com`

---

## 🏃 Run Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Set API key
export ANTHROPIC_API_KEY=your_key_here

# Run
python app.py
# → http://localhost:5000
```

---

## 📁 Project Structure

```
mediassist/
├── app.py              # Flask backend + AI routes
├── requirements.txt    # Python dependencies
├── render.yaml         # Render deployment config
├── README.md
└── templates/
    └── index.html      # Full frontend (single-file)
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Frontend UI |
| POST | `/api/triage` | Initial symptom analysis |
| POST | `/api/followup` | Follow-up conversation |
| GET | `/health` | Health check |

### POST `/api/triage`
```json
{
  "symptoms": "severe headache and nausea",
  "age": "34",
  "gender": "Female",
  "duration": "6–24 hours",
  "medical_history": "migraines",
  "conversation_history": []
}
```

### Response
```json
{
  "urgency": "MODERATE",
  "urgency_color": "yellow",
  "summary": "Symptoms are consistent with a migraine episode...",
  "possible_conditions": ["Migraine", "Tension Headache", "Cluster Headache"],
  "recommended_action": "Take prescribed migraine medication if available...",
  "care_pathway": "Primary Care",
  "follow_up_questions": ["Do you have visual disturbances?", "Is this your worst headache ever?"],
  "next_steps": ["Rest in a dark, quiet room", "Stay hydrated", "Monitor for worsening symptoms"],
  "disclaimer": "This is AI-generated guidance and not a medical diagnosis."
}
```

---

## ⚕️ Responsible AI & Ethics

This project demonstrates:
- **Transparent AI** — Always identified as AI, never impersonating a doctor
- **Emergency escalation** — Life-threatening symptoms route to 911
- **Medical disclaimers** — Prominent throughout the UI
- **Appropriate scope** — Triage guidance only, no prescriptions or diagnoses

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | HTML/CSS/JS (single-file, no build step) |
| Backend | Python Flask |
| AI | Anthropic Claude (claude-sonnet-4) |
| Deployment | Render (render.yaml) |
| WSGI | Gunicorn |

---

## 📋 Portfolio Notes (Week 6 Deliverable)

**Theme**: End-to-End AI Solution & Career Readiness  
**Industry**: Healthcare  
**Core Competencies Demonstrated**:
- ✅ End-to-end solution design (frontend → API → AI → response)
- ✅ Problem-solving using AI (symptom triage, differential generation)
- ✅ Responsible AI (disclaimers, escalation, ethical guardrails)
- ✅ Real-world use case mapping (replaces basic triage hotlines)
- ✅ Deployable functional prototype (Render-ready)
