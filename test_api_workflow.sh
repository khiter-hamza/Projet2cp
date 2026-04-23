#!/bin/bash
# Complete API Workflow Testing - Bash Script with curl
# This script demonstrates the complete workflow using curl commands

set -e  # Exit on error

BASE_URL="http://localhost:8000/api/v1"
TEMP_DIR="/tmp/api_test_$$"
mkdir -p "$TEMP_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper function to print colored output
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Test authentication endpoint
print_header "PHASE 1: AUTHENTICATION"

print_info "Registering researcher user..."
RESEARCHER_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/register" \
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
  }')

RESEARCHER_ID=$(echo "$RESEARCHER_RESPONSE" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)
if [ -z "$RESEARCHER_ID" ]; then
    print_error "Failed to register researcher"
    echo "$RESEARCHER_RESPONSE" | jq '.' 2>/dev/null || echo "$RESEARCHER_RESPONSE"
    RESEARCHER_ID=$(echo "$RESEARCHER_RESPONSE" | jq -r '.id' 2>/dev/null)
fi
print_success "Researcher registered: $RESEARCHER_ID"

print_info "Registering admin user..."
ADMIN_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@test.com",
    "username": "admin_user",
    "lastname": "Admin",
    "password": "AdminPassword123!",
    "role": "admin_dpgr",
    "grade": "professeur",
    "anciente": 10,
    "laboratory_name": "Admin_Lab"
  }')

ADMIN_ID=$(echo "$ADMIN_RESPONSE" | jq -r '.id' 2>/dev/null)
print_success "Admin registered: $ADMIN_ID"

print_info "Logging in as researcher..."
RESEARCHER_LOGIN=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "researcher@test.com",
    "password": "TestPassword123!"
  }')

RESEARCHER_TOKEN=$(echo "$RESEARCHER_LOGIN" | jq -r '.access_token' 2>/dev/null)
if [ "$RESEARCHER_TOKEN" = "null" ] || [ -z "$RESEARCHER_TOKEN" ]; then
    print_error "Failed to login as researcher"
    echo "$RESEARCHER_LOGIN" | jq '.'
    exit 1
fi
print_success "Researcher logged in"
echo "Token: ${RESEARCHER_TOKEN:0:50}..."

print_info "Logging in as admin..."
ADMIN_LOGIN=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@test.com",
    "password": "AdminPassword123!"
  }')

ADMIN_TOKEN=$(echo "$ADMIN_LOGIN" | jq -r '.access_token' 2>/dev/null)
if [ "$ADMIN_TOKEN" = "null" ] || [ -z "$ADMIN_TOKEN" ]; then
    print_error "Failed to login as admin"
    exit 1
fi
print_success "Admin logged in"

# Session Management
print_header "PHASE 2: SESSION MANAGEMENT"

print_info "Checking for active session..."
ACTIVE_SESSION=$(curl -s -X GET "$BASE_URL/sessions/active")
SESSION_ID=$(echo "$ACTIVE_SESSION" | jq -r '.id' 2>/dev/null)

if [ "$SESSION_ID" = "null" ] || [ -z "$SESSION_ID" ]; then
    print_info "No active session found. Creating new session..."
    
    START_DATE=$(date -d "+1 day" +%Y-%m-%d)
    END_DATE=$(date -d "+120 days" +%Y-%m-%d)
    
    SESSION_RESPONSE=$(curl -s -X POST "$BASE_URL/sessions/" \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer $ADMIN_TOKEN" \
      -d "{
        \"name\": \"2024-2025 Academic Year\",
        \"academic_year\": \"2024-2025\",
        \"start_date\": \"$START_DATE\",
        \"end_date\": \"$END_DATE\"
      }")
    
    SESSION_ID=$(echo "$SESSION_RESPONSE" | jq -r '.id' 2>/dev/null)
    print_success "Session created: $SESSION_ID"
else
    print_success "Active session found: $SESSION_ID"
    echo "$ACTIVE_SESSION" | jq '.'
fi

# Application Creation
print_header "PHASE 3: APPLICATION CREATION & MANAGEMENT"

print_info "Creating draft application..."
APP_RESPONSE=$(curl -s -X POST "$BASE_URL/applications/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $RESEARCHER_TOKEN" \
  -d '{
    "destination_country": "france",
    "destination_city": "Paris",
    "host_institution": "University of Paris",
    "scientific_objective": "Research on AI and machine learning",
    "start_date": "'$(date -d '+1 day' +%Y-%m-%d)'",
    "end_date": "'$(date -d '+31 days' +%Y-%m-%d)'"
  }')

APP_ID=$(echo "$APP_RESPONSE" | jq -r '.id' 2>/dev/null)
if [ "$APP_ID" = "null" ] || [ -z "$APP_ID" ]; then
    print_error "Failed to create application"
    echo "$APP_RESPONSE" | jq '.'
    exit 1
fi
print_success "Draft application created: $APP_ID"

print_info "Updating draft application..."
curl -s -X PATCH "$BASE_URL/applications/$APP_ID" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $RESEARCHER_TOKEN" \
  -d '{
    "destination_country": "france",
    "destination_city": "Lyon",
    "host_institution": "Claude Bernard University",
    "scientific_objective": "Advanced research on distributed systems"
  }' | jq '.'
