# API Workflow Testing Scripts

This directory contains comprehensive scripts to test the complete API workflow for the Projet 2CP application. The workflow respects the proper order of API calls and handles authentication, application lifecycle, document management, and CS decision-making.

## Overview of the Workflow

The complete workflow follows these phases:

1. **Authentication** - Register and login users (researcher and admin)
2. **Session Management** - Create or get active session
3. **Application Creation** - Create and manage draft applications
4. **Document Management** - Upload and retrieve documents
5. **Eligibility & Evaluation** - Check eligibility and calculate scores
6. **Application Submission** - Submit applications for review
7. **History & Tracking** - View application history and events
8. **CS Workflow** - Admin operations for CS decision-making

## Available Scripts

### 1. Python Script (`test_api_workflow.py`)

**Best for**: Complex testing, automation, detailed logging

**Features**:
- Fully async/await implementation
- Comprehensive error handling
- Detailed logging and output
- Type hints and documentation
- Easy to extend and customize

**Requirements**:
```bash
pip install httpx
```

**Usage**:
```bash
python test_api_workflow.py
```

**Output**:
- Structured logs for each phase
- Success/failure indicators
- Key IDs printed at the end for reference
- Example:
  ```
  [1. REGISTER] Creating user: researcher@test.com
  ✓ User registered: {'id': '...', 'username': '...', ...}
  [2. LOGIN] Authenticating user: researcher@test.com
  ✓ Login successful
    Token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
  ```

### 2. Bash Script (`test_api_workflow.sh`)

**Best for**: Quick testing, CI/CD pipelines, shell environments

**Features**:
- Pure bash with curl commands
- Colored output for easy reading
- Works on any Unix-like system
- No Python dependencies
- Automatic cleanup of temporary files

**Requirements**:
- `curl`
- `jq` (for JSON parsing)
- `bash`

**Installation on Linux**:
```bash
sudo apt-get install curl jq
```

**Usage**:
```bash
chmod +x test_api_workflow.sh
./test_api_workflow.sh
```

**Output**:
- Colored output (green for success, red for error, yellow for info)
- Each API response formatted as JSON
- Temporary files automatically cleaned up

## API Endpoints Reference

### Authentication Endpoints
```
POST /api/v1/auth/register     - Register a new user
POST /api/v1/auth/login        - Login and get JWT token
```

### Session Endpoints
```
POST   /api/v1/sessions/         - Create new session (Admin only)
GET    /api/v1/sessions/         - List all sessions (Admin only)
GET    /api/v1/sessions/active   - Get current active session
GET    /api/v1/sessions/{id}     - Get specific session
```

### Application Endpoints
```
POST   /api/v1/applications/                   - Create draft application
GET    /api/v1/applications/                   - List user applications
GET    /api/v1/applications/{id}               - Get application details
PATCH  /api/v1/applications/{id}               - Update draft application
POST   /api/v1/applications/{id}/submit        - Submit application
POST   /api/v1/applications/{id}/cancel        - Cancel application
DELETE /api/v1/applications/{id}               - Delete draft
```

### Document Endpoints
```
POST /api/v1/applications/{id}/documents     - Upload document
GET  /api/v1/applications/{id}/documments    - Get documents
DELETE /api/v1/document/{id}                 - Delete document
```

### Eligibility Endpoints
```
POST /api/v1/applications/{id}/check-eligibility     - Check eligibility
GET  /api/v1/applications/{id}/eligibility-details   - Get details
```

### Evaluation Endpoints
```
GET /api/v1/evaluation/users/{user_id}/score          - Get user score
GET /api/v1/evaluation/applications/{app_id}/score    - Get app score
```

### History Endpoints
```
GET /api/v1/applications/{id}/history      - Get application history
GET /api/v1/applications/history            - Get paginated history
```

### CS Workflow Endpoints
```
POST /api/v1/cs/prepare-deliberation/{session_id}     - Prepare deliberation
GET  /api/v1/cs/dashboard                              - Get CS dashboard
POST /api/v1/cs/applications/{id}/approve              - Approve application
POST /api/v1/cs/applications/{id}/reject               - Reject application
GET  /api/v1/cs/decision-history                       - Get decision history
```

## Example Request/Response Flows

### Register User
```bash
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "researcher@test.com",
  "username": "researcher_user",
  "lastname": "Test",
  "password": "TestPassword123!",
  "role": "researcher",
  "grade": "Professor",
  "anciente": 5,
  "laboratory_name": "Lab1"
}

Response:
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "researcher_user",
  "lastname": "Test",
  "email": "researcher@test.com"
}
```

### Login User
```bash
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "researcher@test.com",
  "password": "TestPassword123!"
}

Response:
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### Create Application
```bash
POST /api/v1/applications/
Authorization: Bearer <token>
Content-Type: application/json

{
  "destination_country": "france",
  "destination_city": "Paris",
  "host_institution": "University of Paris",
  "scientific_objective": "Research on AI",
  "start_date": "2024-02-15",
  "end_date": "2024-03-15"
}

Response:
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "DRAFT",
  "destination_country": "france",
  "destination_city": "Paris",
  "host_institution": "University of Paris",
  "scientific_objective": "Research on AI",
  "start_date": "2024-02-15T00:00:00",
  "end_date": "2024-03-15T00:00:00",
  "is_eligible": null,
  "cs_decision": null,
  "created_at": "2024-02-01T10:30:00",
  "submitted_at": null,
  "documents": []
}
```

### Submit Application
```bash
POST /api/v1/applications/{app_id}/submit
Authorization: Bearer <token>
Content-Type: application/json

