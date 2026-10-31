"""JanSahayak Agent Tool Implementations.

Defines asynchronous, modular tools utilized by the LangGraph orchestrator
to retrieve official government sources, verify facts, analyze eligibility,
and perform multilingual translation and voice synthesis.
"""

import logging
from typing import Dict, Any, List, Optional
import httpx
from bs4 import BeautifulSoup

from app.models.schemas import GovernmentScheme, Language
from app.services.government_sources import GovernmentSourceAggregator
from app.services.llm_service import LLMService
from app.services.voice_service import VoiceService
from app.rag.embeddings import search_collection
from app.utils.language import translate_text

logger = logging.getLogger(__name__)

# Singletons for tool execution
_GOV_AGGREGATOR = GovernmentSourceAggregator()
_LLM_SERVICE = LLMService()
_VOICE_SERVICE = VoiceService()


async def search_official_sources(
    query: str,
    state: str = "",
    category: str = "",
    beneficiary_type: str = ""
) -> Dict[str, Any]:
    """Search official government sources (MyScheme, India.gov.in, Data.gov.in) for schemes.
    
    Args:
        query: Scheme name, keyword, or citizen requirement.
        state: Specific Indian State or Union Territory filter.
        category: Scheme sector (e.g. Agriculture, Healthcare, Education).
        beneficiary_type: Target demographic (e.g. Farmers, Women, Students).
        
    Returns:
        Dict with 'schemes', 'total', 'sources_queried', 'sources_failed'.
    """
    logger.info("Tool: search_official_sources called with query='%s', state='%s'", query, state)
    try:
        results = await _GOV_AGGREGATOR.search_all(
            query=query,
            state=state,
            category=category,
            beneficiary_type=beneficiary_type,
        )
        return {
            "success": True,
            "schemes": [s.model_dump() if hasattr(s, "model_dump") else s for s in results["schemes"]],
            "total": results["total"],
            "sources_queried": results["sources_queried"],
            "sources_failed": results["sources_failed"],
        }
    except Exception as e:
        logger.error("Tool search_official_sources failed: %s", e)
        return {
            "success": False,
            "schemes": [],
            "total": 0,
            "error": str(e),
        }


async def fetch_government_document(url: str) -> Dict[str, Any]:
    """Fetch and extract readable text from a government webpage or online document.
    
    Args:
        url: Direct HTTP/HTTPS link to official page or gazette.
        
    Returns:
        Dict containing title, extracted plain text snippet, and status.
    """
    logger.info("Tool: fetch_government_document fetching URL: %s", url)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) JanSahayak/1.0",
        "Accept": "text/html,application/xhtml+xml,application/pdf"
    }
    try:
        async with httpx.AsyncClient(timeout=10.0, headers=headers, follow_redirects=True) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                content_type = resp.headers.get("content-type", "")
                if "html" in content_type:
                    soup = BeautifulSoup(resp.text, "lxml")
                    # Remove script and style elements
                    for tag in soup(["script", "style", "nav", "footer"]):
                        tag.decompose()
                    text = " ".join(soup.get_text().split())
                    title = soup.title.string.strip() if soup.title else url
                    return {
                        "success": True,
                        "title": title,
                        "text": text[:3000],
                        "url": url
                    }
                else:
                    return {
                        "success": True,
                        "title": url.split("/")[-1],
                        "text": resp.text[:2000],
                        "url": url
                    }
            else:
                return {"success": False, "error": f"HTTP status {resp.status_code}", "url": url}
    except Exception as e:
        logger.warning("Tool fetch_government_document failed for %s: %s", url, e)
        return {"success": False, "error": str(e), "url": url}


async def retrieve_relevant_passages(
    query: str,
    document_id: Optional[str] = None,
    n_results: int = 5
) -> Dict[str, Any]:
    """Search the vector database for passages relevant to the query.
    
    Args:
        query: Citizen question or search string.
        document_id: Optional specific document collection ID.
        n_results: Max passages to return.
        
    Returns:
        Dict with list of matching text passages and confidence scores.
    """
    logger.info("Tool: retrieve_relevant_passages query='%s', document_id='%s'", query, document_id)
    target_col = document_id if document_id else "general_schemes"
    try:
        passages = search_collection(collection_name=target_col, query=query, n_results=n_results)
        return {
            "success": True,
            "passages": passages,
            "count": len(passages)
        }
    except Exception as e:
        logger.error("Tool retrieve_relevant_passages failed: %s", e)
        return {"success": False, "passages": [], "error": str(e)}


async def extract_document_content(document_id: str) -> Dict[str, Any]:
    """Retrieve indexed content of an uploaded document."""
    return await retrieve_relevant_passages(query="overview eligibility benefits rules", document_id=document_id, n_results=6)


