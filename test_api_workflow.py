#!/usr/bin/env python3
"""
Comprehensive API Workflow Testing Script
Tests all endpoints in the correct order for a full application lifecycle.

Roles needed:
- chercheur (researcher): Creates and submits applications
- assistant_dpgr (assistant): Manages sessions
- admin_dpgr (admin): CS deliberation decisions
"""

import httpx
import json
import asyncio
from pathlib import Path
from datetime import date, timedelta
from uuid import UUID

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
UPLOAD_DIR = "uploads/test_documents"

# Test credentials - 3 roles
RESEARCHER_EMAIL = "researcher@test.com"
RESEARCHER_PASSWORD = "test"
RESEARCHER_USERNAME = "researcher_user"
RESEARCHER_LASTNAME = "TestLastname"

ASSISTANT_EMAIL = "assistant@test.com"
ASSISTANT_PASSWORD = "test"
ASSISTANT_USERNAME = "assistant_user"
ASSISTANT_LASTNAME = "AssistantLastname"

ADMIN_EMAIL = "admin@test.com"
ADMIN_PASSWORD = "test"
ADMIN_USERNAME = "admin_user"
ADMIN_LASTNAME = "AdminLastname"

# Stored IDs
researcher_token = None
assistant_token = None
admin_token = None
session_id = None
application_id = None
document_id = None

passed = 0
failed = 0
errors = []


def report(step, success, detail=""):
    global passed, failed, errors
    status = "✓" if success else "✗"
    print(f"  {status} {step}")
    if detail:
        print(f"    → {detail}")
    if success:
        passed += 1
    else:
        failed += 1
        errors.append(f"{step}: {detail}")


# ============================================================================
# HELPERS
# ============================================================================

async def api(client, method, path, token=None, json_data=None, files=None, data=None, params=None, expect_status=None):
    """Generic API call helper"""
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    kwargs = {"headers": headers}
    if json_data is not None:
        kwargs["json"] = json_data
    if files is not None:
        kwargs["files"] = files
    if data is not None:
        kwargs["data"] = data
    if params is not None:
        kwargs["params"] = params
    
    url = f"{BASE_URL}{path}"
    response = await getattr(client, method)(url, **kwargs)
    
    if expect_status and response.status_code != expect_status:
        return None, response.status_code, response.text
    
    if response.status_code >= 400:
        return None, response.status_code, response.text
    
    try:
        return response.json(), response.status_code, None
    except Exception:
        return response.content, response.status_code, None


# ============================================================================
# MAIN WORKFLOW
# ============================================================================

