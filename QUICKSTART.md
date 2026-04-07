# Projet 2CP API - Quick Start Guide

This guide helps you quickly test the complete Projet 2CP API workflow with example requests and proper workflow ordering.

## 📋 Workflow Overview

The API follows this defined workflow:

```
Register/Login → Session → Create Draft → Update → Upload Docs → Eligibility → Submit → History → CS Decision
```

## 🚀 Quick Start (Choose One Method)

### Option 1: Run Python Script (Recommended for Full Automation)

**Best for**: Running the complete workflow automatically with detailed logging

```bash
# Install dependencies
pip install httpx

# Run the complete workflow
python test_api_workflow.py
```

**Output shows**:
✓ User registration and login
✓ Session creation/retrieval
✓ Application creation and updates
✓ Document uploads
✓ Eligibility checks
✓ Application submission
✓ History tracking
✓ CS operations (for admin users)

### Option 2: Run Bash Script (No Python Required)

**Best for**: Simple shell environment, CI/CD pipelines

```bash
# Make executable
chmod +x test_api_workflow.sh

# Run the complete workflow
./test_api_workflow.sh
```

**Requirements**:
- `bash`
- `curl`
- `jq` (for JSON parsing)

### Option 3: Use Postman Collection (Interactive Testing)

**Best for**: Manual testing, learning, and exploring endpoints

1. **Import the collection**:
   - Open Postman
   - Click "Import"
   - Select `Projet2CP_API.postman_collection.json`
   - Choose your workspace

2. **Set environment variables**:
   - Create new environment in Postman
   - Set `base_url` = `http://localhost:8000/api/v1`
   - Leave other variables empty (they auto-populate after login)

3. **Follow the workflow**:
   - Start with "Authentication" folder
   - Run "Login Researcher" (sets token automatically)
   - Run "Login Admin" (sets admin token automatically)
   - Continue through each folder in order

### Option 4: Manual curl Commands

**Best for**: Quick testing of individual endpoints

See API_WORKFLOW_GUIDE.md for detailed curl examples.

## 📊 Complete Workflow Steps

### Step 1: Authentication
```bash
# Register users
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "researcher@test.com",
    "username": "researcher_user",
    "lastname": "Test",
    "password": "TestPassword123!",
    "role": "chercheur",
    "grade": "professeur",
    "anciente": 5,
    "laboratory_name": "Lab1"
  }'

# Login to get token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "researcher@test.com",
    "password": "TestPassword123!"
  }'

# Response includes access_token - save this!
```

### Step 2: Session Management
```bash
TOKEN="your_access_token_here"

# Check active session
curl -X GET http://localhost:8000/api/v1/sessions/active

# If no session, create one (admin only)
curl -X POST http://localhost:8000/api/v1/sessions/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "2024-2025",
    "academic_year": "2024-2025",
    "start_date": "2024-02-01",
    "end_date": "2024-06-30"
  }'
```

### Step 3: Create Application
```bash
TOKEN="your_access_token_here"

curl -X POST http://localhost:8000/api/v1/applications/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "destination_country": "france",
    "destination_city": "Paris",
    "host_institution": "University of Paris",
    "scientific_objective": "Research on AI",
    "start_date": "2024-02-20",
    "end_date": "2024-03-20"
  }'

# Save the returned application ID
```

### Step 4: Update Draft
```bash
TOKEN="your_access_token_here"
APP_ID="application_id_from_step_3"

curl -X PATCH http://localhost:8000/api/v1/applications/$APP_ID \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "destination_city": "Lyon",
    "host_institution": "Claude Bernard University",
    "scientific_objective": "Advanced research"
  }'
```

### Step 5: Upload Documents
```bash
TOKEN="your_access_token_here"
APP_ID="application_id"

# Create test document
echo "Test document content" > test.txt

# Upload
curl -X POST http://localhost:8000/api/v1/applications/$APP_ID/documents \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test.txt" \
  -F "document_type=cv"

# Supported document types:
# - cv
# - motivation_letter
# - publication
# - report
```

### Step 6: Check Eligibility
```bash
TOKEN="your_access_token_here"
APP_ID="application_id"

curl -X POST http://localhost:8000/api/v1/applications/$APP_ID/check-eligibility \
  -H "Authorization: Bearer $TOKEN"

# Response:
# {
#   "is_eligible": true,
#   "errors": [],
#   "checked_at": "2024-02-01T10:37:00"
# }
```

### Step 7: Submit Application
```bash
TOKEN="your_access_token_here"
APP_ID="application_id"

curl -X POST http://localhost:8000/api/v1/applications/$APP_ID/submit \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "destination_country": "FR",
    "destination_city": "Lyon",
    "host_institution": "Claude Bernard University",
    "scientific_objective": "Advanced research"
  }'

# Application status changes from DRAFT to SUBMITTED
```

