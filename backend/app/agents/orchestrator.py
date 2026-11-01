"""LangGraph Orchestrator for JanSahayak AI.

Implements an intelligent, multi-step agent workflow with intent classification,
official source retrieval, eligibility evaluation, claim verification,
multilingual synthesis, and follow-up generation.
"""

from datetime import datetime, timezone
import json
import logging
import operator
import re
from typing import TypedDict, List, Dict, Any, Optional, Annotated

from langgraph.graph import StateGraph, END

from app.models.schemas import SourceCitation, Language
from app.services.llm_service import LLMService
from app.services.government_sources import GovernmentSourceAggregator
from app.services.document_service import DocumentService
from app.services.voice_service import VoiceService
from app.agents.tools import (
    search_official_sources,
    retrieve_relevant_passages,
    analyze_scheme_eligibility,
)
from app.utils.language import LANGUAGE_PROMPTS, LANGUAGE_NAMES, translate_text

logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    """LangGraph State dictionary maintained across all pipeline nodes."""
    # User Inputs
    user_message: str
    language: str
    user_profile: Optional[Dict[str, Any]]
    document_id: Optional[str]
    conversation_history: List[Dict[str, str]]
    include_audio: bool
    session_id: str

    # Internal pipeline state
    intent: Optional[str]  # "scheme_query", "rights_query", "eligibility_check", "document_query", "general"
    retrieved_schemes: List[Dict[str, Any]]
    retrieved_passages: List[Dict[str, Any]]
    eligibility_results: Optional[Dict[str, Any]]
    agent_steps: Annotated[List[str], operator.add]

    # Outputs
    final_answer: Optional[str]
    sources: List[Dict[str, Any]]
    audio_url: Optional[str]
    suggested_questions: List[str]
    error: Optional[str]