{
  "destination_country": "france",
  "destination_city": "Paris",
  "host_institution": "University of Paris",
  "scientific_objective": "Research on AI"
}

Response:
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "status": "SUBMITTED",
  "submitted_at": "2024-02-01T10:35:00",
  ...
}
```

### Upload Document
```bash
POST /api/v1/applications/{app_id}/documents
Authorization: Bearer <token>

Form Data:
- file: (binary file content)
- document_type: "cv"

Response:
{
  "id": "770e8400-e29b-41d4-a716-446655440002",
  "application_id": "660e8400-e29b-41d4-a716-446655440001",
  "document_type": "cv",
  "file_name": "my_cv.pdf",
  "file_path": "uploads/documents/660e8400-e29b-41d4-a716-446655440001/uuid.pdf",
  "file_size": 1024000,
  "mime_type": "application/pdf",
  "uploaded_at": "2024-02-01T10:36:00"
}
```

### Check Eligibility
```bash
POST /api/v1/applications/{app_id}/check-eligibility
Authorization: Bearer <token>

Response:
{
  "application_id": "660e8400-e29b-41d4-a716-446655440001",
  "is_eligible": true,
  "errors": [],
  "checked_at": "2024-02-01T10:37:00"
}
```

### Get History
```bash
GET /api/v1/applications/{app_id}/history?limit=50&offset=0
Authorization: Bearer <token>

Response:
{
  "total": 5,
  "items": [
    {
      "id": "880e8400-e29b-41d4-a716-446655440003",
      "application_id": "660e8400-e29b-41d4-a716-446655440001",
      "event_type": "SUBMITTED",
      "timestamp": "2024-02-01T10:35:00",
      "details": {"reason": "User submitted application"}
    },
    {
      "id": "880e8400-e29b-41d4-a716-446655440004",
      "application_id": "660e8400-e29b-41d4-a716-446655440001",
      "event_type": "ELIGIBILITY_CHECKED",
      "timestamp": "2024-02-01T10:37:00",
      "details": {"result": "eligible"}
    }
  ]
}
```

## Usage Examples

### Run Complete Workflow with Python
```bash
# Install dependencies
pip install httpx

# Run the script
python test_api_workflow.py
```

### Run Complete Workflow with Bash
```bash
# Make executable
chmod +x test_api_workflow.sh

# Run the script
./test_api_workflow.sh
```

### Test Individual Endpoints with curl

**Login**:
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "researcher@test.com",
    "password": "TestPassword123!"
  }' | jq
```

**Get Active Session**:
```bash
curl -X GET http://localhost:8000/api/v1/sessions/active | jq
```

**Create Application**:
```bash
TOKEN="your_jwt_token_here"
curl -X POST http://localhost:8000/api/v1/applications/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "destination_country": "FR",
    "destination_city": "Paris",
    "host_institution": "University of Paris",
    "scientific_objective": "Research on AI",
    "start_date": "2024-02-15",
    "end_date": "2024-03-15"
  }' | jq
```

**Upload Document**:
```bash
TOKEN="your_jwt_token_here"
APP_ID="application_id_here"
curl -X POST http://localhost:8000/api/v1/applications/$APP_ID/documents \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/path/to/document.pdf" \
  -F "document_type=cv" | jq
```

## Troubleshooting

### "No active session found"
The API requires an active session to submit applications. You can:
1. Create a session using admin credentials:
```bash
curl -X POST http://localhost:8000/api/v1/sessions/ \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "2024-2025",
    "academic_year": "2024-2025",
    "start_date": "2024-02-01",
    "end_date": "2024-06-30"
  }' | jq
```

### "Not authorized"
Ensure you have the correct role for the operation:
- `admin_dpgr` - Can create sessions and make CS decisions
- `researcher` - Can submit applications
- Other roles may have specific permissions

### "Eligibility check failed"
Make sure:
1. Application is in correct status (usually after submission)
2. Required documents are uploaded
3. User meets grade and seniority requirements

### CORS Issues
If you're calling from a browser, ensure CORS is properly configured in the FastAPI settings.

## Performance Tips

1. **Batch operations**: Reuse the same HTTP client connection when possible
2. **Async operations**: The Python script uses async/await for better performance
3. **Pagination**: Use limit and offset for large result sets
4. **Document uploads**: Consider file size limits and upload timeouts

## Security Notes

⚠️ **Never commit credentials to version control**
- These scripts contain test credentials for demonstration
- In production, use environment variables or secure credential management
- Rotate tokens regularly
- Use HTTPS in production

## API Documentation

Access the interactive Swagger UI documentation:
```
http://localhost:8000/docs
```

Or ReDoc:
```
http://localhost:8000/redoc
```

## Contributing

To add new test cases:
1. Create a new function in the appropriate script
2. Follow the existing naming convention
3. Add appropriate error handling
4. Update this README with any new endpoints

## Support

For issues or questions:
1. Check that the API server is running on `http://localhost:8000`
2. Review the API logs for error details
3. Verify user credentials and permissions
4. Test individual endpoints with curl first
