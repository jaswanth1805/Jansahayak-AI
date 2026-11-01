"""JanSahayak Agent Tool Implementations.

Defines asynchronous, modular tools utilized by the LangGraph orchestrator
to retrieve official government sources, verify facts, analyze eligibility,
and perform multilingual translation and voice synthesis.
"""

import logging
import re
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse
import httpx
from bs4 import BeautifulSoup
from starlette.concurrency import run_in_threadpool

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
    """Search MyScheme and India.gov.in, then compare the results with curated references.
    
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
    parsed_url = urlparse(url)
    host = (parsed_url.hostname or "").lower().rstrip(".")
    if parsed_url.scheme != "https" or not host.endswith(".gov.in"):
        return {"success": False, "error": "Only HTTPS pages on government .gov.in domains are allowed."}

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) JanSahayak/1.0",
        "Accept": "text/html,application/xhtml+xml"
    }
    try:
        async with httpx.AsyncClient(timeout=10.0, headers=headers, follow_redirects=False) as client:
            async with client.stream("GET", url) as resp:
                if resp.is_redirect:
                    return {"success": False, "error": "Redirects are not followed for source retrieval.", "url": url}
                if resp.status_code != 200:
                    return {"success": False, "error": f"HTTP status {resp.status_code}", "url": url}
                if "html" not in resp.headers.get("content-type", "").lower():
                    return {"success": False, "error": "The source did not return an HTML page.", "url": url}
                body = bytearray()
                async for chunk in resp.aiter_bytes():
                    body.extend(chunk)
                    if len(body) > 2 * 1024 * 1024:
                        return {"success": False, "error": "The source page exceeds the 2 MB retrieval limit.", "url": url}
                soup = BeautifulSoup(bytes(body), "lxml")
                for tag in soup(["script", "style", "nav", "footer"]):
                    tag.decompose()
                text = " ".join(soup.get_text().split())
                title = soup.title.get_text(strip=True) if soup.title else url
                return {"success": True, "title": title[:300], "text": text[:3000], "url": url}
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
        Dict with list of matching text passages and raw vector distances.
    """
    logger.info("Tool: retrieve_relevant_passages query='%s', document_id='%s'", query, document_id)
    target_col = document_id if document_id else "general_schemes"
    try:
        passages = await run_in_threadpool(
            search_collection,
            collection_name=target_col,
            query=query,
            n_results=n_results,
        )
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
    criteria_text = " ".join(criteria_list)
    criteria_lower = criteria_text.casefold()
    additional = user_profile.get("additional_info") or {}
    if not isinstance(additional, dict):
        additional = {}
    checked_criteria = 0

    scheme_state = scheme_data.get("state")
    user_state = user_profile.get("state")
    if scheme_state:
        checked_criteria += 1
        if not user_state:
            missing.append(f"State of residence (Scheme is restricted to {scheme_state})")
        elif " ".join(scheme_state.casefold().split()) == " ".join(user_state.casefold().split()):
            satisfied.append(f"Resident of {scheme_state}")
        else:
            unsatisfied.append(f"Restricted to residents of {scheme_state} (Your state: {user_state})")

    user_age = user_profile.get("age")
    if "70" in criteria_text and any(word in criteria_lower for word in ("senior", "age", "years")):
        checked_criteria += 1
        if user_age is None:
            missing.append("Age (Required to verify the 70+ years criterion)")
        elif user_age >= 70:
            satisfied.append(f"Age criterion met (reported age: {user_age})")
        else:
            unsatisfied.append(f"Must be 70 years or older (reported age: {user_age})")
    elif re.search(r"18\s*(?:-|to|and)\s*40", criteria_lower):
        checked_criteria += 1
        if user_age is None:
            missing.append("Age (Required to verify the 18–40 years criterion)")
        elif 18 <= user_age <= 40:
            satisfied.append(f"Age criterion met (reported age: {user_age})")
        else:
            unsatisfied.append(f"Must be between 18 and 40 years (reported age: {user_age})")
    elif "minimum age of 18" in criteria_lower:
        checked_criteria += 1
        if user_age is None:
            missing.append("Age (Required to verify the minimum age criterion)")
        elif user_age >= 18:
            satisfied.append(f"Minimum age criterion met (reported age: {user_age})")
        else:
            unsatisfied.append(f"Must be at least 18 years old (reported age: {user_age})")

    if "income" in criteria_lower or "bpl" in criteria_lower:
        checked_criteria += 1
        bpl_value = additional.get("is_bpl")
        if "bpl" in criteria_lower and isinstance(bpl_value, bool):
            if bpl_value:
                satisfied.append("BPL status was reported by the applicant; official certificate verification is still required")
            else:
                unsatisfied.append("The scheme's stated BPL condition is not met based on the supplied profile")
        amount_match = re.search(r"(?:₹|rs\.?\s*)\s*([\d,]+(?:\.\d+)?)\s*(lakh|lakhs|lac|crore)?", criteria_lower)
        lakh_match = re.search(r"([\d,.]+)\s*(?:lakh|lakhs|lac)\b", criteria_lower)
        threshold = None
        if amount_match:
            threshold = float(amount_match.group(1).replace(",", ""))
            if amount_match.group(2) in {"lakh", "lakhs", "lac"}:
                threshold *= 100_000
            elif amount_match.group(2) == "crore":
                threshold *= 10_000_000
        elif lakh_match:
            threshold = float(lakh_match.group(1).replace(",", "")) * 100_000
        if threshold is None and "bpl" in criteria_lower and isinstance(bpl_value, bool):
            pass
        elif threshold is None or not any(word in criteria_lower for word in ("below", "less than", "not exceed", "up to", "upto", "within", "maximum")):
            missing.append("The income threshold requires confirmation from the official scheme criteria")
        elif user_profile.get("annual_income") is None:
            missing.append(f"Annual household income (To verify the stated ₹{threshold:,.0f} limit)")
        elif user_profile["annual_income"] <= threshold:
            satisfied.append(f"Reported income is within the stated ₹{threshold:,.0f} limit")
        else:
            unsatisfied.append(f"Reported income exceeds the stated ₹{threshold:,.0f} limit")

    beneficiaries = scheme_data.get("beneficiary_types", [])
    if beneficiaries:
        checked_criteria += 1
        user_occ = (user_profile.get("occupation") or "").casefold().strip()
        if not user_occ:
            missing.append(f"Occupation or beneficiary category (Scheme lists: {', '.join(beneficiaries)})")
        elif any(user_occ in b.casefold() or b.casefold() in user_occ for b in beneficiaries):
            satisfied.append(f"Beneficiary category matched: {user_profile.get('occupation')}")
        else:
            unsatisfied.append(f"Occupation '{user_profile.get('occupation')}' does not match the listed beneficiary groups")

    if any(word in criteria_lower for word in ("student", "enrolled", "studying")):
        checked_criteria += 1
        student_status = user_profile.get("is_student")
        if student_status is None and (user_profile.get("occupation") or "").casefold() == "student":
            student_status = True
        if student_status is None:
            missing.append("Current school, college, or training enrollment status")
        elif student_status:
            satisfied.append("Current student status was reported; enrollment documents require verification")
        else:
            unsatisfied.append("The scheme requires current student or enrollment status")

    if any(word in criteria_lower for word in ("women", "woman", "female", "girl child")):
        checked_criteria += 1
        gender = (user_profile.get("gender") or "").casefold()
        if not gender or gender == "prefer not to say":
            missing.append("Gender or beneficiary-category information required by this scheme")
        elif gender in {"female", "woman", "girl"}:
            satisfied.append("Reported gender matches the stated women/girl beneficiary group")
        else:
            unsatisfied.append("The scheme is restricted to women/girl beneficiaries")

    if any(word in criteria_lower for word in ("landholding", "land holding", "cultivable land", "agricultural land")):
        checked_criteria += 1
        acres = additional.get("land_holding_acres")
        if acres is None:
            missing.append("Agricultural land ownership or landholding information")
        else:
            try:
                if float(acres) > 0:
                    satisfied.append("Reported agricultural landholding; ownership and scheme thresholds require official verification")
                else:
                    unsatisfied.append("No agricultural landholding was reported")
            except (TypeError, ValueError):
                missing.append("Valid agricultural landholding information")

    if any(word in criteria_lower for word in ("udyam", "msme registration", "business registration")):
        checked_criteria += 1
        registration = additional.get("has_business_reg")
        if not isinstance(registration, bool):
            missing.append("Current Udyam/MSME or business registration status")
        elif registration:
            satisfied.append("Business registration was reported; certificate verification is still required")
        else:
            unsatisfied.append("The scheme requires business registration")

    category_rules = {
        "scheduled caste": "sc",
        "scheduled tribe": "st",
        "sc/st": "sc/st",
        "obc": "obc",
    }
    required_categories = {category for keyword, category in category_rules.items() if keyword in criteria_lower}
    if required_categories:
        checked_criteria += 1
        user_category = (user_profile.get("category") or "").casefold().replace(" ", "")
        if not user_category:
            missing.append("Social-category information required by the scheme")
        elif "sc/st" in required_categories:
            if user_category in {"sc", "st", "scheduledcaste", "scheduledtribe"}:
                satisfied.append("Reported social category matches one of the scheme's listed groups")
            else:
                unsatisfied.append("The scheme is restricted to SC/ST beneficiaries")
        elif user_category not in required_categories:
            unsatisfied.append(f"Reported social category does not match the scheme's required group ({', '.join(sorted(required_categories))})")
        else:
            satisfied.append("Reported social category matches a listed group; certificate verification is required")

    if "unemployed" in criteria_lower or "not employed" in criteria_lower:
        checked_criteria += 1
        employment_status = user_profile.get("is_employed")
        if employment_status is None:
            missing.append("Current employment status")
        elif employment_status:
            unsatisfied.append("The scheme requires the applicant to be unemployed")
        else:
            satisfied.append("Reported employment status matches the stated unemployed group")

    if "disabil" in criteria_lower:
        checked_criteria += 1
        disability_status = additional.get("has_disability")
        if not isinstance(disability_status, bool):
            missing.append("Disability status and any required official certification")
        elif disability_status:
            satisfied.append("Disability was reported; official certification and any percentage threshold require verification")
        else:
            unsatisfied.append("The scheme requires a person with a disability")

    if not criteria_list:
        missing.append("No detailed eligibility criteria are available for this scheme")
    elif checked_criteria == 0:
        missing.append("The scheme's eligibility rules need review against the official criteria")
    elif not unsatisfied:
        missing.append("Confirm that all scheme-specific conditions are met with the responsible department")

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
    req_docs = scheme_data.get("required_documents", [])
    app_steps = [
        f"1. Review the current instructions at the official scheme page: {scheme_data.get('official_url', 'https://www.myscheme.gov.in')}.",
        "2. Confirm the current eligibility rules, required documents, and application process with the responsible department before applying.",
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
