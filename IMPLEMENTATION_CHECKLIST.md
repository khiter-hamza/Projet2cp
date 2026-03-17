# 📋 IMPLEMENTATION CHECKLIST - What's Left to Do

**Project**: CAHIER DES CHARGES - PRJP12  
**Current Date**: March 16, 2026  
**Backend Status**: ~45% Complete

---

## ✅ COMPLETED (DON'T TOUCH)

### Phase 1: Core Setup
- [x] FastAPI setup with async support
- [x] PostgreSQL database configuration
- [x] Alembic migrations setup
- [x] CORS & middleware setup
- [x] Authentication (login/register/JWT)
- [x] User model with roles & grades

### Phase 2: Applications Management
- [x] Application CRUD (create, read, update, delete)
- [x] Draft creation & management
- [x] Application submission with status = SUBMITTED
- [x] Application listing with filters

### Phase 3: Documents & Sessions
- [x] Document upload/download (single + batch)
- [x] Session management (create/update/list)

### Phase 4: Eligibility Verification ✨ (NEW)
- [x] Eligibility service (grade, history, documents checks)
- [x] Automatic verification on submission
- [x] Status transition (CS_PREPARATION or REJECTED)
- [x] Eligibility details endpoint

### Phase 5: Scoring System ✨ (NEW - Teacher Requirements)
- [x] Score calculation (completed apps + total apps)
- [x] Scoring endpoints
- [x] Proper weighting (completed x10, total x5)

### Phase 6: Notifications
- [x] Basic notification CRUD (get/delete/mark-read)
- [x] Notification service foundation

### Phase 7: Indemnity & Zones
- [x] Zone management (create/update/list/delete)
- [x] Indemnity calculation logic (tiered by duration)
- [x] Automatic calculation when creating indemnity

---

## ❌ NOT IMPLEMENTED (REQUIRED)

### **🔴 PRIORITY 1 - CRITICAL (Do First)**

#### 1. **CS Workflow & Decision Making** ⚠️ CORE FEATURE
**Status**: Not Started  
**What's Needed**:
- [ ] CS Preparation endpoint - consolidate eligible applications
- [ ] CS Deliberation endpoint - approve/reject with notes
- [ ] Generate attestations for approved applications
- [ ] Calculate fees for approved applications
- [ ] CS decision notification to users

**Files to Create**:
- `services/admin/cs_service.py` - CS decision logic
- `endpoints/cs.py` - CS endpoints (deliberation, preparation)

**Endpoints Needed**:
```
POST /api/v1/cs/prepare-deliberation/{session_id}
    → Consolidate applications ready for CS
    
POST /api/v1/cs/deliberate/{application_id}
    → Approve or reject with notes
    → Input: {decision: "approuve"|"rejete", notes: "..."}
    
GET /api/v1/cs/dashboard
    → Dashboard for CS with scores, recommendations, history
```

---

#### 2. **Fees & Indemnity Calculation** ✅ IMPLEMENTED
**Status**: DONE (zone management + calculation logic both exist in idemnity endpoints)  
**What's Done**:
- [x] Zone management endpoints (GET/POST/DELETE)
- [x] Indemnity calculation logic (tiered by duration)
- [x] Fee calculation happens automatically when creating indemnity

No further work needed - indemnity.py has everything.

#### 3. **Application Report Submission** ⚠️ USER ACTION
**Status**: Model fields exist, no service/endpoints  
**What's Needed**:
- [ ] Report upload endpoint
- [ ] Report validation (PDF format, completeness)
- [ ] Report submission status change
- [ ] Automatic reminders for late reports

**Files to Create**:
- `services/application/report_service.py`
- `endpoints/reports.py`

**Endpoints Needed**:
```
POST /api/v1/applications/{id}/submit-report
    → Upload stage/séjour report
    → Input: file upload (PDF)
    → Status: COMPLETED

GET /api/v1/applications/{id}/report
    → Download submitted report
```

---

#### 4. **Notifications & Alerts** ⚠️ COMMUNICATION
**Status**: Skeleton only  
**What's Needed**:
- [ ] Email notifications on status changes
- [ ] Rejection email with reason
- [ ] Approval email with attestation
- [ ] Report submission reminders
- [ ] Deadline alerts