### Step 8: Get History
```bash
TOKEN="your_access_token_here"
APP_ID="application_id"

# Get history for specific application
curl -X GET "http://localhost:8000/api/v1/applications/$APP_ID/history?limit=50&offset=0" \
  -H "Authorization: Bearer $TOKEN"

# Get paginated history for all applications
curl -X GET "http://localhost:8000/api/v1/applications/history?limit=10&offset=0&sort_by=submitted_at" \
  -H "Authorization: Bearer $TOKEN"
```

### Step 9: CS Operations (Admin Only)
```bash
ADMIN_TOKEN="admin_access_token"
SESSION_ID="session_id"

# Prepare CS deliberation
curl -X POST http://localhost:8000/api/v1/cs/prepare-deliberation/$SESSION_ID \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Get CS dashboard
curl -X GET http://localhost:8000/api/v1/cs/dashboard?session_id=$SESSION_ID \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Approve application
curl -X POST http://localhost:8000/api/v1/cs/applications/$APP_ID/approve \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}'

# Reject application
curl -X POST http://localhost:8000/api/v1/cs/applications/$APP_ID/reject \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"reason": "Insufficient credentials"}'
```

## 🔐 Test Credentials

**Researcher Account**:
- Email: `researcher@test.com`
- Password: `TestPassword123!`
- Role: `chercheur`
- Grade: `professeur`

**Admin Account**:
- Email: `admin@test.com`
- Password: `AdminPassword123!`
- Role: `admin_dpgr`
- Grade: `professeur`

## 📱 API Response Examples

### Success Response (200/201)
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "SUBMITTED",
  "destination_country": "FR",
  "is_eligible": true,
  "created_at": "2024-02-01T10:30:00",
  "submitted_at": "2024-02-01T10:35:00"
}
```

### Error Response (4xx/5xx)
```json
{
  "detail": "Not authorized"
}
```

Or detailed:
```json
{
  "detail": "Eligibility check failed: Required documents missing"
}
```

## 🐛 Common Issues & Solutions

### Issue: "No active session found"
**Solution**: Create a session first (admin only)
```bash
curl -X POST http://localhost:8000/api/v1/sessions/ \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{...}'
```

### Issue: "Not authorized" on session operations
**Solution**: Use admin account (role = admin_dpgr)

### Issue: "Application not found"
**Solution**: Verify application ID and ensure you're the owner

### Issue: "Document upload failed"
**Solution**: Check file size and format

### Issue: Token expired
**Solution**: Login again and get new token

### Issue: "Eligibility check failed"
**Solution**: Ensure required documents are uploaded and user meets grade requirements

## 📚 Additional Resources

- **Interactive API Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Detailed Guide**: See `API_WORKFLOW_GUIDE.md`
- **Postman Collection**: `Projet2CP_API.postman_collection.json`

## 🔍 Debugging

### Check Server Status
```bash
curl http://localhost:8000/api/v1/health
# Should return: {"status": "ok"}
```

### View API Logs
```bash
# If running with Docker
docker logs projet2cp_container_name

# If running locally with uvicorn
# Check terminal where you started the server
```

### Test Token Validity
```bash
TOKEN="your_token"
curl -X GET http://localhost:8000/api/v1/applications/ \
  -H "Authorization: Bearer $TOKEN"
# If invalid: {"detail": "Not authenticated"}
```

## 📝 Workflow State Diagram

```
┌─────────────┐
│   CREATED   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│    DRAFT    │ ◄─── Update allowed here
└──────┬──────┘
       │ Submit
       ▼
┌─────────────────────┐
│    SUBMITTED        │ ◄─── Eligibility checked here
└──────┬──────────────┘
       │
       ├─ ELIGIBLE ──┐
       │             ▼
       │        ┌──────────────┐
       │        │ CS_PREP      │ ◄─── Admin reviews
       │        └──────┬───────┘
       │               │
       │         ┌─────┴─────┐
       │         │           │
       │         ▼           ▼
       │    APPROVED    REJECTED
       │
       └─ NOT_ELIGIBLE ──→ REJECTED
```

## 🚀 Next Steps

1. **Run the workflow**:
   - Choose Python, Bash, or Postman
   - Follow the steps in order

2. **Explore the API**:
   - Check http://localhost:8000/docs for all endpoints
   - Try individual requests with curl

3. **Customize**:
   - Modify test data
   - Add more test cases
   - Integrate with your frontend

## 💡 Tips

- **Always login first** to get a valid token
- **Save IDs returned** by create operations for subsequent calls
- **Use environment variables** to manage tokens and IDs
- **Test one endpoint at a time** before running full workflow
- **Check error messages** for detailed debugging info
- **Use swagger UI** to see live API documentation

## 📞 Support

For issues:
1. Check that API is running: `curl http://localhost:8000/api/v1/health`
2. Verify token is valid
3. Check user role permissions
4. Review API logs for server errors
5. See `API_WORKFLOW_GUIDE.md` for more examples
