"""Government Schemes API Endpoints.

Provides search and retrieval of official welfare schemes,
along with comprehensive listings of Indian states, UTs, and scheme sectors.
"""

from datetime import datetime, timezone
import logging
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Query, status

from app.models.schemas import (
    SchemeSearchRequest,
    SchemeSearchResponse,
    GovernmentScheme,
)
from app.services.government_sources import GovernmentSourceAggregator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/schemes", tags=["schemes"])
_gov_aggregator = GovernmentSourceAggregator()

# Comprehensive listing of 28 Indian States and 8 Union Territories
INDIAN_STATES = [
    {"name": "Andhra Pradesh", "code": "AP", "type": "State"},
    {"name": "Arunachal Pradesh", "code": "AR", "type": "State"},
    {"name": "Assam", "code": "AS", "type": "State"},
    {"name": "Bihar", "code": "BR", "type": "State"},
    {"name": "Chhattisgarh", "code": "CG", "type": "State"},
    {"name": "Goa", "code": "GA", "type": "State"},
    {"name": "Gujarat", "code": "GJ", "type": "State"},
    {"name": "Haryana", "code": "HR", "type": "State"},
    {"name": "Himachal Pradesh", "code": "HP", "type": "State"},
    {"name": "Jharkhand", "code": "JH", "type": "State"},
    {"name": "Karnataka", "code": "KA", "type": "State"},
    {"name": "Kerala", "code": "KL", "type": "State"},
    {"name": "Madhya Pradesh", "code": "MP", "type": "State"},
    {"name": "Maharashtra", "code": "MH", "type": "State"},
    {"name": "Manipur", "code": "MN", "type": "State"},
    {"name": "Meghalaya", "code": "ML", "type": "State"},
    {"name": "Mizoram", "code": "MZ", "type": "State"},
    {"name": "Nagaland", "code": "NL", "type": "State"},
    {"name": "Odisha", "code": "OD", "type": "State"},
    {"name": "Punjab", "code": "PB", "type": "State"},
    {"name": "Rajasthan", "code": "RJ", "type": "State"},
    {"name": "Sikkim", "code": "SK", "type": "State"},
    {"name": "Tamil Nadu", "code": "TN", "type": "State"},
    {"name": "Telangana", "code": "TG", "type": "State"},
    {"name": "Tripura", "code": "TR", "type": "State"},
    {"name": "Uttar Pradesh", "code": "UP", "type": "State"},
    {"name": "Uttarakhand", "code": "UK", "type": "State"},
    {"name": "West Bengal", "code": "WB", "type": "State"},
    # Union Territories
    {"name": "Andaman and Nicobar Islands", "code": "AN", "type": "Union Territory"},
    {"name": "Chandigarh", "code": "CH", "type": "Union Territory"},
    {"name": "Dadra and Nagar Haveli and Daman and Diu", "code": "DH", "type": "Union Territory"},
    {"name": "Delhi (NCT)", "code": "DL", "type": "Union Territory"},
    {"name": "Jammu and Kashmir", "code": "JK", "type": "Union Territory"},
    {"name": "Ladakh", "code": "LA", "type": "Union Territory"},
    {"name": "Lakshadweep", "code": "LD", "type": "Union Territory"},
    {"name": "Puducherry", "code": "PY", "type": "Union Territory"},
]

SCHEME_CATEGORIES = [
    {"id": "agriculture", "name": "Agriculture, Rural & Environment", "icon": "sprout"},
    {"id": "banking-finance", "name": "Banking, Financial Services and Insurance", "icon": "bank"},
    {"id": "business-entrepreneurship", "name": "Business & Entrepreneurship", "icon": "briefcase"},
    {"id": "education-learning", "name": "Education & Learning", "icon": "graduation-cap"},
    {"id": "health-wellness", "name": "Health & Wellness", "icon": "heart-pulse"},
    {"id": "housing-shelter", "name": "Housing & Shelter", "icon": "home"},
    {"id": "public-safety-law", "name": "Public Safety, Law & Justice", "icon": "shield"},
    {"id": "skills-employment", "name": "Skills & Employment", "icon": "wrench"},
    {"id": "social-welfare", "name": "Social Welfare & Empowerment", "icon": "users"},
    {"id": "transport-infrastructure", "name": "Transport & Infrastructure", "icon": "truck"},
    {"id": "utility-sanitation", "name": "Utility & Sanitation", "icon": "droplet"},
    {"id": "women-child", "name": "Women and Child Development", "icon": "baby"},
]


@router.post("/search", response_model=SchemeSearchResponse)
async def search_schemes(request: SchemeSearchRequest) -> SchemeSearchResponse:
    """Search government welfare schemes across official portals."""
    results = await _gov_aggregator.search_all(
        query=request.query or "",
        state=request.state or "",
        category=request.category or "",
        beneficiary_type=request.beneficiary_type or "",
    )

    schemes = results.get("schemes", [])
    failed = results.get("sources_failed", [])
    warning = f"Notice: Sources with connectivity issues: {', '.join(failed)}" if failed else None

    return SchemeSearchResponse(
        schemes=schemes,
        total=len(schemes),
        source="MyScheme / India.gov.in / National Registry",
        retrieved_at=results.get("retrieved_at", datetime.now(timezone.utc)),
        warning=warning,
    )


@router.get("/categories/list")
async def list_categories() -> Dict[str, Any]:
    """Retrieve all standard official scheme categories."""
    return {
        "categories": SCHEME_CATEGORIES,
        "total": len(SCHEME_CATEGORIES)
    }


@router.get("/states/list")
async def list_states() -> Dict[str, Any]:
    """Retrieve all Indian States and Union Territories with state codes."""
    return {
        "states": INDIAN_STATES,
        "total": len(INDIAN_STATES)
    }


@router.get("/{scheme_id}", response_model=GovernmentScheme)
async def get_scheme(scheme_id: str, source: str = "myscheme") -> GovernmentScheme:
    """Fetch complete details, criteria, benefits, and documents for a specific scheme."""
    scheme = await _gov_aggregator.fetch_scheme_details(scheme_id=scheme_id, source=source)
    if not scheme:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scheme with ID '{scheme_id}' was not found in official records."
        )
    return scheme
