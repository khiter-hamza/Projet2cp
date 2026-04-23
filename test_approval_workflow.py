#!/usr/bin/env python3
"""
API Workflow Testing Script - Approval & Rejection Flow
Tests the complete application submission and CS deliberation workflow, including indemnity validation.
"""

import httpx
import asyncio
import time
from pathlib import Path
from datetime import date, timedelta

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
UPLOAD_DIR = "uploads/test_documents"

# Generate unique strings for this test run
RUN_ID = str(int(time.time()))
RESEARCHER_EMAIL = f"researcher_{RUN_ID}@test.com"
RESEARCHER_USERNAME = f"researcher_user_{RUN_ID}"
ADMIN_EMAIL = f"admin_{RUN_ID}@test.com"
ADMIN_USERNAME = f"admin_user_{RUN_ID}"
PASSWORD = "TestPassword123!"

async def register_user(client, email, username, role, grade="professeur"):
    print(f"\n[REGISTER] Creating {role}: {email}")
    payload = {
        "email": email, "username": username, "lastname": "Test",
        "password": PASSWORD, "role": role, "grade": grade,
        "anciente": 5, "laboratory_name": "Lab1", "ancientee": 0
    }
    response = await client.post(f"{BASE_URL}/auth/register", json=payload)
    if response.status_code == 200:
        print("✓ Registered successfully")
        return response.json()
    print(f"✗ Registration failed: {response.status_code}")
    return None

async def login_user(client, email):
    print(f"\n[LOGIN] Authenticating: {email}")
    response = await client.post(f"{BASE_URL}/auth/login", json={"email": email, "password": PASSWORD})
    if response.status_code == 200:
        print("✓ Login successful")
        return response.json().get("access_token")
    print(f"✗ Login failed: {response.text}")
    return None

async def create_session(client, token):
    print("\n[SESSION] Checking active session")
    resp = await client.get(f"{BASE_URL}/sessions/active")
    if resp.status_code == 200:
        return resp.json().get("id")
    
    print("\n[SESSION] Creating new session as admin")
    tomorrow = date.today() + timedelta(days=1)
    end_dt = tomorrow + timedelta(days=90)
    payload = {
        "name": f"Session {RUN_ID}", "academic_year": "2024-2025",
        "start_date": str(tomorrow), "end_date": str(end_dt)
    }
    resp = await client.post(f"{BASE_URL}/sessions/", json=payload, headers={"Authorization": f"Bearer {token}"})
    if resp.status_code == 200:
        return resp.json().get("id")
    print(f"✗ Session creation failed: {resp.text}")
    return None

async def main():
    print("=" * 60)
    print("TEST: APP CREATION -> SUBMISSION -> APPROVAL")
    print("=" * 60)
    
    async with httpx.AsyncClient(timeout=30) as client:
        # Setup users
        await register_user(client, ADMIN_EMAIL, ADMIN_USERNAME, "admin_dpgr")
        admin_token = await login_user(client, ADMIN_EMAIL)
        
        await register_user(client, RESEARCHER_EMAIL, RESEARCHER_USERNAME, "chercheur")
        researcher_token = await login_user(client, RESEARCHER_EMAIL)
        
        if not admin_token or not researcher_token: return
        
        # Setup session
        session_id = await create_session(client, admin_token)
        if not session_id: return
        
        # 1. Draft App
        print("\n[WORKFLOW] Creating draft application")
        tomorrow = date.today() + timedelta(days=1)
        next_month = tomorrow + timedelta(days=30)
        app_payload = {
            "destination_country": "france", "destination_city": "Paris",
            "host_institution": "University of Paris", "scientific_objective": "Test",
            "start_date": str(tomorrow), "end_date": str(next_month)
        }
        res = await client.post(f"{BASE_URL}/applications/", json=app_payload, headers={"Authorization": f"Bearer {researcher_token}"})
        if res.status_code != 200:
            print("✗ Draft creation failed:", res.text)
            return
        
        app_id = res.json().get("id")
        print(f"✓ Draft created (ID: {app_id})")
        
        # 2. Submit App
        print("\n[WORKFLOW] Submitting application")
        res = await client.post(f"{BASE_URL}/applications/{app_id}/submit", json=app_payload, headers={"Authorization": f"Bearer {researcher_token}"})
        if res.status_code != 200:
            print("✗ Submission failed:", res.text)
            return
        print(f"✓ Application submitted")
        
        # 3. View App (Verify Indemnity)
        print("\n[WORKFLOW] Verifying Submitted Application details")
        res = await client.get(f"{BASE_URL}/applications/{app_id}", headers={"Authorization": f"Bearer {admin_token}"})
        if res.status_code == 200:
            app_data = res.json()
            fees = app_data.get('calculated_fees')
            print(f"✓ Retrieved App. Calculated Fees for duration: {fees}")
            if not fees:
                print("! Warning: Calculated fees are empty! Indemnity calculation might have failed.")
        
        # 4. Skip Preparation/Dashboard (Endpoints not mapped)
        
        # 5. Approve Application
        print(f"\n[WORKFLOW] Approving Application {app_id}")
        deliberate_payload = {
            "decision": "approved",
            "notes": "Approved by testing script"
        }
        res = await client.post(f"{BASE_URL}/cs/deliberate/{app_id}", headers={"Authorization": f"Bearer {admin_token}"}, json=deliberate_payload)
        if res.status_code == 200:
            print(f"✓ CS Decision: {res.json().get('cs_decision')} | Application Status: {res.json().get('status')}")
        else:
            print(f"✗ Approval failed: {res.status_code} - {res.text}")

if __name__ == "__main__":
    asyncio.run(main())