**Files to Create**:
- `services/notification/email_service.py` - Email template & sending
- `services/notification/notification_triggers.py` - When to send

**Functions Needed**:
```python
async def notify_application_approved(application)
async def notify_application_rejected(application)
async def notify_report_deadline_approaching(application)
async def send_report_reminder(application)
```

---

### **🟡 PRIORITY 2 - IMPORTANT (Do Second)**

#### 5. **Admin Management Endpoints** ⚠️ ADMIN PANEL
**Status**: Not Started  
**What's Needed**:
- [ ] User management (create/edit/delete users)
- [ ] Role assignment endpoints
- [ ] Laboratory/Department management
- [ ] System settings management

**Files to Create**:
- `services/admin/admin_service.py`
- `endpoints/admin.py` (comprehensive)

**Endpoints Needed**:
```
POST /api/v1/admin/users
    → Create new user (admin, assistant, super-admin)
    
PUT /api/v1/admin/users/{id}
    → Update user role/grade
    
DELETE /api/v1/admin/users/{id}
    → Delete user

GET /api/v1/admin/laboratories
    → List all labs
    
POST /api/v1/admin/laboratories
    → Create/update laboratory
```

---

#### 6. **Dashboard & Statistics** ⚠️ REPORTING
**Status**: Empty skeleton  
**What's Needed**:
- [ ] Researcher dashboard (my applications status)
- [ ] Admin dashboard (all applications, statistics)
- [ ] CS dashboard with scores and recommendations
- [ ] Real-time statistics

**Files to Create/Update**:
- `services/dashboard/dashboard_service.py`
- `endpoints/dashboard.py`

**Endpoints Needed**:
```
GET /api/v1/dashboard/researcher
    → My applications, status, alerts

GET /api/v1/dashboard/admin
    → All applications, statistics, pending actions

GET /api/v1/dashboard/cs
    → Ready applications, scores, recommendations

GET /api/v1/statistics
    → Overall stats: total applications, approvals, funding
```

---

#### 7. **Cancellation & Modifications** ⚠️ WORKFLOW
**Status**: Model fields exist, no endpoints  
**What's Needed**:
- [ ] Request cancellation endpoint
- [ ] Admin approval of cancellation
- [ ] Cancellation notifications
- [ ] Resubmit rejected application

**Endpoints Needed**:
```
POST /api/v1/applications/{id}/request-cancellation
    → Request to cancel (provide reason)

POST /api/v1/admin/applications/{id}/approve-cancellation
    → Admin approves cancellation

POST /api/v1/applications/{id}/resubmit
    → Resubmit a rejected application
```

---

#### 8. **Search & Advanced Filtering** ⚠️ USABILITY
**Status**: Basic filters done, needs enhancement  
**What's Needed**:
- [ ] Full-text search across all fields
- [ ] Save filters as favorites
- [ ] Export application list (Excel/CSV)
- [ ] Batch operations (download docs, send reminders)

**Endpoints Needed**:
```
GET /api/v1/applications/search
    → Advanced search with multiple criteria

POST /api/v1/applications/bulk-download-documents
    → Download all docs for multiple applications

POST /api/v1/applications/bulk-export
    → Export selected applications to Excel
```

---

### **🟢 PRIORITY 3 - NICE TO HAVE (Do Third)**

#### 9. **Attestation & Certificate Generation** ⚠️
- [ ] Generate PDF attestations for approved applications
- [ ] Certificate templates
- [ ] Download attestations

**Files to Create**:
- `services/document/pdf_service.py`
- `endpoints/attestations.py`

---

#### 10. **Publications & Impact Tracking** ⚠️
- [ ] Track publications from stages/séjours
- [ ] Link publications to applications
- [ ] Impact statistics

**Files to Create**:
- `services/application/publication_service.py`

---

#### 11. **Session Management** ⚠️
- [ ] Create/manage call sessions (open/close)
- [ ] Session-specific criteria configuration
- [ ] Session statistics

**Files to Create**:
- `services/admin/session_service.py`

---

#### 12. **Audit & Compliance** ⚠️
- [ ] Complete activity logging
- [ ] Audit trail for all actions
- [ ] Compliance reports

