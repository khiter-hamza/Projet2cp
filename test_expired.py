#!/usr/bin/env python3
"""
Two-path API workflow test:
Path 1 (Happy path): auth → session → draft → submit → CS approve → report → close app → archive session
Path 2 (Error/logic path): auth → session → draft → close session (auto-submit) → CS approve → submit → flag → delete report → archive session
"""

import httpx
import asyncio
from pathlib import Path
from datetime import date, timedelta

BASE_URL = "http://localhost:8000/api/v1"
UPLOAD_DIR = "uploads/test_documents"

# ── Credentials ───────────────────────────────────────────────────────────────
USERS = {
    "researcher": {"email": "researcher@test.com", "password": "test", "username": "researcher_user",
                   "lastname": "ResearcherLast", "role": "chercheur"},
    "assistant":  {"email": "assistant@test.com",  "password": "test", "username": "assistant_user",
                   "lastname": "AssistantLast",  "role": "assistant_dpgr"},
    "admin":      {"email": "admin@test.com",      "password": "test", "username": "admin_user",
                   "lastname": "AdminLast",       "role": "admin_dpgr"},
}

# ── Helpers ───────────────────────────────────────────────────────────────────

async def api(client, method, path, token=None, json_data=None, files=None, data=None, params=None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    kwargs = {"headers": headers}
    if json_data: kwargs["json"] = json_data
    if files:     kwargs["files"] = files
    if data:      kwargs["data"] = data
    if params:    kwargs["params"] = params
    r = await getattr(client, method)(f"{BASE_URL}{path}", **kwargs)
    try:    body = r.json()
    except: body = r.content
    return body, r.status_code

def ok(label, success, detail=""):
    sym = "✓" if success else "✗"
    line = f"    {sym} {label}"
    if detail: line += f"  → {detail}"
    print(line)
    return success

def section(title):
    print(f"\n  ── {title} {'─' * max(0, 55 - len(title))}")

def status_change(old, new, note=""):
    arrow = f"  📋 STATUS: {old or '?'} → {new or '?'}"
    if note: arrow += f"  ({note})"
    print(arrow)

async def register_all(client):
    for u in USERS.values():
        await api(client, "post", "/auth/register", json_data={
            "email": u["email"], "username": u["username"], "lastname": u["lastname"],
            "password": u["password"], "role": u["role"],
            "grade": "professeur", "anciente": 5, "laboratory_name": "Test Lab", "ancientee": 0,
        })

async def login_all(client):
    tokens = {}
    for key, u in USERS.items():
        r, s = await api(client, "post", "/auth/login", json_data={"email": u["email"], "password": u["password"]})
        tokens[key] = r.get("access_token") if s == 200 else None
        ok(f"Login {key}", bool(tokens[key]))
    return tokens

async def create_session(client, token, name):
    today = date.today()
    r, s = await api(client, "post", "/sessions/", token=token, json_data={
        "name": name, "academic_year": "2025-2026",
        "start_date": str(today), "end_date": str(today + timedelta(days=120)),
    })
    sid = r.get("id") if s in [200, 201] else None
    ok("Create session", bool(sid), f"id={sid}")
    return sid

async def create_draft(client, token, country="france", city="Paris",
                        institution="Univ Paris", objective="AI research"):
    tomorrow = date.today() + timedelta(days=1)
    r, s = await api(client, "post", "/applications/", token=token, json_data={
        "destination_country": country, "destination_city": city,
        "host_institution": institution, "scientific_objective": objective,
        "start_date": str(tomorrow), "end_date": str(tomorrow + timedelta(days=7)),
    })
    aid = r.get("id") if s in [200, 201] else None
    ok("Create draft", bool(aid), f"id={aid}")
    if aid: status_change(None, "draft")
    return aid

async def upload_docs(client, token, app_id, doc_types):
    Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    for doc_type in doc_types:
        f_path = Path(UPLOAD_DIR) / f"{app_id}_{doc_type}.pdf"
        f_path.write_text(f"Test {doc_type} for {app_id}")
        with open(f_path, "rb") as f:
            r, s = await api(client, "post", f"/applications/{app_id}/documents",
                token=token,
                files={"file": (f"{doc_type}.pdf", f, "application/pdf")},
                data={"document_type": doc_type},
            )
        ok(f"Upload {doc_type}", s in [200, 201])

async def get_app_status(client, token, app_id):
    r, s = await api(client, "get", f"/applications/{app_id}", token=token)
    return r.get("status") if s == 200 and r else None

# ══════════════════════════════════════════════════════════════════════════════
# PATH 1 — Happy path
# ══════════════════════════════════════════════════════════════════════════════

async def path1(client, tokens):
    print("\n" + "═" * 65)
    print("  PATH 1 — Happy path")
    print("═" * 65)

    # Session
    section("Session")
    session_id = await create_session(client, tokens["assistant"], "Path1-Session")
    if not session_id: print("  FATAL: no session"); return

    # Draft
    section("Draft application")
    app_id = await create_draft(client, tokens["researcher"])
    if not app_id: print("  FATAL: no app"); return

    # Documents
    section("Upload required documents")
    await upload_docs(client, tokens["researcher"], app_id,
                      ["cv", "invitation", "programme", "passport", "accord_labo"])

    # Submit
    section("Submit application")
    prev = await get_app_status(client, tokens["researcher"], app_id)
    r, s = await api(client, "post", f"/applications/{app_id}/submit", token=tokens["researcher"],
        json_data={"destination_country": "france", "destination_city": "Paris",
                   "host_institution": "Univ Paris", "scientific_objective": "AI research",
                   "host_supervisor": "Dr. Martin", "supervisor_email": "martin@univ-paris.fr",
                   "host_department": "Computer Science", "title_of_stay": "AI Research Residency",
                   "research_axis": "Artificial Intelligence", "expected_outcomes": "Joint publication and prototype"})
    submitted_ok = ok("Submit", s == 200,
        f"eligibility={r.get('eligibility_status') if isinstance(r, dict) else s}")
    if submitted_ok:
        curr = await get_app_status(client, tokens["researcher"], app_id)
        status_change(prev, curr)

    # Close session
    section("Close session")
    r, s = await api(client, "patch", f"/sessions/{session_id}/close", token=tokens["assistant"])
    ok("Close session", s == 200, f"status={s}")

    # CS approve
    section("CS deliberation → approve")
    prev = await get_app_status(client, tokens["researcher"], app_id)
    r, s = await api(client, "post", f"/cs/deliberate/{app_id}", token=tokens["admin"],
        json_data={"decision": "approved", "notes": "Excellent research proposal"})
    approved_ok = ok("CS approve", s == 200, f"status={s}")
    if approved_ok:
        curr = await get_app_status(client, tokens["researcher"], app_id)
        status_change(prev, curr)

    # Upload report
    section("Upload report (triggers COMPLETED)")
    prev = await get_app_status(client, tokens["researcher"], app_id)
    await upload_docs(client, tokens["researcher"], app_id, ["report"])
    curr = await get_app_status(client, tokens["researcher"], app_id)
    status_change(prev, curr, "report upload")

    # Close application
    section("Close application")
    prev = curr
    r, s = await api(client, "post", f"/applications/{app_id}/close_application", token=tokens["admin"])
    ok("Close application", s == 200, f"status={s}")
    curr = await get_app_status(client, tokens["researcher"], app_id)
    status_change(prev, curr)

    # Archive session
    section("Archive session")
    r, s = await api(client, "patch", f"/sessions/{session_id}/archive", token=tokens["assistant"])
    ok("Archive session", s == 200, f"status={s}")

    print(f"\n  ✓ Path 1 complete — final app status: {await get_app_status(client, tokens['researcher'], app_id)}")


# ══════════════════════════════════════════════════════════════════════════════
# PATH 2 — Error/logic path (things that should fail or be guarded)
# ══════════════════════════════════════════════════════════════════════════════

async def path2(client, tokens):
    print("\n" + "═" * 65)
    print("  PATH 2 — Error/logic path (violations must be rejected)")
    print("═" * 65)

    def expect_fail(label, s, body, note=""):
        """A step MUST fail — flag it wrong if it succeeds."""
        failed = s >= 400
        sym = "✓" if failed else "✗ (should have failed!)"
        err = body.get("detail", body) if isinstance(body, dict) else s
        line = f"    {sym} {label}  → HTTP {s}  |  {err}"
        if note: line += f"  [{note}]"
        print(line)
        return failed

    # Session
    section("Session")
    session_id = await create_session(client, tokens["assistant"], "Path2-Session")
    if not session_id: print("  FATAL: no session"); return

    # Draft (no docs → cannot submit yet)
    section("Draft application (no docs)")
    app_id = await create_draft(client, tokens["researcher"],
                                 country="allemagne", city="Berlin",
                                 institution="TU Berlin", objective="Robotics research")
    if not app_id: print("  FATAL: no app"); return

    # Close session WITH unsubmitted draft → should auto-submit or reject
    section("Close session with unsubmitted draft (auto-submit expected)")
    prev = await get_app_status(client, tokens["researcher"], app_id)
    r, s = await api(client, "patch", f"/sessions/{session_id}/close", token=tokens["assistant"])
    ok("Close session (auto-submit draft)", s == 200, f"status={s}")
    curr = await get_app_status(client, tokens["researcher"], app_id)
    status_change(prev, curr, "auto-submit on session close")

    # CS approve
    section("CS deliberation → approve")
    prev = curr
    r, s = await api(client, "post", f"/cs/deliberate/{app_id}", token=tokens["admin"],
        json_data={"decision": "approved", "notes": "Approved for error path test"})
    ok("CS approve", s == 200)
    curr = await get_app_status(client, tokens["researcher"], app_id)
    status_change(prev, curr)

    # Try to submit AGAIN after approval (must fail)
    section("Re-submit after CS approval (must fail)")
    r, s = await api(client, "post", f"/applications/{app_id}/submit", token=tokens["researcher"],
        json_data={"destination_country": "allemagne", "destination_city": "Berlin",
                   "host_institution": "TU Berlin", "scientific_objective": "Robotics research"})
    expect_fail("Re-submit already-approved app", s, r, "cannot re-submit approved application")

    # Flag the application
    section("Flag application")
    prev = await get_app_status(client, tokens["researcher"], app_id)
    r, s = await api(client, "post", f"/applications/{app_id}/flag", token=tokens["admin"],
        json_data={"reason": "Suspicious documentation"})
    ok("Flag application", s == 200, f"status={s}")
    curr = await get_app_status(client, tokens["researcher"], app_id)
    status_change(prev, curr)

    # Upload report on FLAGGED application (must fail)
    section("Upload report on flagged app (must fail)")
    Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    f_path = Path(UPLOAD_DIR) / f"{app_id}_report.pdf"
    f_path.write_text("Report for flagged app")
    with open(f_path, "rb") as f:
        r, s = await api(client, "post", f"/applications/{app_id}/documents",
            token=tokens["researcher"],
            files={"file": ("report.pdf", f, "application/pdf")},
            data={"document_type": "report"},
        )
    expect_fail("Upload report to flagged app", s, r, "flagged apps should not accept reports")

    # Delete the (non-existent / rejected) report — try anyway
    section("Delete report (was never accepted — must fail)")
    # Get document list to find any report doc id
    r, s = await api(client, "get", f"/applications/{app_id}/documents", token=tokens["researcher"])
    docs = r if isinstance(r, list) else []
    report_doc = next((d for d in docs if d.get("document_type") == "report"), None)
    if report_doc:
        doc_id = report_doc.get("id")
        r, s = await api(client, "delete", f"/document/{doc_id}", token=tokens["researcher"])
        expect_fail("Delete report from flagged app", s, r, "should not be deletable on flagged")
    else:
        print("    ✓ No report doc exists (upload was correctly rejected — nothing to delete)")

    # Archive session (while app is flagged — should this be allowed?)
    section("Archive session with flagged application")
    r, s = await api(client, "patch", f"/sessions/{session_id}/archive", token=tokens["assistant"])
    if s == 200:
        ok("Archive session (accepted)", True, "server allows archive with flagged apps")
    else:
        ok("Archive session (rejected)", False,
           f"HTTP {s} — server blocks archive while apps are flagged")

    print(f"\n  ✓ Path 2 complete — final app status: {await get_app_status(client, tokens['researcher'], app_id)}")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

async def main():
    print("═" * 65)
    print("  COMPREHENSIVE WORKFLOW TEST")
    print("═" * 65)

    async with httpx.AsyncClient(timeout=30) as client:

        section("Register & login all users")
        await register_all(client)
        tokens = await login_all(client)

        if not all(tokens.values()):
            print("FATAL: one or more logins failed"); return

        await path1(client, tokens)
        await path2(client, tokens)

    print("\n" + "═" * 65)
    print("  ALL PATHS DONE")
    print("═" * 65)

if __name__ == "__main__":
    asyncio.run(main())