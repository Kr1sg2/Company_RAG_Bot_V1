# API Reference

Base URL: `http://localhost:8601`

## Core Endpoints

### Health Check
```http
GET /api/health
```

**Response:**
```json
{
  "status": "ok",
  "service": "lexa-backend"
}
```

### Chat Query (GET)
```http
GET /api/chat/?query={user_question}
```

**Parameters:**
- `query` (string, required): User's question

**Response:**
```json
{
  "response": "Based on the company handbook, employees with 6 years of service are eligible for 3 weeks of paid time off annually. — 1-1-paid-time-off.pdf, p. 2",
  "sources": [
    {
      "name": "1-1-paid-time-off.pdf (p.2)",
      "url": "http://localhost:8601/files/1-1-paid-time-off.pdf#page=2"
    }
  ]
}
```

### Chat Query (POST)
```http
POST /api/chat
Content-Type: application/json
```

**Request Body:**
```json
{
  "query": "What is the dress code policy?"
}
```

**Response:** Same as GET version

## Admin Endpoints

### Get Public Branding
```http
GET /api/admin/settings/public/branding
```

**Response:**
```json
{
  "companyName": "Leader's Casual Furniture",
  "primaryColor": "#2563eb",
  "secondaryColor": "#64748b"
}
```

### Get Admin Branding
```http
GET /api/admin/settings/branding
```

**Response:** Same as public branding in local mode

### Update Branding
```http
PUT /api/admin/settings/branding
Content-Type: application/json
```

**Request Body:**
```json
{
  "companyName": "Your Company",
  "primaryColor": "#2563eb",
  "secondaryColor": "#64748b",
  "logoUrl": "https://example.com/logo.png"
}
```

**Response:**
```json
{
  "companyName": "Your Company",
  "primaryColor": "#2563eb",
  "secondaryColor": "#64748b",
  "logoUrl": "https://example.com/logo.png"
}
```

## Authentication Endpoints

### Admin Login
```http
POST /api/admin/login
Content-Type: application/json
```

**Request Body:**
```json
{
  "password": "admin_password"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Logged in successfully"
}
```

**Note:** In local development mode, password validation is disabled.

### Admin Logout
```http
POST /api/admin/logout
```

**Response:**
```json
{
  "success": true,
  "message": "Logged out"
}
```

### Current User
```http
GET /api/admin/me
```

**Response:**
```json
{
  "user": "admin",
  "authenticated": true
}
```

## Error Responses

### Standard Error Format
```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common HTTP Status Codes
- `200` - Success
- `400` - Bad Request (invalid query, missing parameters)
- `401` - Unauthorized (authentication required)
- `404` - Not Found (endpoint doesn't exist)
- `500` - Internal Server Error (processing failed)

### Chat Endpoint Error Responses

**Empty Query:**
```json
{
  "response": "Query cannot be empty.",
  "sources": []
}
```

**Search Unavailable:**
```json
{
  "response": "Search functionality is not available.",
  "sources": []
}
```

**No Relevant Information:**
```json
{
  "response": "I could not find relevant information in my database.",
  "sources": []
}
```

## OpenAPI Documentation

Interactive API documentation is available at:
- Swagger UI: `http://localhost:8601/api/docs`
- ReDoc: `http://localhost:8601/api/redoc`
- OpenAPI JSON: `http://localhost:8601/api/openapi.json`

## Rate Limiting

Currently no rate limiting is implemented in local development mode. For production deployment, consider adding rate limiting middleware.

## CORS Configuration

The API accepts requests from:
- `http://localhost:8081` (alternative frontend port)
- `http://127.0.0.1:8081`
- `http://localhost:5173` (Vite dev server)
- Any localhost origin via regex pattern

## Legacy Endpoints

### Legacy Query
```http
GET /query/?query={user_question}
```

**Note:** This endpoint is deprecated. Use `/api/chat` instead.