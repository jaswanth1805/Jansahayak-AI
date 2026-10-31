"""Eligibility Assessment API Endpoints.

Provides automated citizen eligibility checks against central and state government schemes,
complete with ranking, checklist of required documents, and dynamic questionnaires.
"""

from datetime import datetime, timezone
import json
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query, status

from app.models.schemas import (
    EligibilityProfile,
    EligibilityResult,
    GovernmentScheme,
    SourceCitation,
)
from app.services.government_sources import GovernmentSourceAggregator
from app.services.llm_service import LLMService
from app.agents.tools import analyze_scheme_eligibility
from app.utils.language import translate_text

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/eligibility", tags=["eligibility"])
_gov_aggregator = GovernmentSourceAggregator()
_llm_service = LLMService()

# Priority rank ordering for results
STATUS_PRIORITY = {
    "likely_eligible": 1,
    "possibly_eligible": 2,
    "insufficient_info": 3,
    "not_eligible": 4,
}


@router.post("/check", response_model=List[EligibilityResult])
async def check_eligibility(
    profile: EligibilityProfile,
    scheme_query: str = Query(default="", description="Optional keyword to filter evaluated schemes"),
    language: str = Query(default="en", description="Target language code")
) -> List[EligibilityResult]:
    """Check citizen eligibility against welfare schemes based on submitted profile.
    
    Returns schemes ranked by match quality (eligible schemes first).
    """
    # 1. Search candidate schemes
    search_res = await _gov_aggregator.search_all(
        query=scheme_query,
        state=profile.state or "",
        beneficiary_type=profile.occupation or "",
    )
    schemes = search_res.get("schemes", [])

    if not schemes:
        # If no schemes matched query, fall back to all curated schemes
        schemes = _gov_aggregator.curated_schemes

    results: List[EligibilityResult] = []
    user_dict = profile.model_dump()

    # 2. Analyze eligibility for each scheme
    for scheme in schemes[:8]:
        scheme_dict = scheme.model_dump()
        analysis = await analyze_scheme_eligibility(scheme_data=scheme_dict, user_profile=user_dict)

        now = datetime.now(timezone.utc)
        citation = SourceCitation(
            title=scheme.name,
            url=scheme.official_url,
            source_type="official_api",
            page_number=None,
            section="Eligibility Criteria",
            retrieved_at=now,
            is_verified=True,
        )

        res_item = EligibilityResult(
            scheme=scheme,
            status=analysis["status"],
            satisfied_conditions=analysis["satisfied_conditions"],
            unsatisfied_conditions=analysis["unsatisfied_conditions"],
            missing_information=analysis["missing_information"],
            required_documents=analysis["required_documents"],
            application_steps=analysis["application_steps"],
            official_link=analysis["official_link"],
            disclaimer=analysis["disclaimer"],
            sources=[citation],
        )

        # Optional translation of criteria feedback if language != "en"
        if language in ("hi", "te"):
            res_item.satisfied_conditions = [translate_text(c, target_language=language) for c in res_item.satisfied_conditions]
            res_item.unsatisfied_conditions = [translate_text(c, target_language=language) for c in res_item.unsatisfied_conditions]
            res_item.missing_information = [translate_text(c, target_language=language) for c in res_item.missing_information]
            res_item.application_steps = [translate_text(s, target_language=language) for s in res_item.application_steps]
            res_item.disclaimer = translate_text(res_item.disclaimer, target_language=language)

        results.append(res_item)

    # 3. Sort results: likely_eligible first, followed by possibly_eligible
    results.sort(key=lambda r: STATUS_PRIORITY.get(r.status, 99))
    return results


@router.post("/questions")
async def get_eligibility_questions(
    scheme_id: str = Query(..., description="ID of the scheme to get questions for"),
    source: str = Query(default="myscheme", description="Source provider"),
    language: str = Query(default="en", description="Question language")
) -> Dict[str, Any]:
    """Generate dynamic questionnaire needed to assess citizen eligibility for a scheme."""
    scheme = await _gov_aggregator.fetch_scheme_details(scheme_id=scheme_id, source=source)
    if not scheme:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scheme '{scheme_id}' not found."
        )

    # Formulate questionnaire
    questions = []
    
    # 1. State question if state-specific
    if scheme.state:
        questions.append({
            "field": "state",
            "type": "select",
            "question": f"Are you a permanent resident of {scheme.state}?",
            "options": ["Yes", "No"],
            "required": True,
        })
    else:
        questions.append({
            "field": "state",
            "type": "text",
            "question": "Which Indian State or Union Territory do you currently reside in?",
            "required": False,
        })

    # 2. Age question
    crit_text = " ".join(scheme.eligibility_criteria).lower()
    if any(k in crit_text for k in ["age", "year old", "senior", "minor", "child"]):
        questions.append({
            "field": "age",
            "type": "number",
            "question": "What is your current age in completed years?",
            "required": True,
        })

    # 3. Occupation question
    if scheme.beneficiary_types:
        questions.append({
            "field": "occupation",
            "type": "select",
            "question": "What is your primary occupation?",
            "options": scheme.beneficiary_types + ["Other"],
            "required": True,
        })

    # 4. Income question
    if any(k in crit_text for k in ["income", "bpl", "deprivation", "annual"]):
        questions.append({
            "field": "annual_income",
            "type": "number",
            "question": "What is your total annual household income (in INR ₹)?",
            "required": True,
        })

    # 5. Landholding / Specific conditions
    if "land" in crit_text or "cultivable" in crit_text:
        questions.append({
            "field": "owns_land",
            "type": "boolean",
            "question": "Do you own cultivable agricultural land registered in your name?",
            "options": ["Yes", "No"],
            "required": True,
        })

    # Translate questions if language != "en"
    if language in ("hi", "te"):
        for q in questions:
            q["question"] = translate_text(q["question"], target_language=language)
            if "options" in q:
                q["options"] = [translate_text(opt, target_language=language) for opt in q["options"]]

    return {
        "scheme_id": scheme.id,
        "scheme_name": scheme.name,
        "questions": questions,
        "total_questions": len(questions),
    }
