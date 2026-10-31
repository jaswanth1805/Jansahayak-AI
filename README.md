# JanSahayak AI 🇮🇳

> **Government policies made understandable to everyone.**

An AI-powered multilingual platform that helps Indian citizens understand government welfare schemes, their rights, and eligibility for benefits — in English, Hindi, and Telugu.

---

## 🎯 Problem Statement

Millions of Indian citizens are unaware of or unable to access government schemes they are entitled to. Government documents are often complex, in bureaucratic language, and not available in regional languages. JanSahayak AI bridges this gap.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🤖 **AI Document Understanding** | Upload government PDFs, ask questions, get simple explanations with page-level citations |
| 🔍 **Live Scheme Discovery** | Real-time scheme data from MyScheme.gov.in, India.gov.in, Data.gov.in |
| ✅ **Eligibility Assessment** | Personalized eligibility checking against official criteria |
| 🌐 **Multilingual AI Assistant** | Chat in English, Hindi, or Telugu |
| 🎙️ **Voice Assistance** | Ask questions by voice, hear answers in your language |
| 📌 **Source Verification** | Every answer backed by official sources with citations |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    JanSahayak AI                            │
├───────────────────────┬─────────────────────────────────────┤
│   FRONTEND (Next.js)  │         BACKEND (FastAPI)           │
│                       │                                     │
│  ┌─────────────────┐  │  ┌────────────────────────────────┐ │
│  │  Landing Page   │  │  │    JanSahayak Orchestrator     │ │
│  │  AI Assistant   │◄─┼─►│    (LangGraph Agent)           │ │
│  │  Scheme Explorer│  │  │                                │ │
│  │  Eligibility    │  │  │  ┌──────────┐ ┌────────────┐  │ │
│  │  Doc Analyzer   │  │  │  │ Tools    │ │ RAG Pipeline│  │ │
│  │  About          │  │  │  └──────────┘ └────────────┘  │ │
│  └─────────────────┘  │  └────────────────────────────────┘ │
│                       │                                     │
│  TypeScript + Tailwind│  ┌───────────┐  ┌───────────────┐  │
│  shadcn/ui + Lucide   │  │  ChromaDB │  │ Gov Sources   │  │
└───────────────────────┴──│  (Vector) │──│ MyScheme API  │──┘
                           │           │  │ India.gov.in  │
                           └───────────┘  │ Data.gov.in   │
                                          └───────────────┘
```

### Agent Workflow

```
User Question
     │
     ▼
[1] Classify Intent
     │ scheme_query / eligibility / document_query / general
     ▼
[2] Retrieve Official Information
     │ search_official_sources() + retrieve_relevant_passages()
     ▼
[3] Extract Key Facts
     │ eligibility criteria, benefits, documents, deadlines
     ▼
[4] Check Eligibility (if profile provided)
     │ analyze_scheme_eligibility()
     ▼
[5] Verify Claims
     │ verify_source_and_citations()
     ▼
[6] Generate Response
     │ In user's language (EN/HI/TE)
     ▼
[7] Generate Audio (if requested)
     │ generate_voice_response()
     ▼
[8] Return with Citations
     └─► Answer + Sources + Agent Steps + Audio URL
```

---

## 🛠️ Technology Stack

### Frontend
- **Next.js 14** (App Router)
- **TypeScript**
- **Tailwind CSS**
- **shadcn/ui** components
- **Lucide React** icons
- **Web Speech API** (browser-native STT)

### Backend
- **Python 3.14** / **FastAPI**
- **LangGraph** (agent orchestration)
- **LangChain** (RAG pipeline)
- **ChromaDB** (vector storage, local)
- **OpenAI API** (LLM + embeddings)
- **PyMuPDF** (PDF processing)
- **gTTS** (text-to-speech)
- **deep-translator** (multilingual)

### Data Sources (Official)
- **MyScheme API** — `https://api.myscheme.gov.in`
- **India.gov.in** — `https://www.india.gov.in`
- **Data.gov.in CKAN API** — `https://data.gov.in/api/3/action`

---

## 🚀 Installation

### Prerequisites
- Python 3.9+
- Node.js 18+
- npm or yarn

### 1. Clone the repository
```bash
git clone https://github.com/your-team/jansahayak-ai.git
cd jansahayak-ai
```

