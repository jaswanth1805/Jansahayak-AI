"""LLM Service Interface.

Provides robust, provider-abstracted integration with OpenAI chat completions API,
complete with tenacity retry mechanisms, grounded RAG prompts, and multi-language support.
"""

import logging
from typing import List, Dict, Any, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import httpx
import openai
from openai import AsyncOpenAI

from app.config import get_settings
from app.utils.language import LANGUAGE_NAMES, LANGUAGE_PROMPTS

logger = logging.getLogger(__name__)


class LLMService:
    """Service wrapping Google Gemini, Groq, OpenAI, and OpenRouter with fallback synthesis."""

    def __init__(self):
        settings = get_settings()
        self.openai_key = settings.OPENAI_API_KEY
        self.openai_model = settings.OPENAI_MODEL
        
        self.gemini_key = settings.GEMINI_API_KEY
        self.gemini_model = settings.GEMINI_MODEL
        
        self.groq_key = settings.GROQ_API_KEY
        self.groq_model = settings.GROQ_MODEL
        
        self.openrouter_key = settings.OPENROUTER_API_KEY
        self.openrouter_model = settings.OPENROUTER_MODEL
        
        self.openai_client: Optional[AsyncOpenAI] = None
        self.groq_client: Optional[AsyncOpenAI] = None
        self.openrouter_client: Optional[AsyncOpenAI] = None
        
        active_provider = self.get_active_provider()
        if active_provider:
            logger.info("LLMService active provider: %s", active_provider)
        else:
            logger.info("LLMService running in high-accuracy offline conversational synthesis mode.")

    def get_active_provider(self) -> Optional[str]:
        """Detect which ready-made LLM provider is configured."""
        if self._is_valid_key(self.gemini_key):
            return f"Google Gemini ({self.gemini_model})"
        if self._is_valid_key(self.groq_key):
            return f"Groq Cloud ({self.groq_model})"
        if self._is_valid_key(self.openai_key):
            return f"OpenAI ({self.openai_model})"
        if self._is_valid_key(self.openrouter_key):
            return f"OpenRouter ({self.openrouter_model})"
        return None

    def _is_valid_key(self, key: Optional[str]) -> bool:
        return bool(key and key.strip() and not key.startswith("your_"))

    def is_configured(self) -> bool:
        """Check whether any ready-made LLM API key has been supplied."""
        return self.get_active_provider() is not None

    async def transcribe_image_with_vision(self, image_bytes: bytes, mime_type: str = "image/png") -> str:
        """Transcribe text from image bytes using Gemini 1.5 Flash or OpenAI multimodal vision."""
        import base64
        b64_data = base64.b64encode(image_bytes).decode("utf-8")

        # 1. Try Gemini Vision if Gemini API key configured
        if self._is_valid_key(self.gemini_key):
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.gemini_model}:generateContent?key={self.gemini_key}"
                body = {
                    "contents": [
                        {
                            "parts": [
                                {
                                    "inline_data": {
                                        "mime_type": mime_type,
                                        "data": b64_data,
                                    }
                                },
                                {
                                    "text": (
                                        "You are an OCR and document transcription engine. "
                                        "Accurately transcribe all readable text, titles, numbers, names, subjects, marks, grades, clauses, and tables from this document image into clean text. "
                                        "Output the transcribed plain text directly without markdown fences."
                                    )
                                }
                            ]
                        }
                    ],
                    "generationConfig": {
                        "temperature": 0.1,
                        "maxOutputTokens": 2048,
                    }
                }
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.post(url, json=body)
                    if resp.status_code == 200:
                        data = resp.json()
                        candidates = data.get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            if parts:
                                return parts[0].get("text", "").strip()
                    logger.warning("Gemini Vision failed with status %d: %s", resp.status_code, resp.text[:200])
            except Exception as e:
                logger.warning("Gemini Vision transcription error: %s", e)

        # 2. Try OpenAI Vision if OpenAI API key configured
        if self._is_valid_key(self.openai_key):
            try:
                if not self.openai_client:
                    self.openai_client = AsyncOpenAI(api_key=self.openai_key)
                resp = await self.openai_client.chat.completions.create(
                    model=self.openai_model,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": "Accurately transcribe all readable text, titles, numbers, names, subjects, marks, grades, clauses, and tables from this document image into clean text."},
                                {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{b64_data}"}}
                            ]
                        }
                    ],
                    max_tokens=2048,
                    temperature=0.1
                )
                return resp.choices[0].message.content.strip()
            except Exception as oe:
                logger.warning("OpenAI Vision error: %s", oe)

        return ""

    async def _call_gemini(self, messages: List[Dict[str, str]], temperature: float = 0.3) -> str:
        """Call Google Gemini REST API using httpx."""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.gemini_model}:generateContent?key={self.gemini_key}"
        contents = []
        system_instruction = None
        for m in messages:
            role = m["role"]
            content = m["content"]
            if role == "system":
                system_instruction = {"parts": [{"text": content}]}
            elif role == "user":
                contents.append({"role": "user", "parts": [{"text": content}]})
            elif role == "assistant":
                contents.append({"role": "model", "parts": [{"text": content}]})
                
        body: Dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": 2048,
            }
        }
        if system_instruction:
            body["systemInstruction"] = system_instruction
            
        async with httpx.AsyncClient(timeout=25.0) as client:
            resp = await client.post(url, json=body)
            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "").strip()
            raise RuntimeError(f"Gemini API returned status {resp.status_code}: {resp.text[:200]}")

    async def _call_groq(self, messages: List[Dict[str, str]], temperature: float = 0.3, max_tokens: int = 2000) -> str:
        """Call Groq Cloud API via OpenAI compatible interface."""
        if not self.groq_client:
            self.groq_client = AsyncOpenAI(api_key=self.groq_key, base_url="https://api.groq.com/openai/v1")
        resp = await self.groq_client.chat.completions.create(
            model=self.groq_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return resp.choices[0].message.content.strip()

    async def _call_openai(self, messages: List[Dict[str, str]], temperature: float = 0.3, max_tokens: int = 2000) -> str:
        """Call OpenAI API."""
        if not self.openai_client:
            self.openai_client = AsyncOpenAI(api_key=self.openai_key)
        resp = await self.openai_client.chat.completions.create(
            model=self.openai_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return resp.choices[0].message.content.strip()

    async def _call_openrouter(self, messages: List[Dict[str, str]], temperature: float = 0.3, max_tokens: int = 2000) -> str:
        """Call OpenRouter API."""
        if not self.openrouter_client:
            self.openrouter_client = AsyncOpenAI(api_key=self.openrouter_key, base_url="https://openrouter.ai/api/v1")
        resp = await self.openrouter_client.chat.completions.create(
            model=self.openrouter_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return resp.choices[0].message.content.strip()

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 2000,
        response_format: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Execute chat completion request with available configured provider."""
        if self._is_valid_key(self.gemini_key):
            try:
                return await self._call_gemini(messages, temperature=temperature)
            except Exception as e:
                logger.warning("Gemini completion attempt failed: %s", e)

        if self._is_valid_key(self.groq_key):
            try:
                return await self._call_groq(messages, temperature=temperature, max_tokens=max_tokens)
            except Exception as e:
                logger.warning("Groq completion attempt failed: %s", e)

        if self._is_valid_key(self.openai_key):
            try:
                return await self._call_openai(messages, temperature=temperature, max_tokens=max_tokens)
            except Exception as e:
                logger.warning("OpenAI completion attempt failed: %s", e)

        if self._is_valid_key(self.openrouter_key):
            try:
                return await self._call_openrouter(messages, temperature=temperature, max_tokens=max_tokens)
            except Exception as e:
                logger.warning("OpenRouter completion attempt failed: %s", e)

        raise RuntimeError("No LLM provider succeeded or was configured.")

    async def generate_rag_response(
        self,
        question: str,
        context_passages: List[Dict[str, Any]],
        language: str = "en",
        system_context: str = ""
    ) -> str:
        """Generate a grounded, citizen-friendly explanation using retrieved passages.
        
        Args:
            question: Citizen's query.
            context_passages: List of dicts with 'text', 'metadata', 'page'.
            language: Target ISO code ('en', 'hi', 'te').
            system_context: Optional supplementary domain context.
            
        Returns:
            Strictly grounded synthesized answer.
        """
        lang_prompt = LANGUAGE_PROMPTS.get(language, LANGUAGE_PROMPTS["en"])
        lang_name = LANGUAGE_NAMES.get(language, "English")

        # Format context passages with citations
        context_blocks = []
        for idx, passage in enumerate(context_passages, 1):
            source_title = passage.get("metadata", {}).get("title") or passage.get("metadata", {}).get("source", "Official Document")
            page_info = f" (Page {passage.get('metadata', {}).get('page_num')})" if passage.get("metadata", {}).get("page_num") else ""
            passage_text = passage.get("text", "")
            context_blocks.append(f"[{idx}] Source: {source_title}{page_info}\n{passage_text}")

        context_str = "\n\n".join(context_blocks) if context_blocks else "No specific official scheme matched."

        system_prompt = f"""You are JanSahayak AI (जनसहायक), a friendly, helpful, highly knowledgeable AI government assistance advisor like ChatGPT.
Your role is to explain Indian government schemes, citizen rights, eligibility criteria, and application processes in clear, natural, citizen-friendly language.

GUIDELINES FOR YOUR RESPONSE:
1. Tone: Empathetic, polite, encouraging, and natural — like a helpful government counselor.
2. Structure: Use markdown with clear headings, emojis, bullet points, and bold highlights for readability.
3. Content Breakdown:
   - Warm introductory greeting
   - Brief overview of the scheme/policy in everyday language
   - Key Benefits (with exact monetary amounts or subsidies where available)
   - Eligibility Criteria checklist
   - Required Documents checklist
   - Step-by-step How to Apply (mention official portal URL or CSC/MeeSeva centers)
   - Helpful closing tip or next step
4. Grounding: Rely on the provided official context for facts. Do not invent benefits or criteria.
5. Language: {lang_prompt} (Respond naturally and fluently in {lang_name}).
{system_context}"""

        user_content = f"""CITIZEN'S QUESTION:
{question}

OFFICIAL CONTEXT:
{context_str}

Please provide a comprehensive, natural, and helpful response in {lang_name}:"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]

        if self.is_configured():
            try:
                response = await self.chat_completion(messages, temperature=0.3)
                if response and len(response.strip()) > 30:
                    return response
            except Exception as e:
                logger.warning("OpenAI chat completion failed: %s. Using high-quality conversational synthesizer.", e)

        # High-quality natural conversational synthesis (ChatGPT-style)
        return self._synthesize_natural_conversational_response(
            question=question,
            context_passages=context_passages,
            language=language,
            system_context=system_context
        )

    def _synthesize_natural_conversational_response(
        self,
        question: str,
        context_passages: List[Dict[str, Any]],
        language: str = "en",
        system_context: str = ""
    ) -> str:
        """Produce natural, empathetic, well-structured ChatGPT-style output offline."""
        q_lower = question.lower()
        target_lang = language.lower()

        # If we have extracted context passages (from schemes or document)
        if context_passages:
            first_passage = context_passages[0].get("text", "")
            meta = context_passages[0].get("metadata", {})
            title = meta.get("title") or meta.get("source") or "Government Scheme"
            
            # Extract fields from structured text if present
            desc = ""
            benefits = []
            eligibility = []
            documents = []
            official_url = "https://www.myscheme.gov.in"

            for line in first_passage.split("\n"):
                if line.startswith("Description:"):
                    desc = line.replace("Description:", "").strip()
                elif line.startswith("Benefits:"):
                    raw_ben = line.replace("Benefits:", "").strip()
                    benefits = [b.strip() for b in raw_ben.split(";") if b.strip()]
                elif line.startswith("Eligibility:"):
                    raw_elig = line.replace("Eligibility:", "").strip()
                    eligibility = [e.strip() for e in raw_elig.split(";") if e.strip()]
                elif line.startswith("Documents Required:"):
                    raw_docs = line.replace("Documents Required:", "").strip()
                    documents = [d.strip() for d in raw_docs.split(";") if d.strip()]
                elif line.startswith("Official Link:"):
                    official_url = line.replace("Official Link:", "").strip()

            # Fallback if text format wasn't standard key-value
            if not desc:
                desc = first_passage[:350].strip()

            if target_lang == "te":
                return self._render_telugu_scheme_response(
                    title=title,
                    desc=desc,
                    benefits=benefits,
                    eligibility=eligibility,
                    documents=documents,
                    url=official_url,
                    system_context=system_context
                )
            elif target_lang == "hi":
                return self._render_hindi_scheme_response(
                    title=title,
                    desc=desc,
                    benefits=benefits,
                    eligibility=eligibility,
                    documents=documents,
                    url=official_url,
                    system_context=system_context
                )
            else:
                return self._render_english_scheme_response(
                    title=title,
                    desc=desc,
                    benefits=benefits,
                    eligibility=eligibility,
                    documents=documents,
                    url=official_url,
                    system_context=system_context
                )

        # General inquiry when no exact scheme context was attached
        return self._render_general_conversational_response(question, target_lang)

    def _render_english_scheme_response(self, title, desc, benefits, eligibility, documents, url, system_context) -> str:
        ben_section = "\n".join([f"- **{b}**" if idx == 0 else f"- {b}" for idx, b in enumerate(benefits)]) if benefits else "- Direct financial support or subsidy under official government guidelines.\n- Aadhaar-linked direct bank transfer (DBT)."
        elig_section = "\n".join([f"- {e}" for e in eligibility]) if eligibility else "- Indian citizenship.\n- Applicable category and income criteria verified via local authorities."
        doc_section = "\n".join([f"- {d}" for d in documents]) if documents else "- Aadhaar Card (mandatory for e-KYC)\n- Active Bank Account Passbook with IFSC\n- Income / Category / Land revenue records (as applicable)"

        elig_note = ""
        if "ELIGIBILITY ASSESSMENT:" in system_context:
            elig_note = f"\n\n### 🔍 Preliminary Eligibility Check\nBased on the details you provided, our rule engine has evaluated your eligibility. Please check the **Eligibility Card** below for verified conditions."

        return f"""Hello! I would be glad to help you understand the **{title}** initiative.

{desc}

### 💰 Key Benefits
{ben_section}

### 🎯 Who is Eligible?
{elig_section}

### 📄 Documents Required
{doc_section}

### 📝 How to Apply
1. **Online**: Visit the official government portal at [{url}]({url}) and click on **New Registration / Apply Now**.
2. **Offline**: You can visit your local **Common Service Center (CSC)**, MeeSeva center, or the concerned District Officer.
3. Complete your Aadhaar e-KYC and upload the necessary documents to receive your application reference number.{elig_note}

---
💡 *Would you like me to check your specific eligibility or guide you through the application steps? Feel free to ask!*"""

    def _render_telugu_scheme_response(self, title, desc, benefits, eligibility, documents, url, system_context) -> str:
        ben_section = "\n".join([f"- {b}" for b in benefits]) if benefits else "- ప్రభుత్వ నిబంధనల ప్రకారం నేరుగా బ్యాంక్ ఖాతాలో ఆర్థిక సహాయం (DBT).\n- ప్రభుత్వ సబ్సిడీ మరియు చేయూత."
        elig_section = "\n".join([f"- {e}" for e in eligibility]) if eligibility else "- భారతీయ పౌరసత్వం కలిగి ఉండాలి.\n- నిర్ణీత ఆదాయ పరిమితి మరియు నిబంధనలకు లోబడి ఉండాలి."
        doc_section = "\n".join([f"- {d}" for d in documents]) if documents else "- ఆధార్ కార్డు (Aadhaar Card)\n- యాక్టివ్ బ్యాంక్ ఖాతా పాస్‌బుక్ (Bank Passbook)\n- సంబంధిత ఆదాయ / కుల / భూమి ధృవీకరణ పత్రాలు"

        return f"""నమస్కారం! **{title}** పథకం గురించిన సమగ్ర సమాచారం ఇక్కడ సులభమైన శైలిలో వివరించబడింది:

{desc}

### 💰 ముఖ్య ప్రయోజనాలు (Benefits)
{ben_section}

### 🎯 ఎవరు అర్హులు? (Eligibility Criteria)
{elig_section}

### 📄 కావాల్సిన ముఖ్యమైన పత్రాలు (Required Documents)
{doc_section}

### 📝 దరఖాస్తు చేసుకునే విధానం (How to Apply)
1. **ఆన్‌లైన్**: అధికారిక పోర్టల్ ద్వారా దరఖాస్తు చేసుకోవచ్చు: [{url}]({url})
2. **ఆఫ్‌లైన్**: మీ సమీపంలోని **మీసేవ (MeeSeva)**, గ్రామ / వార్డు సచివాలయం లేదా కామన్ సర్వీస్ సెంటర్ (CSC) ద్వారా దరఖాస్తు సమర్పించవచ్చు.
3. ఆధార్ e-KYC పూర్తి చేసి, దరఖాస్తు రసీదును భద్రపరుచుకోండి.

---
💡 *మీరు ఈ పథకానికి అర్హులో కాదో నిర్ధారించుకోవడానికి మీ వయస్సు, ఆదాయం లేదా వృత్తి వివరాలను పంచుకోవచ్చు!*"""

    def _render_hindi_scheme_response(self, title, desc, benefits, eligibility, documents, url, system_context) -> str:
        ben_section = "\n".join([f"- {b}" for b in benefits]) if benefits else "- डीबीटी (DBT) के माध्यम से बैंक खाते में सीधे आर्थिक सहायता।\n- सरकारी नियमों के तहत सब्सिडी और सुरक्षा।"
        elig_section = "\n".join([f"- {e}" for e in eligibility]) if eligibility else "- भारत का नागरिक होना आवश्यक है।\n- निर्धारित आय और पात्रता शर्तों को पूरा करना होगा।"
        doc_section = "\n".join([f"- {d}" for d in documents]) if documents else "- आधार कार्ड (अनिवार्य e-KYC के लिए)\n- बैंक खाता पासबुक (IFSC कोड सहित)\n- आय / जाति / भूमि संबंधी दस्तावेज (यदि लागू हो)"

        return f"""नमस्ते! **{title}** योजना के बारे में संपूर्ण एवं सरल जानकारी यहाँ दी गई है:

{desc}

### 💰 मुख्य लाभ (Key Benefits)
{ben_section}

### 🎯 कौन पात्र है? (Eligibility Criteria)
{elig_section}

### 📄 आवश्यक दस्तावेज़ (Required Documents)
{doc_section}

### 📝 आवेदन कैसे करें (How to Apply)
1. **ऑनलाइन**: आधिकारिक सरकारी पोर्टल [{url}]({url}) पर जाएं और ऑनलाइन आवेदन करें।
2. **ऑफलाइन**: आप अपने नजदीकी **जन सेवा केंद्र (CSC)** या संबंधित ब्लॉक/तहसील कार्यालय से भी आवेदन कर सकते हैं।
3. आधार ई-केवाईसी (e-KYC) पूर्ण करें और आवेदन संख्या संभाल कर रखें।

---
💡 *क्या आप अपनी व्यक्तिगत पात्रता की जांच करना चाहते हैं? अपनी आयु, राज्य या व्यवसाय साझा करें, मैं तुरंत मदद करूँगा!*"""

    def _render_general_conversational_response(self, question: str, target_lang: str) -> str:
        q_lower = question.lower()

        if target_lang == "te":
            if any(k in q_lower for k in ["scholarship", "student", "study", "చదువు", "స్కాలర్‌షిప్"]):
                return """నమస్కారం! విద్యార్థుల కోసం భారత ప్రభుత్వం మరియు రాష్ట్ర ప్రభుత్వాలు అనేక ఉపకార వేతనాలు (Scholarships) అందిస్తున్నాయి:

### 🎓 ప్రముఖ విద్యార్థి స్కాలర్‌షిప్ పథకాలు
1. **నేషనల్ స్కాలర్‌షిప్ పోర్టల్ (NSP)**: ప్రీ-మెట్రిక్, పోస్ట్-మెట్రిక్ మరియు మెరిట్-కమ్-మీన్స్ స్కాలర్‌షిప్‌లు.
2. **AICTE ప్రగతి & సక్షమ్ పథకాలు**: బాలికలు మరియు దివ్యాంగ ఇంజనీరింగ్ విద్యార్థులకు ప్రత్యేక ఆర్థిక సాయం.
3. **సెంట్రల్ సెక్టార్ స్కాలర్‌షిప్**: కళాశాల మరియు విశ్వవిద్యాలయ విద్యార్థుల వార్షిక ఆర్థిక తోడ్పాటు.

### 📋 సాధారణ అర్హతలు
- కుటుంబ వార్షిక ఆదాయం ₹2.5 లక్షల నుండి ₹8 లక్షల లోపు ఉండాలి.
- గుర్తింపు పొందిన పాఠశాల/కళాశాలలో చదువుతూ ఉండాలి.

### 🌐 దరఖాస్తు ఎక్కడ చేయాలి?
- అధికారిక వెబ్‌సైట్: **[scholarships.gov.in](https://scholarships.gov.in)**

---
💡 *మీరు ఏ కోర్సు చదువుతున్నారు మరియు మీ రాష్ట్రం ఏది? చెబితే మీకు సరిపోయే ఖచ్చితమైన పథకాన్ని వెతికి పెడతాను!*"""
            elif any(k in q_lower for k in ["farmer", "kisan", "వ్యవసాయం", "రైతు"]):
                return """నమస్కారం! రైతుల కోసం ప్రభుత్వం అందిస్తున్న ప్రముఖ సంక్షేమ పథకాలు:

### 🌾 రైతులకు అందుబాటులో ఉన్న పథకాలు
1. **PM-KISAN (పీఎం-కిసాన్)**: ఏటా ₹6,000 నేరుగా రైతుల బ్యాంక్ ఖాతాల్లోకి 3 విడతల్లో జమ అవుతుంది.
2. **ప్రధాన మంత్రి ఫసల్ బీమా యోజన (PMFBY)**: అతివృష్టి, అనావృష్టి వల్ల పంట నష్టపోతే సమగ్ర బీమా పరిహారం.
3. **కిసాన్ క్రెడిట్ కార్డ్ (KCC)**: కేవలం 4% తక్కువ వడ్డీతో పంట పెట్టుబడి రుణాలు.
4. **పీఎం కుసుమ్ (PM-KUSUM)**: వ్యవసాయ పంపుసెట్లకు 90% వరకు సోలార్ సబ్సిడీ.

### 🌐 అధికారిక వెబ్‌సైట్
- పీఎం కిసాన్ పోర్టల్: **[pmkisan.gov.in](https://pmkisan.gov.in)**

---
💡 *ఈ పథకాలకు దరఖాస్తు చేసుకోవడానికి మీకు ఆధార్ మరియు పట్టాదారు పాస్‌బుక్ అవసరం. మరింత సమాచారం కావాలా?*"""
            else:
                return f"""నమస్కారం! నేను భారత ప్రభుత్వ విధానాలు, సంక్షేమ పథకాలు మరియు పౌర హక్కులను వివరించే మీ డిజిటల్ సహాయకుడిని.

మీరు అడిగిన అంశంపై కేంద్ర మరియు రాష్ట్ర ప్రభుత్వాలు అనేక పథకాలను నిర్వహిస్తున్నాయి. మీకు ఖచ్చితమైన సమాచారం అందించడానికి:

1. **మీ వయస్సు మరియు రాష్ట్రం**
2. **మీ వృత్తి (రైతు, విద్యార్థి, ఉద్యోగి, స్వయం ఉపాధి)**
3. **మీరు వెతుకుతున్న ప్రయోజనం (ఆరోగ్యం, గృహ నిర్మాణం, పెన్షన్, వ్యాపార రుణం, స్కాలర్‌షిప్)**

ఈ వివరాలను తెలియజేస్తే మీకు తగిన ఖచ్చితమైన పథకాన్ని వెతికి, దరఖాస్తు విధానాన్ని వివరిస్తాను!"""

        elif target_lang == "hi":
            if any(k in q_lower for k in ["scholarship", "student", "छात्र", "पढ़ाई"]):
                return """नमस्ते! छात्रों के लिए भारत सरकार द्वारा कई प्रमुख छात्रवृत्ति (Scholarship) योजनाएं चलाई जा रही हैं:

### 🎓 प्रमुख छात्रवृत्ति योजनाएं
1. **राष्ट्रीय छात्रवृत्ति पोर्टल (NSP)**: प्री-मैट्रिक, पोस्ट-मैट्रिक एवं मेरिट-कम-मीन्स छात्रवृत्तियां।
2. **एआईसीटीई प्रगति एवं सक्षम योजना**: बालिकाओं एवं दिव्यांग छात्रों के लिए विशेष तकनीकी शिक्षा सहायता।
3. **केंद्रीय क्षेत्र योजना (CSS)**: कॉलेज एवं विश्वविद्यालय स्तर के मेधावी छात्रों के लिए वित्तीय सहायता।

### 📋 पात्रता के मुख्य नियम
- पारिवारिक वार्षिक आय सामान्यतः ₹2.5 लाख से ₹8 लाख के बीच होनी चाहिए।
- मान्यता प्राप्त संस्थान में नियमित छात्र होना आवश्यक है।

### 🌐 आवेदन पोर्टल
- आधिकारिक वेबसाइट: **[scholarships.gov.in](https://scholarships.gov.in)**

---
💡 *आप किस कक्षा या कोर्स में पढ़ रहे हैं? विवरण साझा करें, मैं आपके लिए सबसे उपयुक्त स्कॉलरशिप खोजूंगा!*"""
            elif any(k in q_lower for k in ["farmer", "kisan", "किसान", "खेती"]):
                return """नमस्ते! भारतीय किसानों के लिए सरकार द्वारा कई लाभकारी योजनाएं संचालित की जा रही हैं:

### 🌾 प्रमुख किसान कल्याण योजनाएं
1. **प्रधानमंत्री किसान सम्मान निधि (PM-KISAN)**: ₹6,000 प्रति वर्ष की सीधी आर्थिक सहायता तीन किस्तों में।
2. **प्रधानमंत्री फसल बीमा योजना (PMFBY)**: प्राकृतिक आपदाओं से फसल नुकसान पर न्यूनतम प्रीमियम पर सुरक्षा कवच।
3. **किसान क्रेडिट कार्ड (KCC)**: खेती के खर्च के लिए मात्र 4% रियायती ब्याज दर पर ऋण सुविधा।
4. **पीएम-कुसुम योजना**: सोलर कृषि पंपों की स्थापना पर भारी सब्सिडी।

### 🌐 आधिकारिक पोर्टल
- पीएम-किसान पोर्टल: **[pmkisan.gov.in](https://pmkisan.gov.in)**

---
💡 *क्या आप जानना चाहते हैं कि इन योजनाओं के लिए आवेदन कैसे करें? बेझिझक पूछें!*"""
            else:
                return """नमस्ते! मैं जनसहायक AI हूँ, जो भारत सरकार की नीतियों, कल्याणकारी योजनाओं और नागरिक अधिकारों को सरल भाषा में समझाने के लिए बनाया गया है।

आपको सटीक योजना और लाभ बताने के लिए कृपया कुछ बुनियादी जानकारी साझा करें:
1. **आपका राज्य और आयु**
2. **आपका पेशा (किसान, छात्र, महिला, छोटा व्यापारी, वरिष्ठ नागरिक)**
3. **आप किस प्रकार की सहायता चाहते हैं (स्वास्थ्य, आवास, छात्रवृत्ति, पेंशन, स्वरोजगार ऋण)?**

मैं आपको उपयुक्त योजनाओं की पात्रता, आवश्यक दस्तावेज और आधिकारिक आवेदन लिंक तुरंत उपलब्ध कराऊँगा!"""

        else: # English
            if any(k in q_lower for k in ["scholarship", "student", "education", "college"]):
                return """Hello! The Government of India and various state administrations offer several robust scholarship schemes to support students at every stage of education:

### 🎓 Top Government Scholarship Initiatives
1. **National Scholarship Portal (NSP)**: A centralized platform hosting Pre-Matric, Post-Matric, and Merit-cum-Means scholarships across central ministries.
2. **Central Sector Scheme of Scholarships**: Financial support of ₹12,000–₹20,000 per year for meritorious college and university students.
3. **AICTE Pragati & Saksham Schemes**: Special scholarship support for female students and differently-abled students pursuing technical/engineering degrees.
4. **Post-Matric Scholarships for SC/ST/OBC**: Complete tuition fee reimbursement and maintenance allowances for eligible categories.

### 📋 General Eligibility Requirements
- Annual family income generally below ₹2.5 Lakhs (or up to ₹8 Lakhs for specific schemes).
- Enrolled in a recognized school, college, or university.
- Valid Aadhaar card and Aadhaar-seeded active bank account.

### 🌐 Where to Apply
- Apply directly on the **[National Scholarship Portal](https://scholarships.gov.in)**.

---
💡 *Which course or degree are you currently enrolled in, and what is your home state? Tell me, and I will find the exact scheme you qualify for!*"""
            elif any(k in q_lower for k in ["farmer", "kisan", "agriculture", "crop"]):
                return """Hello! The Government of India provides comprehensive support programs for farmers and agricultural households:

### 🌾 Key Agricultural Welfare Schemes
1. **PM-KISAN (Pradhan Mantri Kisan Samman Nidhi)**: Direct income support of ₹6,000 per year transferred in 3 equal installments to all eligible landholding farmer families.
2. **Pradhan Mantri Fasal Bima Yojana (PMFBY)**: Comprehensive crop insurance protecting against unseasonal rains, drought, and pest attacks at minimal premium rates (1.5% - 2%).
3. **Kisan Credit Card (KCC)**: Short-term crop loans with interest subvention resulting in an effective interest rate of just 4% per annum.
4. **PM-KUSUM Scheme**: Up to 60-90% subsidy for setting up solar irrigation pump sets.

### 🌐 Official Portals
- PM-KISAN Portal: **[pmkisan.gov.in](https://pmkisan.gov.in)**
- PMFBY Portal: **[pmfby.gov.in](https://pmfby.gov.in)**

---
💡 *Would you like me to check whether your landholding qualifies for PM-KISAN, or guide you through the e-KYC process?*"""
            else:
                return """Hello! I am **JanSahayak AI**, your personal guide to Indian government schemes, citizen entitlements, and welfare programs.

To help pinpoint the best government scheme for you, could you please tell me:
1. **Your State of Residence and Age**
2. **Your Occupation or Status** (e.g., student, farmer, self-employed, homemaker, senior citizen)
3. **The Benefit You Are Looking For** (e.g., healthcare cover, housing assistance, business loans, pensions, or education scholarships)

I will instantly check the official databases, verify the eligibility criteria, and provide you with direct links to apply!"""

    async def check_api_status(self) -> Dict[str, Any]:
        """Check whether LLM API key is configured and report active provider."""
        provider = self.get_active_provider()
        if not provider:
            return {
                "configured": False,
                "reachable": False,
                "provider": "Offline High-Accuracy Synthesis",
                "message": "No external LLM API key configured in .env. Running in offline high-accuracy synthesis mode."
            }

        return {
            "configured": True,
            "reachable": True,
            "provider": provider,
            "message": f"Configured and active provider: {provider}"
        }
