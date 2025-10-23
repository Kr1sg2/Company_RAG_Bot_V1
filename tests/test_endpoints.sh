#!/bin/bash
set -e

# Test endpoints for Lexa AI settings system
# Usage: ./test_endpoints.sh [base_url] [admin_password]

BASE_URL=${1:-"http://localhost:8000"}
ADMIN_PASSWORD=${2:-"${ADMIN_PASSWORD:-Krypt0n!t3}"}
ADMIN_USER="admin"

echo "🧪 Testing Lexa AI Settings API"
echo "📍 Base URL: $BASE_URL"
echo "👤 Admin user: $ADMIN_USER"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper function to make authenticated requests
auth_curl() {
    curl -s -u "$ADMIN_USER:$ADMIN_PASSWORD" "$@"
}

# Helper function to test an endpoint
test_endpoint() {
    local method=$1
    local endpoint=$2
    local description=$3
    local data=$4
    local expected_status=${5:-200}
    
    echo -e "${BLUE}Testing:${NC} $method $endpoint - $description"
    
    if [[ $method == "GET" ]]; then
        response=$(auth_curl -w "\n%{http_code}" "$BASE_URL$endpoint")
    elif [[ $method == "POST" ]]; then
        response=$(auth_curl -X POST -H "Content-Type: application/json" -d "$data" -w "\n%{http_code}" "$BASE_URL$endpoint")
    elif [[ $method == "PUT" ]]; then
        response=$(auth_curl -X PUT -H "Content-Type: application/json" -d "$data" -w "\n%{http_code}" "$BASE_URL$endpoint")
    else
        echo -e "${RED}❌ Unknown method: $method${NC}"
        return 1
    fi
    
    # Extract status code (last line)
    status_code=$(echo "$response" | tail -n1)
    # Extract body (all lines except last)
    body=$(echo "$response" | head -n -1)
    
    if [[ $status_code == $expected_status ]]; then
        echo -e "${GREEN}✅ $status_code${NC} - Success"
        if [[ ${#body} -gt 100 ]]; then
            echo "📄 Response: ${body:0:100}..."
        else
            echo "📄 Response: $body"
        fi
    else
        echo -e "${RED}❌ $status_code${NC} - Expected $expected_status"
        echo "📄 Response: $body"
        return 1
    fi
    echo ""
}

# Test basic health check
echo -e "${YELLOW}=== Health Check ===${NC}"
test_endpoint "GET" "/health" "Health check"

# Test authentication endpoints
echo -e "${YELLOW}=== Authentication ===${NC}"
test_endpoint "POST" "/auth/login" "Admin login" "{\"username\":\"$ADMIN_USER\",\"password\":\"$ADMIN_PASSWORD\"}"

# Test public settings (no auth required)
echo -e "${YELLOW}=== Public Settings ===${NC}"
test_endpoint "GET" "/admin/settings?public=true" "Public settings (no auth)" "" 200

# Test protected settings endpoints
echo -e "${YELLOW}=== Protected Settings Endpoints ===${NC}"
test_endpoint "GET" "/admin/settings" "Full admin settings"
test_endpoint "GET" "/admin/settings/branding" "Branding settings"
test_endpoint "GET" "/admin/settings/ai" "AI settings"
test_endpoint "GET" "/admin/settings/full" "Full settings (unified)"

# Test settings updates
echo -e "${YELLOW}=== Settings Updates ===${NC}"

# Test branding update
branding_update='{
    "companyName": "Test Company",
    "primaryColor": "#ff0000"
}'
test_endpoint "PUT" "/admin/settings/branding" "Update branding" "$branding_update"

# Test AI settings update
ai_update='{
    "temperature": 0.8,
    "max_tokens": 512,
    "model": "gpt-4o-mini"
}'
test_endpoint "PUT" "/admin/settings/ai" "Update AI settings" "$ai_update"

# Test full settings update
full_update='{
    "companyName": "Full Test Company",
    "temperature": 0.6,
    "taglineText": "Test tagline"
}'
test_endpoint "PUT" "/admin/settings/full" "Update full settings" "$full_update"

# Test admin endpoints from router
echo -e "${YELLOW}=== Admin API Router Endpoints ===${NC}"
test_endpoint "GET" "/api/admin/settings" "Admin settings (router)"

# Test legacy compatibility
echo -e "${YELLOW}=== Legacy Compatibility ===${NC}"
legacy_settings='{
    "primaryColor": "#00ff00",
    "temperature": 0.9
}'
test_endpoint "PUT" "/admin/settings" "Legacy settings update" "$legacy_settings"

# Test document management
echo -e "${YELLOW}=== Document Management ===${NC}"
test_endpoint "GET" "/list_documents/" "List documents"
test_endpoint "GET" "/count_documents/" "Count documents"
test_endpoint "POST" "/api/scan/" "Manual scan"

# Test branding endpoints
echo -e "${YELLOW}=== Branding Management ===${NC}"
test_endpoint "GET" "/api/admin/branding" "Admin branding (router)"

# Test query functionality (no auth required)
echo -e "${YELLOW}=== Query System ===${NC}"
test_endpoint "GET" "/query/?query=test" "Query snippets" "" 200

# Test chat endpoint (no auth required)  
echo -e "${YELLOW}=== Chat System ===${NC}"
# Using GET parameters since it's a POST but with Query params
echo -e "${BLUE}Testing:${NC} POST /chat/ - Chat completion"
chat_response=$(curl -s -X POST "$BASE_URL/chat/?query=hello&style=paragraph&tone=friendly&length=short" -w "\n%{http_code}")
chat_status=$(echo "$chat_response" | tail -n1)
chat_body=$(echo "$chat_response" | head -n -1)

if [[ $chat_status == "200" ]]; then
    echo -e "${GREEN}✅ $chat_status${NC} - Success"
    echo "📄 Response: ${chat_body:0:100}..."
else
    echo -e "${RED}❌ $chat_status${NC} - Expected 200"
    echo "📄 Response: $chat_body"
fi
echo ""

# Summary
echo -e "${YELLOW}=== Test Summary ===${NC}"
echo "🎉 Endpoint testing complete!"
echo ""
echo "💡 Tips:"
echo "   • All settings are persisted to storage/settings.json"
echo "   • Backups are created automatically during migrations"
echo "   • Use ./rollback_settings.py --list to see available backups"
echo "   • Check logs for any errors during testing"
echo ""
echo "🔧 Manual verification:"
echo "   curl -u $ADMIN_USER:$ADMIN_PASSWORD $BASE_URL/admin/settings/ai"
echo "   curl -u $ADMIN_USER:$ADMIN_PASSWORD $BASE_URL/admin/settings/branding"