### 2. Backend Setup
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your OpenAI API key
```

### 3. Frontend Setup
```bash
cd frontend
npm install
cp .env.example .env.local
# Edit .env.local if needed
```

---

## 🔑 Environment Variables

### Backend (`backend/.env`)

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | **Yes** | OpenAI API key for LLM and embeddings |
| `OPENAI_MODEL` | No | Model to use (default: `gpt-4o-mini`) |
| `BACKEND_HOST` | No | Server host (default: `0.0.0.0`) |
| `BACKEND_PORT` | No | Server port (default: `8000`) |
| `CORS_ORIGINS` | No | Allowed frontend origins |
| `MAX_UPLOAD_SIZE_MB` | No | Max PDF upload size (default: `20`) |
| `DATA_GOV_API_KEY` | No | data.gov.in API key (higher rate limits) |

### Frontend (`frontend/.env.local`)

| Variable | Required | Description |
|----------|----------|-------------|
| `NEXT_PUBLIC_BACKEND_URL` | No | Backend URL (default: `http://localhost:8000`) |

---

## 📡 API Documentation

### Chat
- `POST /api/chat/` — Main AI chat endpoint
- `POST /api/chat/voice-input` — Voice transcription
- `GET /api/chat/session/{session_id}` — Get session history

### Schemes
- `POST /api/schemes/search` — Search government schemes
- `GET /api/schemes/{scheme_id}` — Get scheme details
- `GET /api/schemes/states/list` — List Indian states
- `GET /api/schemes/categories/list` — List scheme categories

### Eligibility
- `POST /api/eligibility/check` — Check scheme eligibility
- `POST /api/eligibility/questions` — Get questions for a scheme

### Documents
- `POST /api/documents/upload` — Upload PDF
- `POST /api/documents/query` — Query uploaded document
- `DELETE /api/documents/{document_id}` — Delete document

### Voice
- `POST /api/voice/synthesize` — Text-to-speech
- `GET /api/voice/audio/{audio_id}` — Get audio file

---

## ▶️ Running Locally

### Backend
```bash
cd backend
# Activate venv first
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

API docs available at: `http://localhost:8000/docs`

### Frontend
```bash
cd frontend
npm run dev
```

App available at: `http://localhost:3000`

---

## 🚢 Deployment

### Backend → Render.com
1. Create a new Web Service on Render
2. Connect your GitHub repository
3. Set Root Directory: `backend`
4. Build Command: `pip install -r requirements.txt`
5. Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
6. Add environment variables in Render dashboard

### Frontend → Vercel
1. Connect your GitHub repository to Vercel
2. Set Root Directory: `frontend`
3. Add `NEXT_PUBLIC_BACKEND_URL` environment variable
4. Deploy

---

## 🧪 Test Scenarios

| Scenario | Expected Behaviour |
|----------|--------------------|
| English scheme query | Full scheme info with sources |
| Hindi question | Response in Hindi |
| Telugu question | Response in Telugu |
| Missing user info | AI asks for required details |
| Upload government PDF | Extract key clauses and dates |
| Ask about uploaded PDF | RAG-grounded answer with page citations |
| No matching scheme found | Honest "not found" message |
| Government API unavailable | Clear error, tries alternate sources |
| Voice input | Transcribed and processed |
| Voice output | Audio generated in selected language |

---

## 👥 Team Contribution Areas

| Area | Files | Technologies |
|------|-------|-------------|
| **AI & Agent** | `backend/app/agents/` | LangGraph, LangChain, OpenAI |
| **Government Data** | `backend/app/services/government_sources.py` | HTTP, web scraping |
| **RAG Pipeline** | `backend/app/rag/` | ChromaDB, embeddings |
| **API Routes** | `backend/app/api/` | FastAPI, Pydantic |
| **Landing Page** | `frontend/src/app/page.tsx` | Next.js, Tailwind |
| **AI Assistant UI** | `frontend/src/app/assistant/` | React, hooks |
| **Scheme Explorer** | `frontend/src/app/schemes/` | React, API calls |
| **Eligibility Wizard** | `frontend/src/app/eligibility/` | Multi-step form |
| **Document Analyzer** | `frontend/src/app/documents/` | File upload, RAG |

---

## ⚠️ Limitations

- Eligibility assessments are **preliminary** — final decisions by government authorities
- Government APIs may have rate limits or downtime
- OCR quality depends on scan quality
- AI may occasionally make mistakes — always verify with official sources
- Voice features require a modern browser

---

## 📜 Privacy

- No user accounts required
- Uploaded documents deleted after 24 hours
- No personal eligibility data stored permanently
- AI is not a government authority and cannot guarantee benefits

---

*Built for the Government Policy Hackathon 2026 | Powered by official Indian government data*
