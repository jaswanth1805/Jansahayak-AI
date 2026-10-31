# JanSahayak AI — Pitch Presentation Outline
## 5–7 Slides for Hackathon Judges

---

## SLIDE 1: Title Slide

**Visual:** Dark navy/indigo gradient background. Large white text.

```
JanSahayak AI 🇮🇳
Government Policies Made Understandable to Everyone

[Team Name] | Hackathon 2026
```

**Sub-headline (in three languages):**
- English: *Your AI guide to Indian government schemes*
- Hindi: *सरकारी योजनाओं का आपका AI मार्गदर्शक*
- Telugu: *ప్రభుత్వ పథకాలకు మీ AI మార్గదర్శి*

---

## SLIDE 2: The Problem

**Visual:** Split image — complex government document on left, confused citizen on right

**Headline:** 80 Crore Indians. Countless Schemes. Zero Understanding.

**Statistics:**
- India runs **1,700+ government welfare schemes**
- **69%** of eligible citizens don't apply due to unawareness
- **89%** of scheme documents are only in English or formal Hindi
- Farmers lose **₹18,000 crore/year** in unclaimed PM-KISAN benefits

**Pain Points:**
- Complex bureaucratic language
- No regional language support
- No personalized eligibility guidance
- Disconnected, hard-to-navigate portals

---

## SLIDE 3: Our Solution

**Visual:** Clean product screenshot of JanSahayak AI chat interface

**Headline:** JanSahayak AI — Your Intelligent Government Assistant

**What it does:**
1. 🔍 Searches **real government schemes** from official sources live
2. 📄 Understands **uploaded government documents** using AI
3. ✅ Checks **personal eligibility** against actual criteria
4. 🌐 Communicates in **English, Hindi, and Telugu**
5. 🎙️ Supports **voice input and audio responses**
6. 📌 Shows **official citations** for every claim

---

## SLIDE 4: Technical Architecture

**Visual:** Architecture diagram (from README)

**Headline:** Built Right. Built for Real.

```
User Question
    │
    ▼ [LangGraph Agent]
[1] Intent Classification
    │
    ▼
[2] Official Source Retrieval ──► MyScheme API + India.gov.in
    │
    ▼
[3] RAG Pipeline ──► ChromaDB Vector Store
    │
    ▼
[4] Eligibility Analysis (Deterministic + LLM)
    │
    ▼
[5] Source Verification
    │
    ▼
[6] Multilingual Response (EN/HI/TE)
    │
    ▼
[7] Audio Generation (gTTS)
```

**Stack:** Next.js | FastAPI | LangGraph | ChromaDB | OpenAI | gTTS

---

## SLIDE 5: Live Demo Highlights

**Visual:** 3-4 screenshots of the application

**Screenshot 1:** Landing page with multilingual headline
**Screenshot 2:** AI assistant responding in Telugu with source citations
**Screenshot 3:** Eligibility checker showing satisfied/unsatisfied conditions
**Screenshot 4:** Document analyzer with key clauses extracted from a PDF

**Headline:** What Makes Us Different

| Others | JanSahayak AI |
|--------|---------------|
| Generic chatbot | Government-specialized AI agent |
| Pre-loaded FAQ | Live official API retrieval |
| English only | English + Hindi + Telugu |
| No citations | Official source citations always |
| No eligibility | Personalized eligibility checking |
| Text only | Voice input + audio output |

---

## SLIDE 6: Impact & Compliance

**Visual:** Map of India with highlighted reach

**Headline:** Real Impact. Real Data. Real Citizens.

**Target beneficiaries:**
- 👨‍🌾 180M+ farmers (PM-KISAN, crop insurance)
- 🎓 45M+ students (scholarship schemes)
- 👩 500M+ women (health, safety, business schemes)
- 🏚️ 300M+ rural households (housing, NREGA)

**Hackathon Compliance:**
- ✅ **Zero fake data** — all schemes from official APIs
- ✅ **Zero hardcoded JSON** — live retrieval every time
- ✅ **Source citations** — every claim traceable
- ✅ **Actual agent reasoning** — LangGraph with 7 tool steps
- ✅ **Real voice** — Web Speech API + gTTS
- ✅ **Privacy first** — no personal data stored

---

## SLIDE 7: Next Steps & Deployment

**Visual:** Roadmap timeline

**Current (MVP):**
- ✅ 3 languages: English, Hindi, Telugu
- ✅ MyScheme + India.gov.in + Data.gov.in integration
- ✅ PDF document understanding
- ✅ Voice I/O
- ✅ Eligibility assessment

**Short-term (Post-hackathon):**
- 📱 Mobile app (React Native)
- 🗣️ 10 more Indian languages
- 📊 State-specific scheme filtering
- 🔔 Deadline reminders and notifications

**Long-term:**
- 🤝 Official government API partnerships
- 📞 IVR integration for feature phones
- 🏛️ Integration with DigiLocker for document verification

**Deployment:**
- Frontend → Vercel (free tier)
- Backend → Render (free tier)
- Database → ChromaDB (local) → Supabase pgvector (production)

---

## SPEAKING NOTES

### Opening hook (for presenter):
*"Imagine a farmer in rural Andhra Pradesh who is eligible for PM-KISAN, Fasal Bima Yojana, and a state agricultural subsidy — but doesn't know it. He loses thousands of rupees every year not because he's ineligible, but because he can't navigate the bureaucracy. JanSahayak AI is his digital government assistant."*

### Technical talking point:
*"This is not a chatbot. It's a multi-step AI agent that actually calls government APIs, retrieves real data, runs eligibility algorithms, verifies its own claims against sources, and responds in the user's language. Every step is logged and visible to the user."*

### Closing:
*"JanSahayak AI is the intersection of AI, civic tech, and language accessibility. We believe that in India, the right to information should not be gatekept by English proficiency or bureaucratic complexity."*

---

*Presentation time: ~5 minutes + 2 minutes Q&A*