class JanSahayakOrchestrator:
    """Production LangGraph orchestrator executing citizen queries."""

    def __init__(
        self,
        llm_service: LLMService,
        gov_sources: GovernmentSourceAggregator,
        doc_service: DocumentService,
        voice_service: VoiceService,
    ):
        self.llm = llm_service
        self.gov_sources = gov_sources
        self.doc_service = doc_service
        self.voice_service = voice_service
        self.graph = self._build_graph()
        self.app = self.graph.compile()

    def _build_graph(self) -> StateGraph:
        """Construct the directed state workflow."""
        workflow = StateGraph(AgentState)

        # Register workflow nodes
        workflow.add_node("classify_intent", self._node_classify_intent)
        workflow.add_node("retrieve_document_passages", self._node_retrieve_document_passages)
        workflow.add_node("retrieve_official_schemes", self._node_retrieve_official_schemes)
        workflow.add_node("extract_relevant_info", self._node_extract_relevant_info)
        workflow.add_node("evaluate_eligibility", self._node_evaluate_eligibility)
        workflow.add_node("verify_claims", self._node_verify_claims)
        workflow.add_node("generate_response", self._node_generate_response)
        workflow.add_node("generate_suggestions", self._node_generate_suggestions)
        workflow.add_node("synthesize_audio", self._node_synthesize_audio)

        # Set entry point
        workflow.set_entry_point("classify_intent")

        # Routing from intent classifier
        def route_after_intent(state: AgentState) -> str:
            if state.get("document_id") or state.get("intent") == "document_query":
                return "retrieve_document_passages"
            return "retrieve_official_schemes"

        workflow.add_conditional_edges(
            "classify_intent",
            route_after_intent,
            {
                "retrieve_document_passages": "retrieve_document_passages",
                "retrieve_official_schemes": "retrieve_official_schemes",
            }
        )

        # Both retrieval branches feed into extraction
        workflow.add_edge("retrieve_document_passages", "extract_relevant_info")
        workflow.add_edge("retrieve_official_schemes", "extract_relevant_info")

        # After extraction, check whether eligibility analysis is required
        def route_after_extraction(state: AgentState) -> str:
            if state.get("user_profile") or state.get("intent") == "eligibility_check":
                return "evaluate_eligibility"
            return "verify_claims"

        workflow.add_conditional_edges(
            "extract_relevant_info",
            route_after_extraction,
            {
                "evaluate_eligibility": "evaluate_eligibility",
                "verify_claims": "verify_claims",
            }
        )

        workflow.add_edge("evaluate_eligibility", "verify_claims")
        workflow.add_edge("verify_claims", "generate_response")
        workflow.add_edge("generate_response", "generate_suggestions")

        # Route after suggestions: voice synthesis if requested, else END
        def route_after_suggestions(state: AgentState) -> str:
            if state.get("include_audio"):
                return "synthesize_audio"
            return END

        workflow.add_conditional_edges(
            "generate_suggestions",
            route_after_suggestions,
            {
                "synthesize_audio": "synthesize_audio",
                END: END,
            }
        )

        workflow.add_edge("synthesize_audio", END)

        return workflow

    # ==================== NODE IMPLEMENTATIONS ====================

    async def _node_classify_intent(self, state: AgentState) -> Dict[str, Any]:
        """Classify user intent into one of five structured pathways."""
        msg = state["user_message"].lower()
        document_id = state.get("document_id")

        if document_id:
            intent = "document_query"
        elif any(k in msg for k in ["eligible", "qualify", "can i apply", "am i eligible", "eligibility", "criteria", "पात्र", "అర్హత"]):
            intent = "eligibility_check"
        elif any(k in msg for k in ["scheme", "yojana", "pension", "kisan", "awas", "ayushman", "subsidy", "loan", "योजना", "పథకం"]):
            intent = "scheme_query"
        elif any(k in msg for k in ["right", "law", "entitlement", "grievance", "complaint", "act", "rti", "अधिकार", "హక్కు"]):
            intent = "rights_query"
        else:
            intent = "general"

        step_desc = f"Identified query intent as: '{intent}'."
        return {
            "intent": intent,
            "agent_steps": [step_desc],
        }

    async def _node_retrieve_document_passages(self, state: AgentState) -> Dict[str, Any]:
        """Retrieve passages from an indexed document collection."""
        doc_id = state.get("document_id", "")
        query = state["user_message"]
        res = await retrieve_relevant_passages(query=query, document_id=doc_id, n_results=4)
        passages = res.get("passages", [])
        
        step_desc = f"Retrieved {len(passages)} passages from uploaded document."
        return {
            "retrieved_passages": passages,
            "retrieved_schemes": [],
            "agent_steps": [step_desc],
        }

    async def _node_retrieve_official_schemes(self, state: AgentState) -> Dict[str, Any]:
        """Query MyScheme and India.gov.in alongside the curated reference registry."""
        query = state["user_message"]
        state_filter = state.get("user_profile", {}).get("state", "") if state.get("user_profile") else ""
        previous_user_query = next((
            str(turn.get("content", ""))[:1000]
            for turn in reversed(state.get("conversation_history", []))
            if turn.get("role") == "user" and isinstance(turn.get("content"), str)
        ), "")
        follow_up_markers = (" it", " this", " that", " its", " they", " those", "what about", "how about")
        is_follow_up = len(query.split()) <= 8 or any(marker in f" {query.casefold()}" for marker in follow_up_markers)
        contextual_query = f"{previous_user_query} {query}"[-2000:] if is_follow_up and previous_user_query else query

        res = await search_official_sources(query=contextual_query, state=state_filter)
        schemes = res.get("schemes", [])
        
        step_desc = f"Searched official government portals (MyScheme, India.gov.in); retrieved {len(schemes)} relevant schemes."
        return {
            "retrieved_schemes": schemes,
            "retrieved_passages": [],
            "agent_steps": [step_desc],
        }

    async def _node_extract_relevant_info(self, state: AgentState) -> Dict[str, Any]:
        """Extract and consolidate key facts from retrieved schemes or document passages."""
        sources: List[Dict[str, Any]] = []
        now = datetime.now(timezone.utc)

        # Format sources from retrieved schemes
        for scheme in state.get("retrieved_schemes", [])[:4]:
            sources.append({
                "title": scheme.get("name", "Government Scheme"),
                "url": scheme.get("official_url") or scheme.get("application_url"),
                "source_type": "official_api" if scheme.get("last_verified") else "curated_reference",
                "page_number": None,
                "section": scheme.get("category"),
                "retrieved_at": scheme.get("last_verified"),
                "is_verified": bool(scheme.get("last_verified")),
            })

        # Format sources from document passages
        for p in state.get("retrieved_passages", []):
            meta = p.get("metadata", {})
            sources.append({
                "title": f"Document: {meta.get('filename', 'Guidelines')} (Page {meta.get('page_num', 1)})",
                "url": None,
                "source_type": "uploaded_document",
                "page_number": meta.get("page_num"),
                "section": f"Page {meta.get('page_num')}",
                "retrieved_at": now,
                "is_verified": False,
            })

        step_desc = f"Collected {len(sources)} source references."
        return {
            "sources": sources,
            "agent_steps": [step_desc],
        }

    async def _node_evaluate_eligibility(self, state: AgentState) -> Dict[str, Any]:
        """Evaluate citizen eligibility against the retrieved scheme."""
        schemes = state.get("retrieved_schemes", [])
        profile = state.get("user_profile") or {}

        if state.get("intent") == "eligibility_check" and not profile:
            step_desc = "Eligibility was not assessed because no citizen profile was provided."
            return {"eligibility_results": None, "agent_steps": [step_desc]}
        
        if not schemes:
            step_desc = "Eligibility check skipped: No matching scheme found to evaluate against."
            return {"eligibility_results": None, "agent_steps": [step_desc]}

        primary_scheme = schemes[0]
        eval_res = await analyze_scheme_eligibility(scheme_data=primary_scheme, user_profile=profile)
        eval_res["scheme_name"] = primary_scheme.get("name")
        
        step_desc = f"Evaluated eligibility for '{primary_scheme.get('name')}': Result = {eval_res['status']}."
        return {
            "eligibility_results": eval_res,
            "agent_steps": [step_desc],
        }

    async def _node_verify_claims(self, state: AgentState) -> Dict[str, Any]:
        """Record the source-limitation notice; no independent claim verifier exists."""
        step_desc = "Prepared the response from retrieved records; confirm scheme details with the responsible department."
        return {
            "agent_steps": [step_desc],
        }

    async def _node_generate_response(self, state: AgentState) -> Dict[str, Any]:
        """Synthesize the final citizen explanation in the target language."""
        lang_code = state.get("language", "en")
        schemes = state.get("retrieved_schemes", [])
        passages = state.get("retrieved_passages", [])
        eligibility = state.get("eligibility_results")

        if state.get("intent") == "eligibility_check" and not state.get("user_profile"):
            if lang_code == "hi":
                answer = "सिर्फ़ प्रश्न के आधार पर पात्रता का आकलन नहीं किया जा सकता। कृपया उम्र, राज्य, व्यवसाय, आय और योजना से जुड़ी आवश्यक जानकारी दें, या पात्रता जाँच पृष्ठ का उपयोग करें। मैं बिना जानकारी के पात्रता का अनुमान नहीं लगाऊँगा।"
            elif lang_code == "te":
                answer = "ప్రశ్న ఒక్కటితో అర్హతను అంచనా వేయలేను. దయచేసి వయస్సు, రాష్ట్రం, వృత్తి, ఆదాయం మరియు పథకానికి అవసరమైన వివరాలు ఇవ్వండి లేదా అర్హత తనిఖీ పేజీని ఉపయోగించండి. సమాచారం లేకుండా అర్హతను ఊహించను."
            else:
                answer = "I can’t assess eligibility from a question alone. Please share the relevant details, such as age, state, occupation, income and scheme-specific information, or use the Eligibility Checker. I won’t assume an eligibility result without that information."
            return {
                "final_answer": answer,
                "agent_steps": ["Asked for profile information before assessing eligibility."],
            }

        # Case 1: Document Query
        if passages:
            answer = await self.llm.generate_rag_response(
                question=state["user_message"],
                context_passages=passages,
                language=lang_code,
                system_context="Answer citizen's question strictly from the uploaded guidelines. Include page citations.",
                conversation_history=state.get("conversation_history", []),
            )
            step_desc = f"Generated answer grounded in document passages in {LANGUAGE_NAMES.get(lang_code, 'English')}."
            return {"final_answer": answer, "agent_steps": [step_desc]}

        # Case 2: Scheme or Eligibility Query
        if schemes:
            # Build context from top schemes
            context_blocks = []
            for s in schemes[:3]:
                crit_str = "; ".join(s.get("eligibility_criteria", []))
                ben_str = "; ".join(s.get("benefits", []))
                docs_str = "; ".join(s.get("required_documents", []))
                
                # Pick localized name if requested
                disp_name = s.get("name", "Government Scheme")
                if lang_code == "te" and s.get("name_telugu"):
                    disp_name = s.get("name_telugu")
                elif lang_code == "hi" and s.get("name_hindi"):
                    disp_name = s.get("name_hindi")

                context_blocks.append({
                    "text": (
                        f"Scheme: {disp_name}\n"
                        f"Ministry: {s.get('ministry', 'Government of India')}\n"
                        f"Description: {s.get('description')}\n"
                        f"Benefits: {ben_str}\n"
                        f"Eligibility: {crit_str}\n"
                        f"Documents Required: {docs_str}\n"
                        f"Official Link: {s.get('official_url')}"
                    ),
                    "metadata": {
                        "source": s.get("source", "unknown"),
                        "title": disp_name,
                        "source_type": "official_api" if s.get("last_verified") else "curated_reference",
                        "retrieved_at": s.get("last_verified"),
                    }
                })

            extra_note = ""
            if eligibility:
                extra_note = (
                    f"\nELIGIBILITY ASSESSMENT:\nStatus: {eligibility.get('status')}\n"
                    f"Satisfied: {', '.join(eligibility.get('satisfied_conditions', []))}\n"
                    f"Missing Details: {', '.join(eligibility.get('missing_information', []))}"
                )

            answer = await self.llm.generate_rag_response(
                question=state["user_message"],
                context_passages=context_blocks,
                language=lang_code,
                system_context=f"Explain the scheme clearly. If eligibility was checked, include the result in clear simple language.{extra_note}",
                conversation_history=state.get("conversation_history", []),
            )
            step_desc = f"Generated a scheme explanation from the retrieved records in {LANGUAGE_NAMES.get(lang_code, 'English')}."
            return {"final_answer": answer, "agent_steps": [step_desc]}

        # Case 3: General or No Specific Scheme Found
        answer = await self.llm.generate_rag_response(
            question=state["user_message"],
            context_passages=[],
            language=lang_code,
            system_context="Provide helpful, empathetic, conversational public-welfare guidance in India for this citizen inquiry.",
            conversation_history=state.get("conversation_history", []),
        )
        step_desc = f"Generated conversational public-welfare guidance in {LANGUAGE_NAMES.get(lang_code, 'English')}."
        return {"final_answer": answer, "agent_steps": [step_desc]}

    async def _node_generate_suggestions(self, state: AgentState) -> Dict[str, Any]:
        """Generate 3 contextual follow-up questions for the citizen in target language."""
        schemes = state.get("retrieved_schemes", [])
        lang_code = state.get("language", "en")

        if lang_code == "te":
            if schemes:
                first_scheme = schemes[0].get("name_telugu") or schemes[0].get("name", "ఈ పథకం")
                suggestions = [
                    f"{first_scheme}కు దరఖాస్తు చేసుకోవడానికి ఏ పత్రాలు కావాలి?",
                    "ఆన్‌లైన్ లేదా మీసేవ కేంద్రంలో ఎలా దరఖాస్తు చేయాలి?",
                    "నేను అర్హుడినో కాదో ఎలా తెలుసుకోవాలి?",
                ]
            elif state.get("document_id"):
                suggestions = [
                    "ఈ పత్రంలో పేర్కొన్న దరఖాస్తు గడువు తేదీ ఏమిటి?",
                    "అర్హత నిబంధనలు ఏమిటి?",
                    "సంబంధిత అధికారి లేదా హెల్ప్‌లైన్ నంబర్ ఏమిటి?",
                ]
            else:
                suggestions = [
                    "రైతులకు ఏ సంక్షేమ పథకాలు అందుబాటులో ఉన్నాయి?",
                    "ఆరోగ్యశ్రీ / ఆయుష్మాన్ భారత్ ద్వారా ఎంత లబ్ధి చేకూరుతుంది?",
                    "ఉచిత ఇళ్ల పథకానికి (PMAY) ఎవరు అర్హులు?",
                ]
        elif lang_code == "hi":
            if schemes:
                first_scheme = schemes[0].get("name_hindi") or schemes[0].get("name", "इस योजना")
                suggestions = [
                    f"{first_scheme} के लिए कौन से दस्तावेज़ आवश्यक हैं?",
                    "ऑनलाइन या जन सेवा केंद्र (CSC) से कैसे आवेदन करें?",
                    "क्या मैं इस योजना के लिए पात्र हूँ?",
                ]
            elif state.get("document_id"):
                suggestions = [
                    "इस दस्तावेज़ में आवेदन की अंतिम तिथि क्या है?",
                    "मुख्य पात्रता शर्तें क्या हैं?",
                    "नोडल अधिकारी या हेल्पलाइन नंबर क्या है?",
                ]
            else:
                suggestions = [
                    "किसानों के लिए कौन सी कल्याणकारी योजनाएं हैं?",
                    "आयुष्मान भारत कार्ड कैसे बनवाएं?",
                    "पीएम आवास योजना के लिए आवेदन कैसे करें?",
                ]
        else:
            if schemes:
                first_scheme = schemes[0].get("name", "this scheme")
                suggestions = [
                    f"What documents do I need to apply for {first_scheme}?",
                    "How can I apply online or at a CSC center?",
                    "What other schemes can I qualify for?",
                ]
            elif state.get("document_id"):
                suggestions = [
                    "What is the application deadline mentioned in this document?",
                    "What penalties or terms are specified?",
                    "Who is the nodal officer or authority?",
                ]
            else:
                suggestions = [
                    "What schemes are available for small farmers?",
                    "Tell me about senior citizen health benefits.",
                    "How do I apply for housing assistance?",
                ]

        return {"suggested_questions": suggestions, "agent_steps": ["Generated contextual follow-up questions."]}

    async def _node_synthesize_audio(self, state: AgentState) -> Dict[str, Any]:
        """Generate MP3 audio for voice accessibility."""
        answer = state.get("final_answer", "")
        lang_code = state.get("language", "en")
        try:
            audio_url = await self.voice_service.text_to_speech(text=answer, language=lang_code)
            return {"audio_url": audio_url, "agent_steps": ["Synthesized multilingual voice response."]}
        except Exception as e:
            logger.warning("Voice synthesis step failed: %s", e)
            return {"audio_url": None, "agent_steps": [f"Voice synthesis skipped: {str(e)}"]}

    # ==================== MAIN EXECUTION ====================

    async def run(
        self,
        message: str,
        language: str = "en",
        user_profile: Optional[Dict[str, Any]] = None,
        document_id: Optional[str] = None,
        conversation_history: List[Dict[str, str]] = None,
        include_audio: bool = False,
        session_id: str = "default_session"
    ) -> Dict[str, Any]:
        """Execute the LangGraph orchestrator pipeline and return final results."""
        initial_state: AgentState = {
            "user_message": message,
            "language": language,
            "user_profile": user_profile,
            "document_id": document_id,
            "conversation_history": conversation_history or [],
            "include_audio": include_audio,
            "session_id": session_id,
            "intent": None,
            "retrieved_schemes": [],
            "retrieved_passages": [],
            "eligibility_results": None,
            "agent_steps": ["Received citizen inquiry."],
            "final_answer": None,
            "sources": [],
            "audio_url": None,
            "suggested_questions": [],
            "error": None,
        }

        try:
            final_state = await self.app.ainvoke(initial_state)
            return {
                "answer": final_state.get("final_answer", "No response generated."),
                "language": Language(final_state.get("language", "en")),
                "sources": [SourceCitation(**s) for s in final_state.get("sources", [])],
                "agent_steps": final_state.get("agent_steps", []),
                "has_audio": bool(final_state.get("audio_url")),
                "audio_url": final_state.get("audio_url"),
                "suggested_questions": final_state.get("suggested_questions", []),
                "eligibility_data": final_state.get("eligibility_results"),
                "session_id": session_id,
            }
        except Exception as err:
            logger.exception("Orchestrator pipeline failed: %s", err)
            fallback_answers = {
                "en": "I couldn’t complete that request because of a service error. Please retry shortly. For current scheme details, check the responsible department’s official portal.",
                "hi": "सेवा में समस्या के कारण आपका अनुरोध पूरा नहीं हो सका। कृपया थोड़ी देर बाद फिर प्रयास करें। वर्तमान जानकारी के लिए संबंधित विभाग के आधिकारिक पोर्टल पर जाँच करें।",
                "te": "సేవలో సమస్య కారణంగా మీ అభ్యర్థనను పూర్తి చేయలేకపోయాను. దయచేసి కొద్దిసేపటి తర్వాత మళ్లీ ప్రయత్నించండి. ప్రస్తుత సమాచారం కోసం సంబంధిత శాఖ అధికారిక పోర్టల్‌ను చూడండి.",
            }
            fallback_answer = fallback_answers.get(language, fallback_answers["en"])
            return {
                "answer": fallback_answer,
                "language": Language(language),
                "sources": [],
                "agent_steps": ["Pipeline encountered an unexpected error."],
                "has_audio": False,
                "audio_url": None,
                "suggested_questions": [],
                "eligibility_data": None,
                "session_id": session_id,
            }