print_success "Application updated"

print_info "Retrieving application details..."
curl -s -X GET "$BASE_URL/applications/$APP_ID" \
  -H "Authorization: Bearer $RESEARCHER_TOKEN" | jq '.'
print_success "Application details retrieved"

print_info "Listing all applications..."
curl -s -X GET "$BASE_URL/applications/" \
  -H "Authorization: Bearer $RESEARCHER_TOKEN" | jq '.'
print_success "Applications listed"

# Document Management
print_header "PHASE 4: DOCUMENT MANAGEMENT"

print_info "Creating test document..."
TEST_DOC="$TEMP_DIR/test_document.txt"
echo "This is a test document for API testing purposes." > "$TEST_DOC"
print_success "Test document created: $TEST_DOC"

print_info "Uploading document..."
UPLOAD_RESPONSE=$(curl -s -X POST "$BASE_URL/applications/$APP_ID/documents" \
  -H "Authorization: Bearer $RESEARCHER_TOKEN" \
  -F "file=@$TEST_DOC" \
  -F "document_type=cv")

DOC_ID=$(echo "$UPLOAD_RESPONSE" | jq -r '.id' 2>/dev/null)
print_success "Document uploaded: $DOC_ID"
echo "$UPLOAD_RESPONSE" | jq '.'

print_info "Getting documents..."
curl -s -X GET "$BASE_URL/applications/$APP_ID/documents" \
  -H "Authorization: Bearer $RESEARCHER_TOKEN" | jq '.'
print_success "Documents retrieved"

# Eligibility & Evaluation
print_header "PHASE 5: ELIGIBILITY & EVALUATION"

print_info "Checking eligibility..."
curl -s -X POST "$BASE_URL/applications/$APP_ID/check-eligibility" \
  -H "Authorization: Bearer $RESEARCHER_TOKEN" | jq '.'
print_success "Eligibility check completed"

print_info "Getting eligibility details..."
curl -s -X GET "$BASE_URL/applications/$APP_ID/eligibility-details" \
  -H "Authorization: Bearer $RESEARCHER_TOKEN" | jq '.'
print_success "Eligibility details retrieved"

print_info "Getting user score..."
curl -s -X GET "$BASE_URL/evaluation/users/$RESEARCHER_ID/score" \
  -H "Authorization: Bearer $RESEARCHER_TOKEN" | jq '.'
print_success "User score retrieved"

# Application Submission
print_header "PHASE 6: APPLICATION SUBMISSION"

print_info "Submitting application..."
SUBMIT_RESPONSE=$(curl -s -X POST "$BASE_URL/applications/$APP_ID/submit" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $RESEARCHER_TOKEN" \
  -d '{
    "destination_country": "france",
    "destination_city": "Lyon",
    "host_institution": "Claude Bernard University",
    "scientific_objective": "Advanced research on distributed systems"
  }')

print_success "Application submitted"
echo "$SUBMIT_RESPONSE" | jq '.'

# History & Tracking
print_header "PHASE 7: HISTORY & TRACKING"

print_info "Getting application history..."
curl -s -X GET "$BASE_URL/applications/$APP_ID/history?limit=50&offset=0" \
  -H "Authorization: Bearer $RESEARCHER_TOKEN" | jq '.'
print_success "Application history retrieved"

print_info "Getting history page..."
curl -s -X GET "$BASE_URL/applications/history?limit=10&offset=0&sort_by=submitted_at&sort_order=desc&session_filter=this" \
  -H "Authorization: Bearer $RESEARCHER_TOKEN" | jq '.'
print_success "History page retrieved"

# CS Workflow (Admin)
print_header "PHASE 8: CS WORKFLOW (Admin Operations)"

print_info "Preparing CS deliberation..."
curl -s -X POST "$BASE_URL/cs/prepare-deliberation/$SESSION_ID" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq '.'
print_success "CS deliberation prepared"

print_info "Getting CS dashboard..."
curl -s -X GET "$BASE_URL/cs/dashboard?session_id=$SESSION_ID" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq '.'
print_success "CS dashboard retrieved"

# Cleanup
print_header "CLEANUP"
rm -rf "$TEMP_DIR"
print_success "Temporary files cleaned up"

# Summary
print_header "WORKFLOW COMPLETED SUCCESSFULLY"
echo "Key IDs for reference:"
echo "  Researcher User ID: $RESEARCHER_ID"
echo "  Admin User ID: $ADMIN_ID"
echo "  Session ID: $SESSION_ID"
echo "  Application ID: $APP_ID"
echo "  Document ID: $DOC_ID"
echo ""
echo "You can now use these IDs to make additional API calls or test other endpoints."
