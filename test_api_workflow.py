#!/usr/bin/env python3
"""
Comprehensive API Workflow Testing Script
Respects the complete application submission and evaluation workflow
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

# Test credentials
RESEARCHER_EMAIL = "researcher@test.com"
RESEARCHER_PASSWORD = "TestPassword123!"
RESEARCHER_USERNAME = "researcher_user"
RESEARCHER_LASTNAME = "Test"

ADMIN_EMAIL = "admin@test.com"
ADMIN_PASSWORD = "AdminPassword123!"
ADMIN_USERNAME = "admin_user"
ADMIN_LASTNAME = "Admin"

# Global variables to store IDs
researcher_token = None
admin_token = None
session_id = None
application_id = None
document_id = None


# ============================================================================
# 1. AUTHENTICATION & USER MANAGEMENT
# ============================================================================

async def register_user(client, email, username, lastname, password, role="chercheur", grade="professeur", anciente=5, laboratory_name="Lab1"):
    """Register a new user"""
    print(f"\n[1. REGISTER] Creating user: {email}")
    
    payload = {
        "email": email,
        "username": username,
        "lastname": lastname,
        "password": password,
        "role": role,
        "grade": grade,
        "anciente": anciente,
        "laboratory_name": laboratory_name,
        "ancientee": 0
    }
    
    try:
        response = await client.post(f"{BASE_URL}/auth/register", json=payload)
        response.raise_for_status()
        user = response.json()
        print(f"✓ User registered: {user}")
        return user
    except httpx.HTTPStatusError as e:
        print(f"✗ Registration failed: {e.response.status_code} - {e.response.text}")
        return None


async def login_user(client, email, password):
    """Login and get authentication token"""
    print(f"\n[2. LOGIN] Authenticating user: {email}")
    
    payload = {
        "email": email,
        "password": password
    }
    
    try:
        response = await client.post(f"{BASE_URL}/auth/login", json=payload)
        response.raise_for_status()
        data = response.json()
        print(f"✓ Login successful")
        print(f"  Token: {data.get('access_token', data)[:50]}...")
        return data
    except httpx.HTTPStatusError as e:
        print(f"✗ Login failed: {e.response.status_code} - {e.response.text}")
        return None


# ============================================================================
# 2. SESSION MANAGEMENT
# ============================================================================

async def get_active_session(client):
    """Get the currently active session"""
    print(f"\n[3. GET ACTIVE SESSION]")
    
    try:
        response = await client.get(f"{BASE_URL}/sessions/active")
        response.raise_for_status()
        session = response.json()
        print(f"✓ Active session retrieved:")
        print(f"  ID: {session.get('id')}")
        print(f"  Name: {session.get('name')}")
        print(f"  Academic Year: {session.get('academic_year')}")
        print(f"  Start Date: {session.get('start_date')}")
        print(f"  End Date: {session.get('end_date')}")
        return session
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            print(f"✗ No active session found")
        else:
            print(f"✗ Get active session failed: {e.response.status_code}")
        return None


async def create_session(client, admin_token, name, academic_year, start_date, end_date):
    """Create a new session (Admin only)"""
    print(f"\n[3.1 CREATE SESSION] Admin creating session: {name}")
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    payload = {
        "name": name,
        "academic_year": academic_year,
        "start_date": start_date,
        "end_date": end_date
    }
    
    try:
        response = await client.post(
            f"{BASE_URL}/sessions/",
            json=payload,
            headers=headers
        )
        response.raise_for_status()
        session = response.json()
        print(f"✓ Session created:")
        print(f"  ID: {session.get('id')}")
        print(f"  Name: {session.get('name')}")
        return session
    except httpx.HTTPStatusError as e:
        print(f"✗ Create session failed: {e.response.status_code} - {e.response.text}")
        return None


# ============================================================================
# 3. APPLICATION WORKFLOW
# ============================================================================

async def create_draft_application(client, token, destination_country="france"):
    """Create a new draft application"""
    print(f"\n[4. CREATE DRAFT APPLICATION]")
    
    headers = {"Authorization": f"Bearer {token}"}
    tomorrow = date.today() + timedelta(days=1)
    next_month = tomorrow + timedelta(days=30)
    
    payload = {
        "destination_country": destination_country.lower() if isinstance(destination_country, str) else destination_country,
        "destination_city": "Paris",
        "host_institution": "University of Paris",
        "scientific_objective": "Research on AI and machine learning",
        "start_date": str(tomorrow),
        "end_date": str(next_month),
    }
    
    try:
        response = await client.post(
            f"{BASE_URL}/applications/",
            json=payload,
            headers=headers
        )
        response.raise_for_status()
        app = response.json()
        print(f"✓ Draft application created:")
        print(f"  ID: {app.get('id')}")
        print(f"  Status: {app.get('status')}")
        print(f"  Destination: {app.get('destination_country')} - {app.get('destination_city')}")
        return app
    except httpx.HTTPStatusError as e:
        print(f"✗ Create application failed: {e.response.status_code} - {e.response.text}")
        return None


async def update_draft_application(client, token, app_id, data):
    """Update a draft application"""
    print(f"\n[5. UPDATE DRAFT APPLICATION] ID: {app_id}")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = await client.patch(
            f"{BASE_URL}/applications/{app_id}",
            json=data,
            headers=headers
        )
        response.raise_for_status()
        app = response.json()
        print(f"✓ Application updated:")
        print(f"  Status: {app.get('status')}")
        print(f"  Scientific Objective: {app.get('scientific_objective')}")
        return app
    except httpx.HTTPStatusError as e:
        print(f"✗ Update application failed: {e.response.status_code} - {e.response.text}")
        return None


async def get_application(client, token, app_id):
    """Retrieve a specific application"""
    print(f"\n[5.1 GET APPLICATION] ID: {app_id}")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = await client.get(
            f"{BASE_URL}/applications/{app_id}",
            headers=headers
        )
        response.raise_for_status()
        app = response.json()
        print(f"✓ Application retrieved:")
        print(f"  Status: {app.get('status')}")
        print(f"  Eligible: {app.get('is_eligible')}")
        print(f"  CS Decision: {app.get('cs_decision')}")
        return app
    except httpx.HTTPStatusError as e:
        print(f"✗ Get application failed: {e.response.status_code} - {e.response.text}")
        return None


async def list_applications(client, token):
    """List all applications for the current user"""
    print(f"\n[5.2 LIST APPLICATIONS]")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = await client.get(
            f"{BASE_URL}/applications/",
            headers=headers
        )
        response.raise_for_status()
        apps = response.json()
        print(f"✓ Applications retrieved: {len(apps)} applications")
        for app in apps:
            print(f"  - {app.get('id')}: Status={app.get('status')}, Eligible={app.get('is_eligible')}")
        return apps
    except httpx.HTTPStatusError as e:
        print(f"✗ List applications failed: {e.response.status_code} - {e.response.text}")
        return None


# ============================================================================
# 4. DOCUMENT MANAGEMENT
# ============================================================================

async def create_test_document(filename):
    """Create a test document file"""
    Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    filepath = Path(UPLOAD_DIR) / filename
    
    if not filepath.exists():
        filepath.write_text("This is a test document for API testing purposes.")
    
    return filepath


async def upload_document(client, token, app_id, document_type, file_path):
    """Upload a document for an application"""
    print(f"\n[6. UPLOAD DOCUMENT] Type: {document_type}")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        with open(file_path, "rb") as f:
            files = {
                "file": (Path(file_path).name, f, "application/pdf")
            }
            data = {
                "document_type": document_type
            }
            
            response = await client.post(
                f"{BASE_URL}/applications/{app_id}/documents",
                files=files,
                data=data,
                headers=headers
            )
        
        response.raise_for_status()
        doc = response.json()
        print(f"✓ Document uploaded:")
        print(f"  ID: {doc.get('id')}")
        print(f"  Type: {doc.get('document_type')}")
        print(f"  File: {doc.get('file_name')}")
        return doc
    except httpx.HTTPStatusError as e:
        print(f"✗ Upload document failed: {e.response.status_code} - {e.response.text}")
        return None


async def get_documents(client, token, app_id):
    """Get all documents for an application"""
    print(f"\n[6.1 GET DOCUMENTS] Application ID: {app_id}")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = await client.get(
            f"{BASE_URL}/applications/{app_id}/documents",
            headers=headers
        )
        response.raise_for_status()
        docs = response.json()
        print(f"✓ Documents retrieved: {len(docs)} documents")
        for doc in docs:
            print(f"  - {doc.get('id')}: {doc.get('document_type')}")
        return docs
    except httpx.HTTPStatusError as e:
        print(f"✗ Get documents failed: {e.response.status_code} - {e.response.text}")
        return None


# ============================================================================
# 5. ELIGIBILITY & EVALUATION
# ============================================================================


async def get_eligibility_details(client, token, app_id):
    """Get detailed eligibility information"""
    print(f"\n[7.1 GET ELIGIBILITY DETAILS] Application ID: {app_id}")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = await client.get(
            f"{BASE_URL}/applications/{app_id}/eligibility-details",
            headers=headers
        )
        response.raise_for_status()
        details = response.json()
        print(f"✓ Eligibility details retrieved:")
        print(f"  Grade Eligible: {details.get('grade_eligible')}")
        print(f"  Required Documents: {details.get('required_documents', [])}")
        return details
    except httpx.HTTPStatusError as e:
        print(f"✗ Get eligibility details failed: {e.response.status_code} - {e.response.text}")
        return None



# ============================================================================
# 6. APPLICATION SUBMISSION
# ============================================================================

async def submit_application(client, token, app_id, data):
    """Submit a draft application for review"""
    print(f"\n[9. SUBMIT APPLICATION] Application ID: {app_id}")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = await client.post(
            f"{BASE_URL}/applications/{app_id}/submit",
            json=data,
            headers=headers
        )
        response.raise_for_status()
        result = response.json()
        print(f"✓ Application submitted successfully:")
        print(f"  Status: {result.get('status')}")
        return result
    except httpx.HTTPStatusError as e:
        print(f"✗ Submit application failed: {e.response.status_code} - {e.response.text}")
        return None


# ============================================================================
# 7. HISTORY & TRACKING
# ============================================================================

async def get_application_history(client, token, app_id):
    """Get the history of an application"""
    print(f"\n[10. GET APPLICATION HISTORY] Application ID: {app_id}")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = await client.get(
            f"{BASE_URL}/applications/{app_id}/history",
            headers=headers,
            params={"limit": 50, "offset": 0}
        )
        response.raise_for_status()
        history = response.json()
        print(f"✓ Application history retrieved:")
        print(f"  Total events: {history.get('total', 0)}")
        for event in history.get('items', [])[:5]:
            print(f"  - {event.get('event_type')}: {event.get('timestamp')}")
        return history
    except httpx.HTTPStatusError as e:
        print(f"✗ Get application history failed: {e.response.status_code} - {e.response.text}")
        return None


async def get_application_history_page(client, token, limit=50, offset=0, status=None):
    """Get paginated application history"""
    print(f"\n[10.1 GET HISTORY PAGE] Limit: {limit}, Offset: {offset}")
    
    headers = {"Authorization": f"Bearer {token}"}
    params = {
        "limit": limit,
        "offset": offset,
        "sort_by": "submitted_at",
        "sort_order": "desc",
        "session_filter": "this"
    }
    
    if status:
        params["status"] = status
    
    try:
        response = await client.get(
            f"{BASE_URL}/applications/history",
            headers=headers,
            params=params
        )
        response.raise_for_status()
        history = response.json()
        print(f"✓ History page retrieved:")
        print(f"  Total: {history.get('total')}")
        print(f"  Items: {len(history.get('items', []))}")
        return history
    except httpx.HTTPStatusError as e:
        print(f"✗ Get history page failed: {e.response.status_code} - {e.response.text}")
        return None


# ============================================================================
# 8. CS WORKFLOW (Admin/CS Users)
# ============================================================================

async def prepare_cs_deliberation(client, token, session_id):
    """Prepare CS deliberation for a session"""
    print(f"\n[11. PREPARE CS DELIBERATION] Session ID: {session_id}")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = await client.post(
            f"{BASE_URL}/cs/prepare-deliberation/{session_id}",
            headers=headers
        )
        response.raise_for_status()
        result = response.json()
        print(f"✓ CS deliberation prepared:")
        print(f"  Session: {result.get('session_name')}")
        print(f"  Total Applications: {result.get('total_applications')}")
        print(f"  Ready: {result.get('ready_for_deliberation')}")
        return result
    except httpx.HTTPStatusError as e:
        print(f"✗ Prepare CS deliberation failed: {e.response.status_code} - {e.response.text}")
        return None


async def get_cs_dashboard(client, token, session_id=None):
    """Get CS dashboard with applications for decision"""
    print(f"\n[11.1 GET CS DASHBOARD] Session ID: {session_id}")
    
    headers = {"Authorization": f"Bearer {token}"}
    params = {}
    if session_id:
        params["session_id"] = session_id
    
    try:
        response = await client.get(
            f"{BASE_URL}/cs/dashboard",
            headers=headers,
            params=params
        )
        response.raise_for_status()
        dashboard = response.json()
        print(f"✓ CS dashboard retrieved:")
        print(f"  Applications Ready: {dashboard.get('applications_count')}")
        return dashboard
    except httpx.HTTPStatusError as e:
        print(f"✗ Get CS dashboard failed: {e.response.status_code} - {e.response.text}")
        return None


async def approve_application(client, token, app_id):
    """CS: Approve an application"""
    print(f"\n[12. APPROVE APPLICATION] Application ID: {app_id}")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = await client.post(
            f"{BASE_URL}/cs/applications/{app_id}/approve",
            headers=headers,
            json={}
        )
        response.raise_for_status()
        result = response.json()
        print(f"✓ Application approved:")
        print(f"  CS Decision: {result.get('cs_decision')}")
        return result
    except httpx.HTTPStatusError as e:
        print(f"✗ Approve application failed: {e.response.status_code} - {e.response.text}")
        return None


async def reject_application(client, token, app_id, reason):
    """CS: Reject an application"""
    print(f"\n[12.1 REJECT APPLICATION] Application ID: {app_id}")
    
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"reason": reason}
    
    try:
        response = await client.post(
            f"{BASE_URL}/cs/applications/{app_id}/reject",
            json=payload,
            headers=headers
        )
        response.raise_for_status()
        result = response.json()
        print(f"✓ Application rejected:")
        print(f"  CS Decision: {result.get('cs_decision')}")
        return result
    except httpx.HTTPStatusError as e:
        print(f"✗ Reject application failed: {e.response.status_code} - {e.response.text}")
        return None


# ============================================================================
# MAIN WORKFLOW
# ============================================================================

async def main():
    """Main workflow demonstrating the complete API usage"""
    
    print("=" * 80)
    print("API WORKFLOW TEST - Comprehensive Application Submission Process")
    print("=" * 80)
    
    async with httpx.AsyncClient(timeout=30) as client:
        
        # ===== PHASE 1: AUTHENTICATION =====
        print("\n" + "=" * 80)
        print("PHASE 1: AUTHENTICATION & USER SETUP")
        print("=" * 80)
        
        # Register researcher
        researcher = await register_user(
            client,
            RESEARCHER_EMAIL,
            RESEARCHER_USERNAME,
            RESEARCHER_LASTNAME,
            RESEARCHER_PASSWORD,
            role="chercheur",
            grade="professeur"
        )
        
        # Register admin
        admin = await register_user(
            client,
            ADMIN_EMAIL,
            ADMIN_USERNAME,
            ADMIN_LASTNAME,
            ADMIN_PASSWORD,
            role="admin_dpgr",
            grade="professeur"
        )
        
        # Login researcher
        researcher_auth = await login_user(client, RESEARCHER_EMAIL, RESEARCHER_PASSWORD)
        researcher_token = researcher_auth.get("access_token") if researcher_auth else None
        
        # Login admin
        admin_auth = await login_user(client, ADMIN_EMAIL, ADMIN_PASSWORD)
        admin_token = admin_auth.get("access_token") if admin_auth else None
        
        if not researcher_token or not admin_token:
            print("\n✗ Authentication failed. Exiting.")
            return
        
        # ===== PHASE 2: SESSION MANAGEMENT =====
        print("\n" + "=" * 80)
        print("PHASE 2: SESSION MANAGEMENT")
        print("=" * 80)
        
        # Check for active session
        active_session = await get_active_session(client)
        
        if not active_session:
            # Create a new session if none exists
            tomorrow = date.today() + timedelta(days=1)
            end_date = tomorrow + timedelta(days=90)
            
            new_session = await create_session(
                client,
                admin_token,
                "2024-2025 Academic Year",
                "2024-2025",
                str(tomorrow),
                str(end_date)
            )
            session_id = new_session.get("id") if new_session else None
        else:
            session_id = active_session.get("id")
        
        # ===== PHASE 3: APPLICATION CREATION & MANAGEMENT =====
        print("\n" + "=" * 80)
        print("PHASE 3: APPLICATION CREATION & MANAGEMENT")
        print("=" * 80)
        
        # Create draft application
        app = await create_draft_application(client, researcher_token)
        application_id = app.get("id") if app else None
        
        if not application_id:
            print("\n✗ Application creation failed. Exiting.")
            return
        
        # Update draft with more details
        update_data = {
            "destination_country": "france",
            "destination_city": "Lyon",
            "host_institution": "Claude Bernard University",
            "scientific_objective": "Advanced research on distributed systems and AI",
        }
        await update_draft_application(client, researcher_token, application_id, update_data)
        
        # Get application details
        app_details = await get_application(client, researcher_token, application_id)
        
        # List all applications
        all_apps = await list_applications(client, researcher_token)
        
        # ===== PHASE 4: DOCUMENT UPLOAD =====
        print("\n" + "=" * 80)
        print("PHASE 4: DOCUMENT MANAGEMENT")
        print("=" * 80)
        
        # Create test documents
        test_doc_path = await create_test_document("test_document.txt")
        
        # Upload document
        doc = await upload_document(
            client,
            researcher_token,
            application_id,
            "cv",
            str(test_doc_path)
        )
        document_id = doc.get("id") if doc else None
        
        # Get documents
        docs = await get_documents(client, researcher_token, application_id)
        
        # ===== PHASE 5: ELIGIBILITY & EVALUATION =====
        print("\n" + "=" * 80)
        print("PHASE 5: ELIGIBILITY & EVALUATION")
        print("=" * 80)
        
        
        # Get eligibility details
        eligibility_details = await get_eligibility_details(client, researcher_token, application_id)
        
        
        # ===== PHASE 6: APPLICATION SUBMISSION =====
        print("\n" + "=" * 80)
        print("PHASE 6: APPLICATION SUBMISSION")
        print("=" * 80)
        
        # Submit application
        submit_data = {
            "destination_country": "france",
            "destination_city": "Lyon",
            "host_institution": "Claude Bernard University",
            "scientific_objective": "Advanced research on distributed systems and AI",
        }
        
        submitted_app = await submit_application(client, researcher_token, application_id, submit_data)
        
        # ===== PHASE 7: HISTORY & TRACKING =====
        print("\n" + "=" * 80)
        print("PHASE 7: HISTORY & TRACKING")
        print("=" * 80)
        
        # Get application history
        history = await get_application_history(client, researcher_token, application_id)
        
        # Get history page
        history_page = await get_application_history_page(client, researcher_token, limit=10, offset=0)
        
        # ===== PHASE 8: CS WORKFLOW (Optional) =====
        if admin_token and session_id:
            print("\n" + "=" * 80)
            print("PHASE 8: CS WORKFLOW (Admin Operations)")
            print("=" * 80)
            
            
            # Get CS dashboard
            cs_dashboard = await get_cs_dashboard(client, admin_token, session_id)
        
        # ===== SUMMARY =====
        print("\n" + "=" * 80)
        print("WORKFLOW COMPLETED SUCCESSFULLY")
        print("=" * 80)
        print(f"\nKey IDs for reference:")
        print(f"  Researcher User ID: {researcher.get('id') if researcher else 'N/A'}")
        print(f"  Admin User ID: {admin.get('id') if admin else 'N/A'}")
        print(f"  Session ID: {session_id}")
        print(f"  Application ID: {application_id}")
        print(f"  Document ID: {document_id}")


if __name__ == "__main__":
    asyncio.run(main())
