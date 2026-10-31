"""End-to-End Test Suite for JanSahayak AI.

Tests all major endpoints:
1. Health check
2. Scheme search (real queries)
3. Categories and States list
4. Eligibility assessment (deterministic logic)
5. Voice synthesis (English, Hindi, Telugu)
6. PDF upload, extraction, and Q&A
7. Chat assistant with LangGraph workflow
"""

import sys
import io
import json
import urllib.request
import urllib.error

sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://localhost:8000"
passed = 0
failed = 0

def test(name, fn):
    global passed, failed
    print(f"\n[TEST] {name}...")
    try:
        fn()
        print(f"  --> PASSED")
        passed += 1
    except Exception as e:
        print(f"  --> FAILED: {e}")
        failed += 1

def test_health():
    with urllib.request.urlopen(f"{BASE_URL}/health") as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode('utf-8'))
        assert data.get("status") == "healthy"

def test_states_and_categories():
    with urllib.request.urlopen(f"{BASE_URL}/api/schemes/states/list") as resp:
        states = json.loads(resp.read().decode('utf-8'))["states"]
        assert len(states) >= 36
        assert any(s.get("name") == "Andhra Pradesh" for s in states)
        assert any(s.get("name") == "Telangana" for s in states)
    
    with urllib.request.urlopen(f"{BASE_URL}/api/schemes/categories/list") as resp:
        cats = json.loads(resp.read().decode('utf-8'))["categories"]
        assert len(cats) >= 5
        assert any("Agriculture" in c.get("name", "") for c in cats)

def test_scheme_search():
    body = json.dumps({"query": "kisan", "language": "en"}).encode('utf-8')
    req = urllib.request.Request(
        f"{BASE_URL}/api/schemes/search",
        data=body,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        assert data["total"] > 0
        assert any("kisan" in s["name"].lower() for s in data["schemes"])

def test_eligibility_check():
    profile = {
        "age": 45,
        "occupation": "farmer",
        "annual_income": 80000,
        "state": "Andhra Pradesh"
    }
    body = json.dumps(profile).encode('utf-8')
    req = urllib.request.Request(
        f"{BASE_URL}/api/eligibility/check?scheme_query=kisan&language=en",
        data=body,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        results = json.loads(resp.read().decode('utf-8'))
        assert len(results) > 0
        assert results[0]["status"] in ("likely_eligible", "possibly_eligible")

def test_voice_synthesis():
    for lang, sample in [("en", "Welcome to JanSahayak"), ("hi", "नमस्ते"), ("te", "నమస్కారం")]:
        body = json.dumps({"text": sample, "language": lang}).encode('utf-8')
        req = urllib.request.Request(
            f"{BASE_URL}/api/voice/synthesize",
            data=body,
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            assert "audio_url" in data
            # Check audio file is downloadable
            with urllib.request.urlopen(f"{BASE_URL}{data['audio_url']}") as a_resp:
                assert a_resp.status == 200
                assert len(a_resp.read()) > 1000

def test_pdf_upload_and_rag():
    import fitz
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 72), "MINISTRY OF RURAL DEVELOPMENT: Guidelines for Rural Employment Guarantee 2026. Minimum 100 days of wage employment per financial year.", fontsize=12)
    pdf_bytes = doc.write()
    doc.close()
    
    boundary = "----TestBoundary12345"
    parts = [
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"mgnregs_test.pdf\"\r\nContent-Type: application/pdf\r\n\r\n".encode('utf-8'),
        pdf_bytes,
        f"\r\n--{boundary}--\r\n".encode('utf-8')
    ]
    body = b"".join(parts)
    req = urllib.request.Request(
        f"{BASE_URL}/api/documents/upload",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}
    )
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode('utf-8'))
        assert res["page_count"] == 1
        assert "document_id" in res
        doc_id = res["document_id"]
        
        # Query the document
        q_body = json.dumps({
            "document_id": doc_id,
            "question": "How many days of wage employment are guaranteed?",
            "language": "en"
        }).encode('utf-8')
        q_req = urllib.request.Request(
            f"{BASE_URL}/api/documents/query",
            data=q_body,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(q_req) as q_resp:
            q_res = json.loads(q_resp.read().decode('utf-8'))
            assert "answer" in q_res

def test_chat_agent():
    body = json.dumps({
        "message": "What is PM Awas Yojana?",
        "language": "en",
        "conversation_history": []
    }).encode('utf-8')
    req = urllib.request.Request(
        f"{BASE_URL}/api/chat/",
        data=body,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode('utf-8'))
        assert "answer" in res
        assert "agent_steps" in res
        assert len(res["agent_steps"]) > 0

if __name__ == "__main__":
    print("=" * 60)
    print("  JANSAHAYAK AI - AUTOMATED VERIFICATION TEST SUITE  ")
    print("=" * 60)
    
    test("1. Backend Health Check", test_health)
    test("2. States & Categories API", test_states_and_categories)
    test("3. Government Scheme Search", test_scheme_search)
    test("4. Eligibility Assessment Engine", test_eligibility_check)
    test("5. Voice Synthesis (EN, HI, TE)", test_voice_synthesis)
    test("6. PDF Upload & Document RAG", test_pdf_upload_and_rag)
    test("7. LangGraph Chat Agent Workflow", test_chat_agent)
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} PASSED, {failed} FAILED (Total: {passed + failed})")
    print("=" * 60)
    sys.exit(0 if failed == 0 else 1)
