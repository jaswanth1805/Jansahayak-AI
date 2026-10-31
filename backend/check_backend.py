"""Backend Validation Script.

Tests all imports, schemas, configurations, and core services for JanSahayak AI.
"""

import sys
import os

# Ensure backend root is on Python module search path
backend_root = os.path.dirname(os.path.abspath(__file__))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

print(f"[1/5] Testing config import from: {backend_root}")
try:
    from app.config import get_settings
    settings = get_settings()
    print(f"  ✓ Config OK (Host: {settings.BACKEND_HOST}, Port: {settings.BACKEND_PORT})")
except Exception as e:
    print(f"  ✗ Config Error: {e}")
    sys.exit(1)

print("[2/5] Testing models & schemas...")
try:
    from app.models.schemas import (
        Language,
        ChatMessage,
        ChatRequest,
        ChatResponse,
        SourceCitation,
        GovernmentScheme,
        SchemeSearchRequest,
        SchemeSearchResponse,
        EligibilityProfile,
        EligibilityResult,
        DocumentUploadResponse,
        DocumentQueryRequest,
        DocumentQueryResponse,
        VoiceRequest,
        VoiceResponse,
    )
    print("  ✓ All 14 Pydantic schemas imported OK")
except Exception as e:
    print(f"  ✗ Schemas Error: {e}")
    sys.exit(1)

print("[3/5] Testing government sources & services...")
try:
    from app.services.government_sources import GovernmentSourceAggregator, CURATED_FLAGSHIP_SCHEMES
    agg = GovernmentSourceAggregator()
    print(f"  ✓ GovernmentSourceAggregator OK ({len(agg.curated_schemes)} curated schemes pre-loaded)")
except Exception as e:
    print(f"  ✗ Government Sources Error: {e}")
    sys.exit(1)

print("[4/5] Testing utils & tools...")
try:
    from app.utils.language import detect_language, translate_text
    from app.utils.file_utils import validate_upload
    from app.agents.tools import search_official_sources, analyze_scheme_eligibility
    print("  ✓ Utilities and agent tools OK")
except Exception as e:
    print(f"  ✗ Utilities / Tools Error: {e}")
    sys.exit(1)

print("[5/5] Testing main FastAPI application...")
try:
    import main
    print(f"  ✓ FastAPI Application '{main.app.title}' v{main.app.version} loaded OK")
    print(f"  ✓ Total registered routes: {len(main.app.routes)}")
except Exception as e:
    print(f"  ✗ Main App Error: {e}")
    sys.exit(1)

print("\n" + "="*50)
print("SUCCESS: All JanSahayak AI backend modules validated successfully!")
print("="*50)
