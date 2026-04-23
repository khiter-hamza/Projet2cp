#!/usr/bin/env python3
"""
Minimal API test: create application → submit → CS approve
"""

import httpx
import asyncio
from pathlib import Path
from datetime import date, timedelta

BASE_URL = "http://localhost:8000/api/v1"
UPLOAD_DIR = "uploads/test_documents"

async def api(client, method, path, token=None, json_data=None, files=None, data=None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    kwargs = {"headers": headers}
    if json_data: kwargs["json"] = json_data
    if files:     kwargs["files"] = files
    if data:      kwargs["data"] = data
    r = await getattr(client, method)(f"{BASE_URL}{path}", **kwargs)
    try:    return r.json(), r.status_code
    except: return r.content, r.status_code

def log(step, ok, detail=""):
    print(f"  {'✓' if ok else '✗'} {step}" + (f"  → {detail}" if detail else ""))

async def main():
    async with httpx.AsyncClient(timeout=30) as c:

        # ── 1. Register & login ───────────────────────────────────────────────
        for role, email, username, lastname in [
            ("chercheur",   "researcher@test.com", "researcher_user", "TestLastname"),
            ("admin_dpgr",  "admin@test.com",      "admin_user",      "AdminLastname"),
        ]:
            await api(c, "post", "/auth/register", json_data={
                "email": email, "username": username, "lastname": lastname,
                "password": "test", "role": role,
                "grade": "professeur", "anciente": 5,
                "laboratory_name": "Test Lab", "ancientee": 0,
            })

        r, _ = await api(c, "post", "/auth/login", json_data={"email": "researcher@test.com", "password": "test"})
        researcher_token = r.get("access_token")
        log("Login researcher", bool(researcher_token))

        r, _ = await api(c, "post", "/auth/login", json_data={"email": "admin@test.com", "password": "test"})
        admin_token = r.get("access_token")
        log("Login admin", bool(admin_token))

        if not researcher_token or not admin_token:
            print("FATAL: auth failed"); return

        # ── 2. Get or create session ──────────────────────────────────────────
        r, status = await api(c, "get", "/sessions/active")
        session_id = r.get("id") if status == 200 and r else None

        if not session_id:
            # Need assistant to create session — register + login
            await api(c, "post", "/auth/register", json_data={
                "email": "assistant@test.com", "username": "assistant_user",
                "lastname": "AssistantLastname", "password": "test",
                "role": "assistant_dpgr", "grade": "professeur",
                "anciente": 10, "laboratory_name": "Admin Office", "ancientee": 0,
            })
            r, _ = await api(c, "post", "/auth/login", json_data={"email": "assistant@test.com", "password": "test"})
            assistant_token = r.get("access_token")

            today = date.today()
            r, status = await api(c, "post", "/sessions/", token=assistant_token, json_data={
                "name": "2025-2026 Academic Year", "academic_year": "2025-2026",
                "start_date": str(today), "end_date": str(today + timedelta(days=120)),
            })
            session_id = r.get("id") if r else None
            log("Create session", bool(session_id))

        if not session_id:
            print("FATAL: no session"); return

        # ── 3. Create application ─────────────────────────────────────────────
        tomorrow = date.today() + timedelta(days=1)
        r, status = await api(c, "post", "/applications/", token=researcher_token, json_data={
            "destination_country": "france",
            "destination_city": "Paris",
            "host_institution": "University of Paris",
            "scientific_objective": "Research on AI and machine learning",
            "start_date": str(tomorrow),
            "end_date": str(tomorrow + timedelta(days=7)),
        })
        app_id = r.get("id") if r else None
        log("Create application", bool(app_id), f"id={app_id}")

        if not app_id:
            print("FATAL: application creation failed"); return

        # ── 4. Upload required documents ──────────────────────────────────────
        Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
        for doc_type in ["cv", "invitation", "programme", "passport", "accord_labo"]:
            f_path = Path(UPLOAD_DIR) / f"{doc_type}.pdf"
            f_path.write_text(f"Test {doc_type}")
            with open(f_path, "rb") as f:
                r, status = await api(c, "post", f"/applications/{app_id}/documents",
                    token=researcher_token,
                    files={"file": (f"{doc_type}.pdf", f, "application/pdf")},
                    data={"document_type": doc_type},
                )
            log(f"Upload {doc_type}", status in [200, 201])

        # ── 5. Submit application ─────────────────────────────────────────────
        r, status = await api(c, "post", f"/applications/{app_id}/submit",
            token=researcher_token, json_data={
                "destination_country": "france",
                "destination_city": "Paris",
                "host_institution": "University of Paris",
                "scientific_objective": "Research on AI and machine learning",
            })
        log("Submit application", status == 200, f"eligibility={r.get('eligibility_status') if r else 'N/A'}")

        # ── 6. CS approve ─────────────────────────────────────────────────────
        r, status = await api(c, "post", f"/cs/deliberate/{app_id}",
            token=admin_token, json_data={"decision": "approved", "notes": "Approved"})
        log("CS approve", status == 200)

        r, status = await api(c, "get", f"/applications/{app_id}", token=researcher_token)
        log("Verify approved", r.get("status") == "approved" if r else False,
            f"status={r.get('status') if r else 'N/A'}")

if __name__ == "__main__":
    asyncio.run(main())