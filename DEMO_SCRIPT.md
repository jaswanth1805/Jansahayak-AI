# JanSahayak AI — Live Demo Script
## Hackathon Demonstration Guide (2–3 Minutes)

---

## PRE-DEMO CHECKLIST

Before the demo, ensure:
- [ ] Backend running: `http://localhost:8000/health` returns `{"status": "ok"}`
- [ ] Frontend running: `http://localhost:3000` loads correctly
- [ ] OpenAI API key configured in `backend/.env`
- [ ] Internet connection available (for government API calls)
- [ ] Browser: Chrome or Edge (best Web Speech API support)
- [ ] Language set to **Telugu** or **Hindi** for dramatic effect

---

## DEMO FLOW (2 Minutes 30 Seconds)

### [0:00 – 0:20] Open the Landing Page

**Action:** Open `http://localhost:3000`

**Narrate:**
> "This is JanSahayak AI — a platform that makes Indian government policies understandable to every citizen. Millions of people are unaware of schemes they're entitled to. JanSahayak AI solves that."

**Point out:**
- The headline in English, Hindi, and Telugu
- "Powered by official government data" section
- The feature cards

---

### [0:20 – 0:45] Language Selection

**Action:** Click the language selector in the header. Select **Telugu** (తెలుగు).

**Narrate:**
> "A farmer in Andhra Pradesh shouldn't need to know English to access their rights. Let's switch to Telugu."

---

### [0:45 – 1:15] Ask a Real Government Question

**Action:** Click "Start Asking" → Navigate to `/assistant`

**Type (or paste) this question in Telugu:**
```
రైతులకు ఏ ప్రభుత్వ పథకాలు అందుబాటులో ఉన్నాయి?
```
*(Translation: What government schemes are available for farmers?)*

**OR in Hindi:**
```
किसानों के लिए कौन से सरकारी योजनाएं उपलब्ध हैं?
```

**Action:** Send the message.

**Narrate (while the agent runs):**
> "Watch the agent's steps on the left. It's not just calling a language model — it's classifying the intent, searching official government sources like MyScheme.gov.in, retrieving actual scheme data, and generating a grounded response."

**When response arrives, point out:**
- The Telugu/Hindi response text
- The "Agent Steps" section showing each tool that was called
- The source citations (MyScheme, India.gov.in)
- The suggested follow-up questions

---

### [1:15 – 1:40] Eligibility Assessment

**Action:** Click one of the suggested questions about eligibility, OR navigate to `/eligibility`

**Narrate:**
> "Now let's check eligibility. I'll fill in a sample profile."

**Fill in:**
- What are you looking for: `PM-KISAN farming scheme`
- Age: `45`
- State: `Andhra Pradesh`
- Occupation: `Farmer`
- Annual Income: `80000`

**Action:** Submit the form.

**Narrate:**
> "The system fetches the actual eligibility criteria from MyScheme, compares them with the user's profile, and tells them exactly which conditions they satisfy and which they don't."

**Point out when results appear:**
- Status badge: "Likely Eligible" (green)
- Conditions satisfied (green checkmarks)
- Required documents list
- Official application link button

---

### [1:40 – 2:00] Scheme Explorer

**Action:** Navigate to `/schemes`

**Type in search:** `health insurance women`

**Narrate:**
> "Users can also browse and discover schemes. This data is fetched live from MyScheme's official API — not a database, not hardcoded JSON."

**Point out:**
- The "Retrieved from official sources" badge with timestamp
- Scheme cards with ministry/state info
- "Last verified" date
- Official link buttons

---

### [2:00 – 2:20] Voice Interaction

**Action:** Go back to `/assistant`. Click the microphone button.

**Speak (in English or Hindi):**
> "What scholarships are available for engineering students?"

**Narrate:**
> "Voice support works through the browser's Web Speech API, so no additional microphone permissions are needed beyond what the browser already supports."

**When answer appears:**
- Click the audio play button on the response
- **Narrate:** "And we can hear the answer — the government scheme explained in audio, in the selected language."

---

### [2:20 – 2:30] Source Verification

**Action:** Expand the "Sources" section of any AI response.

**Narrate:**
> "Every factual claim is backed by a citation. Users can see exactly where the information came from, when it was retrieved, and click through to the official government URL. No hallucinations, no fake data."

---

## KEY TALKING POINTS FOR JUDGES

### Technical Depth
- LangGraph agent with 6+ tools executing in sequence
- RAG pipeline with ChromaDB vector store
- Real HTTP calls to MyScheme API and India.gov.in
- PyMuPDF + OCR document processing
- Multilingual: langdetect + gTTS + deep-translator

### AI Reasoning
- Intent classification before retrieval
- Source-grounded responses (not hallucinated)
- Claim verification step
- Structured eligibility analysis (deterministic where possible)

### Impact
- 180+ million farmers who can't navigate government portals
- First-generation students missing scholarship deadlines
- Women unaware of government health entitlements

### Compliance
- All scheme data from official APIs
- Source citations always shown
- AI explicitly states it's not a government authority
- No personal data stored beyond session

---

## FALLBACK IF SOMETHING GOES WRONG

| Issue | Fallback |
|-------|---------|
| Backend not running | Show `/docs` FastAPI auto-documentation |
| Government API down | Show error message explaining fallback behavior |
| Voice not working | Type the question, show "browser STT not supported" message |
| Slow response | "The agent is calling external government APIs — this shows it's live" |

---

## DEMO TIPS

1. **Don't apologize** if something is slow — it's calling real government APIs
2. **Do** mention "This is live data from MyScheme.gov.in" when showing schemes
3. **Do** show the agent steps panel — this impresses technical judges
4. **Do** change the language mid-demo to show multilingual capability
5. **Don't** click around randomly — follow this script

---

*Good luck! 🇮🇳 JanSahayak AI — Government policies made understandable to everyone.*