**Files to Create**:
- `services/audit/audit_service.py`

---

## 📊 IMPLEMENTATION PRIORITY ORDER

```
Week 1:  CS Workflow + Fees Calculation + Reports
Week 2:  Notifications + Admin Panel
Week 3:  Dashboard + Cancellations + Advanced Filtering
Week 4:  Attestations + Publications + Testing
```

---

## 🎯 NEXT IMMEDIATE STEPS (ACCURATE PRIORITIES)

### **Step 1: CS Workflow** (CRITICAL - Do First)
The **core blocker** - applications stuck after eligibility check, need CS deliberation to proceed

**Files to Create**:
- `services/admin/cs_service.py` - CS decision logic
- `endpoints/cs.py` - CS deliberation endpoints

**What to code**:
```python
# endpoints/cs.py endpoints needed:
POST /api/v1/cs/deliberate/{application_id}
    → Input: {decision: "approuve"|"rejete", notes: "..."}
    → Update Application.cs_decision
    → Trigger fee calculation if approved
    → Update status to APPROVED or REJECTED
    → Send notification to user

GET /api/v1/cs/dashboard
    → List all CS_PREPARATION applications
    → Show scores and sorting recommendations
```

---

### **Step 2: Report Submission** (HIGH - Do Second)
Users can't close applications without submitting final reports

**Files to Create**:
- `endpoints/reports.py` - Report submission endpoints

**What to code**:
```python
# endpoints/reports.py endpoints needed:
POST /api/v1/applications/{id}/submit-report
    → Upload PDF file
    → Validation: must be PDF, non-empty
    → Update Application.stage_report_path
    → Status: APPROVED → COMPLETED

GET /api/v1/applications/{id}/report
    → Download submitted report
```

---

### **Step 3: Dashboard** (IMPORTANT - Do Third)
Users/admins/CS need visibility into applications

**Files to Create**:
- `services/dashboard/dashboard_service.py` - Query logic
- `endpoints/dashboard.py` - Dashboard endpoints

**What to code**:
```python
# endpoints/dashboard.py endpoints needed:
GET /api/v1/dashboard/researcher
    → My applications grouped by status
    → Alert if pending actions

GET /api/v1/dashboard/cs
    → Ready applications (CS_PREPARATION)
    → Sorted by score (highest first)
    → Show eligibility issues

GET /api/v1/dashboard/admin
    → All applications by status
    → Statistics: total/approved/rejected
    → Search/filter
```

---

## 📝 Summary Table

| Feature | Priority | Complexity | Time Est. | Status |
|---------|----------|-----------|----------|--------|
| CS Workflow | 🔴 HIGH | High | 4-6h | ❌ Not Started |
| Report Submission | 🔴 HIGH | Medium | 2-3h | ❌ Not Started |
| Dashboard | 🟡 MEDIUM | High | 4-5h | ❌ Not Started |
| Email Service | 🟡 MEDIUM | Medium | 2-3h | ❌ Not Started |
| Notifications (Email) | 🟡 MEDIUM | Medium | 3-4h | 🟡 Partial |
| Admin Panel | 🟡 MEDIUM | High | 4-5h | ❌ Not Started |
| Cancellations | 🟡 MEDIUM | Low | 2h | ❌ Not Started |
| Publications | 🟢 LOW | Medium | 2h | ❌ Not Started |
| Settings Management | 🟢 LOW | Low | 1-2h | ❌ Not Started |
| Fees/Indemnity | ✅ DONE | N/A | 0h | ✅ COMPLETE |
| Attestations | 🟢 LOW | Medium | 2-3h | ❌ Not Started |

---

## 🚀 Total Estimated Work

- **🔴 PRIORITY 1**: ~6-9 hours (CS Workflow + Report Submission)
- **🟡 PRIORITY 2**: ~13-17 hours (Dashboard + Email + Notifications + Admin)
- **🟢 PRIORITY 3**: ~5-7 hours (Publications + Settings + Attestations)

**Total**: ~24-33 hours remaining (~3-4 days intensive)

---

**Recommendation**: Start with Priority 1 this week. Those are the absolutely essential workflow components that make the system functional.