async def analyze_scheme_eligibility(
    scheme_data: Dict[str, Any],
    user_profile: Dict[str, Any]
) -> Dict[str, Any]:
    """Deterministically check which eligibility criteria a user satisfies.
    
    Evaluates concrete fields (age, state, income, student, employment, gender)
    and uses LLM only for nuanced qualitative criteria.
    
    Returns structured eligibility assessment.
    """
    satisfied: List[str] = []
    unsatisfied: List[str] = []
    missing: List[str] = []

    criteria_list = scheme_data.get("eligibility_criteria", [])
    scheme_name = scheme_data.get("name", "the scheme")

    # 1. State check
    scheme_state = scheme_data.get("state")
    user_state = user_profile.get("state")
    if scheme_state:
        if user_state:
            if scheme_state.lower() in user_state.lower() or user_state.lower() in scheme_state.lower():
                satisfied.append(f"Resident of {scheme_state} (Matches your profile)")
            else:
                unsatisfied.append(f"Restricted to residents of {scheme_state} (Your state: {user_state})")
        else:
            missing.append(f"Requires residence in {scheme_state} (Please confirm your state of residence)")

    # 2. Age checks
    user_age = user_profile.get("age")
    scheme_desc_and_crit = " ".join(criteria_list) + " " + scheme_data.get("description", "")
    
    # Check for senior citizen criteria
    if "70" in scheme_desc_and_crit and ("senior" in scheme_desc_and_crit.lower() or "age" in scheme_desc_and_crit.lower()):
        if user_age is not None:
            if user_age >= 70:
                satisfied.append(f"Age criterion: 70+ years (Your age: {user_age})")
            else:
                unsatisfied.append(f"Age criterion: Must be 70 years or older (Your age: {user_age})")
        else:
            missing.append("Age (Required to verify if you are 70+ years)")

    # Check for general working age (18-40 e.g. APY or Vishwakarma)
    if "18 and 40" in scheme_desc_and_crit or "18-40" in scheme_desc_and_crit:
        if user_age is not None:
            if 18 <= user_age <= 40:
                satisfied.append(f"Age between 18 and 40 years (Your age: {user_age})")
            else:
                unsatisfied.append(f"Must be between 18 and 40 years old (Your age: {user_age})")
        else:
            missing.append("Age (Must be between 18 and 40 years)")
    elif "minimum age of 18" in scheme_desc_and_crit.lower() or "18 years" in scheme_desc_and_crit.lower():
        if user_age is not None:
            if user_age >= 18:
                satisfied.append(f"Minimum age 18 years (Your age: {user_age})")
            else:
                unsatisfied.append(f"Minimum age requirement is 18 years (Your age: {user_age})")
        else:
            missing.append("Age (Must be at least 18 years old)")

    # 3. Income check
    user_income = user_profile.get("annual_income")
    if "income" in scheme_desc_and_crit.lower() or "bpl" in scheme_desc_and_crit.lower():
        if user_income is not None:
            if user_income <= 250000:
                satisfied.append(f"Low-income / BPL eligibility (Reported income: ₹{user_income:,.0f}/year)")
            else:
                unsatisfied.append(f"Income threshold might be exceeded (Reported income: ₹{user_income:,.0f}/year)")
        else:
            missing.append("Annual household income (To verify low-income / BPL status)")

    # 4. Occupation / Beneficiary check
    user_occ = user_profile.get("occupation", "").lower()
    beneficiaries = [b.lower() for b in scheme_data.get("beneficiary_types", [])]
    if beneficiaries and user_occ:
        if any(user_occ in b or b in user_occ for b in beneficiaries):
            satisfied.append(f"Beneficiary category matched: {user_profile.get('occupation')}")
        else:
            missing.append(f"Targeted to {', '.join(scheme_data.get('beneficiary_types', []))} (Your occupation: {user_profile.get('occupation')})")

    # Determine status
    if unsatisfied:
        status = "not_eligible"
    elif missing and not satisfied:
        status = "insufficient_info"
    elif missing and satisfied:
        status = "possibly_eligible"
    else:
        status = "likely_eligible"

    # Default application steps and documents
    req_docs = scheme_data.get("required_documents", ["Aadhaar Card", "Bank Account Details", "Proof of Residence"])
    app_steps = [
        f"1. Visit the official portal: {scheme_data.get('official_url', 'myscheme.gov.in')}",
        "2. Complete online registration using Aadhaar and mobile OTP authentication.",
        f"3. Upload the required documents: {', '.join(req_docs[:3])}.",
        "4. Submit your application and keep the generated acknowledgment number for status tracking."
    ]

    return {
        "status": status,
        "satisfied_conditions": satisfied,
        "unsatisfied_conditions": unsatisfied,
        "missing_information": missing,
        "required_documents": req_docs,
        "application_steps": app_steps,
        "official_link": scheme_data.get("application_url") or scheme_data.get("official_url"),
        "disclaimer": (
            "This eligibility assessment is for guidance only. "
            "Sanction and approval are subject to official verification by the concerned department."
        ),
    }


async def translate_response(text: str, target_language: str) -> Dict[str, Any]:
    """Translate text response to target language using GoogleTranslator."""
    translated = translate_text(text=text, target_language=target_language)
    return {"original": text, "translated": translated, "language": target_language}


async def generate_voice_response(text: str, language: str) -> Dict[str, Any]:
    """Synthesize voice response in target language."""
    try:
        audio_url = await _VOICE_SERVICE.text_to_speech(text=text, language=language)
        return {"success": True, "audio_url": audio_url, "language": language}
    except Exception as e:
        logger.warning("Voice synthesis failed: %s", e)
        return {"success": False, "audio_url": None, "error": str(e)}


async def verify_source_and_citations(claims: List[str], sources: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Verify that specific claims are supported by the provided sources."""
    verified_claims = []
    unverified_claims = []

    source_text = " ".join([
        (s.get("description", "") + " " + " ".join(s.get("benefits", [])) + " " + " ".join(s.get("eligibility_criteria", [])))
        for s in sources
    ]).lower()

    for claim in claims:
        # Check keyword overlap
        words = [w.lower() for w in claim.split() if len(w) > 3]
        if words and sum(1 for w in words if w in source_text) >= len(words) * 0.4:
            verified_claims.append(claim)
        else:
            unverified_claims.append(claim)

    return {
        "verified_claims": verified_claims,
        "unverified_claims": unverified_claims,
        "confidence_score": round(len(verified_claims) / max(len(claims), 1), 2)
    }