async def main():
    global researcher_token, assistant_token, admin_token
    global session_id, application_id, document_id

    print("=" * 80)
    print("COMPREHENSIVE API WORKFLOW TEST")
    print("=" * 80)

    async with httpx.AsyncClient(timeout=30) as client:

        # =====================================================================
        # PHASE 1: HEALTH CHECK
        # =====================================================================
        print(f"\n{'='*60}")
        print("PHASE 1: HEALTH CHECK")
        print(f"{'='*60}")

        result, status, err = await api(client, "get", "/health")
        report("GET /health", status == 200, f"status={status}")

        # =====================================================================
        # PHASE 2: USER REGISTRATION & LOGIN
        # =====================================================================
        print(f"\n{'='*60}")
        print("PHASE 2: USER REGISTRATION & LOGIN")
        print(f"{'='*60}")

        # Register researcher (chercheur)
        result, status, err = await api(client, "post", "/auth/register", json_data={
            "email": RESEARCHER_EMAIL, "username": RESEARCHER_USERNAME,
            "lastname": RESEARCHER_LASTNAME, "password": RESEARCHER_PASSWORD,
            "role": "chercheur", "grade": "professeur", "anciente": 5,
            "laboratory_name": "AI Lab", "ancientee": 0
        })
        report("POST /auth/register (researcher)", status in [200, 201], f"status={status}")

        # Register assistant (assistant_dpgr) - manages sessions
        result, status, err = await api(client, "post", "/auth/register", json_data={
            "email": ASSISTANT_EMAIL, "username": ASSISTANT_USERNAME,
            "lastname": ASSISTANT_LASTNAME, "password": ASSISTANT_PASSWORD,
            "role": "assistant_dpgr", "grade": "professeur", "anciente": 10,
            "laboratory_name": "Admin Office", "ancientee": 0
        })
        report("POST /auth/register (assistant)", status in [200, 201], f"status={status}")

        # Register admin (admin_dpgr) - CS deliberation
        result, status, err = await api(client, "post", "/auth/register", json_data={
            "email": ADMIN_EMAIL, "username": ADMIN_USERNAME,
            "lastname": ADMIN_LASTNAME, "password": ADMIN_PASSWORD,
            "role": "admin_dpgr", "grade": "professeur", "anciente": 15,
            "laboratory_name": "Admin Office", "ancientee": 0
        })
        report("POST /auth/register (admin_dpgr)", status in [200, 201], f"status={status}")

        # Login researcher
        result, status, err = await api(client, "post", "/auth/login", json_data={
            "email": RESEARCHER_EMAIL, "password": RESEARCHER_PASSWORD
        })
        if result:
            researcher_token = result.get("access_token")
        else:
            print(f"DEBUG: No result for researcher login. Status: {status}, Error: {err}")
        print(f"DEBUG: researcher_token: {researcher_token}")
        report("POST /auth/login (researcher)", researcher_token is not None, f"status={status}")

        # Login assistant
        result, status, err = await api(client, "post", "/auth/login", json_data={
            "email": ASSISTANT_EMAIL, "password": ASSISTANT_PASSWORD
        })
        if result:
            assistant_token = result.get("access_token")
        report("POST /auth/login (assistant)", assistant_token is not None, f"status={status}")

        # Login admin
        result, status, err = await api(client, "post", "/auth/login", json_data={
            "email": ADMIN_EMAIL, "password": ADMIN_PASSWORD
        })
        if result:
            admin_token = result.get("access_token")
        report("POST /auth/login (admin)", admin_token is not None, f"status={status}")

        if not researcher_token or not assistant_token or not admin_token:
            print("\n✗ FATAL: Authentication failed. Cannot continue.")
            return

        # =====================================================================
        # PHASE 3: SESSION MANAGEMENT (assistant role)
        # =====================================================================
        print(f"\n{'='*60}")
        print("PHASE 3: SESSION MANAGEMENT (assistant_dpgr)")
        print(f"{'='*60}")

        # Check for active session first
        result, status, err = await api(client, "get", "/sessions/active")
        if status == 200 and result:
            session_id = result.get("id")
            report("GET /sessions/active", True, f"Found existing session: {session_id}")
        else:
            # Create session (assistant role)
            tomorrow = date.today()
            end_date = tomorrow + timedelta(days=120)
            result, status, err = await api(client, "post", "/sessions/", token=assistant_token, json_data={
                "name": "2025-2026 Academic Year",
                "academic_year": "2025-2026",
                "start_date": str(tomorrow),
                "end_date": str(end_date)
            })
            if result:
                session_id = result.get("id")
            report("POST /sessions/ (create)", session_id is not None, f"status={status}, err={err}")

        if not session_id:
            print("\n✗ FATAL: No session available. Cannot continue.")
            return

        # List sessions
        result, status, err = await api(client, "get", "/sessions/", token=assistant_token)
        report("GET /sessions/ (list)", status == 200, f"status={status}, count={len(result) if result else 0}")

        # Get session by ID
        result, status, err = await api(client, "get", f"/sessions/{session_id}", token=assistant_token)
        report(f"GET /sessions/{{id}}", status == 200, f"status={status}")

        # =====================================================================
        # PHASE 4: APPLICATION CREATION (researcher role)
        # =====================================================================
        print(f"\n{'='*60}")
        print("PHASE 4: APPLICATION CREATION (chercheur)")
        print(f"{'='*60}")

        # Create draft application
        tomorrow = date.today() + timedelta(days=1)
        next_month = tomorrow + timedelta(days=6)  # 7 days for professeur séjour
        result, status, err = await api(client, "post", "/applications/", token=researcher_token, json_data={
            "destination_country": "france",
            "destination_city": "Paris",
            "host_institution": "University of Paris",
            "scientific_objective": "Research on AI and machine learning",
            "start_date": str(tomorrow),
            "end_date": str(next_month),
        })
        if result:
            application_id = result.get("id")
        report("POST /applications/ (create draft)", application_id is not None, f"status={status}, err={err}")

        if not application_id:
            print("\n✗ FATAL: Application creation failed. Cannot continue.")
            return

        # Get current application
        result, status, err = await api(client, "get", "/applications/current", token=researcher_token)
        report("GET /applications/current", status == 200, f"status={status}, err={err}")

        # Get application by ID
        result, status, err = await api(client, "get", f"/applications/{application_id}", token=researcher_token)
        report(f"GET /applications/{{id}}", status == 200, f"status={status}")

        # List applications
        result, status, err = await api(client, "get", "/applications/", token=researcher_token)
        report("GET /applications/ (list)", status == 200 and isinstance(result, list), f"status={status}, count={len(result) if result else 0}")

        # Update draft
        result, status, err = await api(client, "patch", f"/applications/{application_id}", token=researcher_token, json_data={
            "destination_country": "france",
            "destination_city": "Lyon",
            "host_institution": "Claude Bernard University",
            "scientific_objective": "Advanced research on distributed systems and AI",
        })
        report(f"PATCH /applications/{{id}} (update)", status == 200, f"status={status}, err={err}")

        # =====================================================================
        # PHASE 5: DOCUMENT MANAGEMENT (researcher role)
        # =====================================================================
        print(f"\n{'='*60}")
        print("PHASE 5: DOCUMENT MANAGEMENT (chercheur)")
        print(f"{'='*60}")

        # Create test document files
        Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
        test_file = Path(UPLOAD_DIR) / "test_cv.pdf"
        test_file.write_text("This is a test CV document.")

        # Upload CV
        with open(test_file, "rb") as f:
            result, status, err = await api(client, "post",
                f"/applications/{application_id}/documents",
                token=researcher_token,
                files={"file": ("test_cv.pdf", f, "application/pdf")},
                data={"document_type": "cv"}
            )
        if result:
            document_id = result.get("id")
        report("POST /applications/{id}/documents (upload CV)", document_id is not None, f"status={status}, err={err}")

        # Upload more required docs
        doc_types = ["invitation", "programme", "passport", "accord_labo"]
        for doc_type in doc_types:
            test_file_doc = Path(UPLOAD_DIR) / f"test_{doc_type}.pdf"
            test_file_doc.write_text(f"This is a test {doc_type} document.")
            with open(test_file_doc, "rb") as f:
                result, status, err = await api(client, "post",
                    f"/applications/{application_id}/documents",
                    token=researcher_token,
                    files={"file": (f"test_{doc_type}.pdf", f, "application/pdf")},
                    data={"document_type": doc_type}
                )
            report(f"POST /applications/{{id}}/documents (upload {doc_type})", status in [200, 201], f"status={status}")

        # Get documents for application
        result, status, err = await api(client, "get", f"/applications/{application_id}/documents", token=researcher_token)
        report("GET /applications/{id}/documents (list)", status == 200, f"status={status}, count={len(result) if result else 0}")

        # Get single document
        if document_id:
            result, status, err = await api(client, "get", f"/document/{document_id}", token=researcher_token)
            report("GET /document/{id} (single)", status == 200, f"status={status}")

            # Download single document
            result, status, err = await api(client, "get", f"/document/{document_id}/download", token=researcher_token)
            report("GET /document/{id}/download", status == 200, f"status={status}")

        # Download all documents as ZIP
        result, status, err = await api(client, "get", f"/applications/{application_id}/documents/downloads", token=researcher_token)
        report("GET /applications/{id}/documents/downloads (ZIP)", status == 200, f"status={status}, err={err}")

        # =====================================================================
        # PHASE 6: ELIGIBILITY CHECK (researcher role)
        # =====================================================================
        print(f"\n{'='*60}")
        print("PHASE 6: ELIGIBILITY CHECK (chercheur)")
        print(f"{'='*60}")

        result, status, err = await api(client, "get", f"/applications/{application_id}/eligibility-details", token=researcher_token)
        report("GET /applications/{id}/eligibility-details", status == 200, f"status={status}, err={err}")

        # =====================================================================
        # PHASE 7: APPLICATION SUBMISSION (researcher role)
        # =====================================================================
        print(f"\n{'='*60}")
        print("PHASE 7: APPLICATION SUBMISSION (chercheur)")
        print(f"{'='*60}")

        result, status, err = await api(client, "post", f"/applications/{application_id}/submit", token=researcher_token, json_data={
            "destination_country": "france",
            "destination_city": "Lyon",
            "host_institution": "Claude Bernard University",
            "scientific_objective": "Advanced research on distributed systems and AI",
            "host_supervisor": "Dr. Laurent",
            "supervisor_email": "laurent@univ-lyon.fr",
            "host_department": "Computer Science",
            "title_of_stay": "Distributed AI Study",
            "research_axis": "Distributed Systems",
            "expected_outcomes": "Publication and collaboration roadmap",
        })
        report("POST /applications/{id}/submit", status == 200, f"status={status}, err={err}")
        if result:
            print(f"    → Eligibility: {result.get('eligibility_status')}")
            print(f"    → Errors: {result.get('verification_errors')}")

        # =====================================================================
        # PHASE 8: HISTORY & TRACKING (researcher role)
        # =====================================================================
        print(f"\n{'='*60}")
        print("PHASE 8: HISTORY & TRACKING (chercheur)")
        print(f"{'='*60}")

        # Application-specific history
        result, status, err = await api(client, "get", f"/applications/{application_id}/history",
            token=researcher_token, params={"limit": 50, "offset": 0})
        report("GET /applications/{id}/history", status == 200, f"status={status}, err={err}")

        # History page (all applications)
        result, status, err = await api(client, "get", "/applications/history",
            token=researcher_token, params={"limit": 10, "offset": 0, "sort_by": "submitted_at", "sort_order": "desc", "session_filter": "this"})
        report("GET /applications/history (page)", status == 200, f"status={status}, err={err}")

        # =====================================================================
        # PHASE 9: CS DELIBERATION (admin_dpgr role)
        # =====================================================================
        print(f"\n{'='*60}")
        print("PHASE 9: CS DELIBERATION (admin_dpgr)")
        print(f"{'='*60}")

        # CS approve application
        result, status, err = await api(client, "post", f"/cs/deliberate/{application_id}", token=admin_token, json_data={
            "decision": "approved",
            "notes": "Excellent candidate, approved by CS"
        })
        report("POST /cs/deliberate/{id} (approve)", status == 200, f"status={status}, err={err}")

        # Verify application status changed
        result, status, err = await api(client, "get", f"/applications/{application_id}", token=researcher_token)
        app_status = result.get("status") if result else None
        cs_decision = result.get("cs_decision") if result else None
        report("GET /applications/{id} (verify approval)", app_status == "approved", f"status={app_status}, cs_decision={cs_decision}")

        # =====================================================================
        # PHASE 10: NOTIFICATIONS (researcher role)
        # =====================================================================
        print(f"\n{'='*60}")
        print("PHASE 10: NOTIFICATIONS (chercheur)")
        print(f"{'='*60}")

        # Get notifications
        result, status, err = await api(client, "get", "/notifications/", token=researcher_token)
        notif_count = len(result) if result else 0
        report("GET /notifications/ (list)", status == 200, f"status={status}, count={notif_count}")

        # Count unread
        result, status, err = await api(client, "get", "/notifications/count-unread", token=researcher_token)
        report("GET /notifications/count-unread", status == 200, f"status={status}, result={result}")

        # Mark all as read
        result, status, err = await api(client, "patch", "/notifications/mark-all-as-read", token=researcher_token)
        report("PATCH /notifications/mark-all-as-read", status == 200, f"status={status}")

        # =====================================================================
        # PHASE 11: DASHBOARD (all roles)
        # =====================================================================
        print(f"\n{'='*60}")
        print("PHASE 11: DASHBOARD")
        print(f"{'='*60}")

        # Researcher dashboard
        result, status, err = await api(client, "get", "/dashboard/researcher", token=researcher_token)
        report("GET /dashboard/researcher", status == 200, f"status={status}, err={err}")

        # Researcher current application (dashboard)
        result, status, err = await api(client, "get", "/dashboard/researcher/current-application", token=researcher_token)
        report("GET /dashboard/researcher/current-application", status == 200, f"status={status}, err={err}")

        # Admin dashboard
        result, status, err = await api(client, "get", "/dashboard/admin", token=admin_token)
        report("GET /dashboard/admin", status == 200, f"status={status}, err={err}")

        # CS dashboard
        result, status, err = await api(client, "get", "/dashboard/cs", token=admin_token)
        report("GET /dashboard/cs", status == 200, f"status={status}, err={err}")

        # Statistics
        result, status, err = await api(client, "get", "/dashboard/statistics")
        report("GET /dashboard/statistics", status == 200, f"status={status}, err={err}")

        # =====================================================================
        # PHASE 12: INDEMNITY/ZONES
        # =====================================================================
        print(f"\n{'='*60}")
        print("PHASE 12: INDEMNITY / ZONES")
        print(f"{'='*60}")

        # Get zones (researcher can view)
        result, status, err = await api(client, "get", "/idemnity/zones", token=researcher_token)
        report("GET /idemnity/zones", status == 200, f"status={status}, count={len(result) if result else 0}")

        # =====================================================================
        # PHASE 13: CANCELLATION FLOW (researcher role)
        # =====================================================================
        print(f"\n{'='*60}")
        print("PHASE 13: CANCELLATION FLOW (chercheur)")
        print(f"{'='*60}")

        # Cancel the approved application
        result, status, err = await api(client, "post", f"/applications/{application_id}/cancel", token=researcher_token, json_data={
            "reason": "Changed plans due to scheduling conflict"
        })
        report("POST /applications/{id}/cancel", status == 200, f"status={status}, err={err}")

        # PHASE 14: CANCELLATION CONFIRMATION (admin role)
        print(f"\n{'='*60}")
        print("PHASE 14: CANCELLATION CONFIRMATION (admin_dpgr)")
        print(f"{'='*60}")

        result, status, err = await api(client, "post", f"/applications/{application_id}/cancel_confirm", token=admin_token)
        report("POST /applications/{id}/cancel_confirm", status == 200, f"status={status}")
        
        # Verify status is now CANCELLED
        result, status, err = await api(client, "get", f"/applications/{application_id}", token=researcher_token)
        report("Verify status is CANCELLED", result.get("status") == "cancelled" if result else False, f"status={result.get('status') if result else 'N/A'}")

        # =====================================================================
        # PHASE 15: COMPLETION & CLOSING (Full Lifecycle)
        # =====================================================================
        print(f"\n{'='*60}")
        print("PHASE 15: COMPLETION & CLOSING (full lifecycle)")
        print(f"{'='*60}")

        # 1. Create a second application to test completion
        tomorrow = date.today() + timedelta(days=10)
        end_date = tomorrow + timedelta(days=7)
        result, status, err = await api(client, "post", "/applications/", token=researcher_token, json_data={
            "destination_country": "allemagne",
            "destination_city": "Berlin",
            "host_institution": "TU Berlin",
            "scientific_objective": "Robotics research",
            "start_date": str(tomorrow),
            "end_date": str(end_date),
        })
        app2_id = result.get("id") if result else None
        report("Create 2nd application", app2_id is not None, f"id={app2_id}")

        if app2_id:
            # 2. Upload minimum required docs for submission
            for doc_type in ["cv", "invitation", "programme", "passport", "accord_labo"]:
                test_file_doc = Path(UPLOAD_DIR) / f"app2_{doc_type}.pdf"
                test_file_doc.write_text(f"App2 {doc_type} content")
                with open(test_file_doc, "rb") as f:
                    await api(client, "post", f"/applications/{app2_id}/documents", token=researcher_token, 
                             files={"file": (f"app2_{doc_type}.pdf", f, "application/pdf")},
                             data={"document_type": doc_type})
            
            # 3. Submit
            await api(client, "post", f"/applications/{app2_id}/submit", token=researcher_token, json_data={
                "destination_country": "allemagne", "destination_city": "Berlin", "host_institution": "TU Berlin",
                "scientific_objective": "Robotics research",
                "host_supervisor": "Dr. Klein", "supervisor_email": "klein@tu-berlin.de",
                "host_department": "Robotics", "title_of_stay": "Robotics Residency",
                "research_axis": "Robotics", "expected_outcomes": "Prototype and technical report",
            })
            
            # 4. CS Approve
            await api(client, "post", f"/cs/deliberate/{app2_id}", token=admin_token, json_data={
                "decision": "approved", "notes": "Approved for completion test"
            })
            
            # 5. Researcher uploads report -> Should trigger Status.COMPLETED
            test_report = Path(UPLOAD_DIR) / "app2_report.pdf"
            test_report.write_text("This is the final stay report.")
            with open(test_report, "rb") as f:
                result, status, err = await api(client, "post", f"/applications/{app2_id}/documents",
                    token=researcher_token,
                    files={"file": ("report.pdf", f, "application/pdf")},
                    data={"document_type": "report"}
                )
            report("Upload Report (triggers COMPLETED)", status == 200, f"status={status}")

            # 6. Verify status is COMPLETED
            result, status, err = await api(client, "get", f"/applications/{app2_id}", token=researcher_token)
            report("Verify status is COMPLETED", result.get("status") == "completed" if result else False, f"status={result.get('status') if result else 'N/A'}")

            # 7. Admin closes application
            result, status, err = await api(client, "post", f"/applications/{app2_id}/close_application", token=admin_token)
            report("POST /applications/{id}/close_application", status == 200, f"status={status}")

            # 8. Verify status is CLOSED
            result, status, err = await api(client, "get", f"/applications/{app2_id}", token=researcher_token)
            report("Verify status is CLOSED", result.get("status") == "closed" if result else False, f"status={result.get('status') if result else 'N/A'}")

        # =====================================================================
        # SUMMARY
        # =====================================================================
        print(f"\n{'='*80}")
        print(f"TEST RESULTS: {passed} passed, {failed} failed, {passed + failed} total")
        print(f"{'='*80}")

        if errors:
            print("\nFAILED TESTS:")
            for e in errors:
                print(f"  ✗ {e}")

        print(f"\nKey IDs:")
        print(f"  Session ID:     {session_id}")
        print(f"  Application ID: {application_id}")
        print(f"  Document ID:    {document_id}")


if __name__ == "__main__":
    asyncio.run(main())
