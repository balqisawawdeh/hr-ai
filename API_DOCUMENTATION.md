# HR-Max AI Assistant API Documentation

## Overview

The HR-Max AI Assistant API provides natural language query capabilities for employee location tracking and status monitoring. This API allows external AI assistants to query employee information, check-in/out status, and location data through secure, rate-limited endpoints.

## Base URL

```
http://your-domain.com/api/
```

## Authentication

All API endpoints require authentication. The system supports:
- **Session Authentication** - For web-based applications
- **Token Authentication** - For external integrations (future enhancement)

### Headers Required
```
Content-Type: application/json
Cookie: sessionid=<session_id>  // For session auth
```

## Rate Limiting

The API implements rate limiting to ensure system stability:

| Endpoint Type | Rate Limit | Scope |
|---------------|------------|-------|
| AI Assistant Queries | 500/hour | Per authenticated user |
| Location Updates | 200/hour | Per authenticated user |
| General API | 1000/hour | Per authenticated user |
| Anonymous Access | 100/hour | Per IP address |

## API Endpoints

### 1. AI Assistant Query

Process natural language queries about employee status and locations.

**Endpoint:** `POST /api/ai-assistant/query/`

**Request Body:**
```json
{
  "query": "string (required, max 1000 characters)",
  "context": {
    "additional_context": "optional context object"
  }
}
```

**Response:**
```json
{
  "query": "How many employees are currently checked in?",
  "response": "Currently 0 employees are online and active.",
  "data": {
    "employees": []
  },
  "confidence": 0.9,
  "timestamp": "2025-06-10T18:54:39.560868Z",
  "user": "admin"
}
```

**Example Queries:**
- "How many employees are currently checked in?"
- "Show me all employees at the main office"
- "Who checked in today?"
- "List employees by department"
- "Find employees near location X"

**Error Responses:**
```json
// Query too long
{
  "error": "Query too long. Maximum length is 1000 characters."
}

// Request too large
{
  "error": "Query too large. Maximum size is 10KB."
}

// Processing error
{
  "error": "Error processing query: <error_message>",
  "timestamp": "2025-06-10T18:54:39.560868Z"
}
```

### 2. Employee Status

Get current status of all employees.

**Endpoint:** `GET /api/employee-status/`

**Response:**
```json
[
  {
    "id": 1,
    "employee": {
      "id": 1,
      "first_name": "John",
      "last_name": "Doe",
      "email": "john.doe@company.com"
    },
    "status": "checked_out",
    "last_check_in": null,
    "last_check_out": null,
    "current_location": null,
    "updated_at": "2025-06-10T18:54:39.560868Z"
  }
]
```

### 3. Check-in

Record employee check-in with location.

**Endpoint:** `POST /api/check-in/`

**Request Body:**
```json
{
  "employee_id": 1,
  "latitude": 40.7128,
  "longitude": -74.0060,
  "notes": "Arrived at office"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Check-in successful",
  "check_in_id": 123,
  "timestamp": "2025-06-10T18:54:39.560868Z"
}
```

**Validation Rules:**
- Latitude: -90 to 90
- Longitude: -180 to 180
- Employee must exist
- Notes are optional

### 4. Check-out

Record employee check-out.

**Endpoint:** `POST /api/check-out/`

**Request Body:**
```json
{
  "employee_id": 1,
  "notes": "End of workday"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Check-out successful",
  "timestamp": "2025-06-10T18:54:39.560868Z"
}
```

### 5. Location Update

Update employee location (for real-time tracking).

**Endpoint:** `POST /api/update-location/`

**Request Body:**
```json
{
  "employee_id": 1,
  "latitude": 40.7128,
  "longitude": -74.0060
}
```

**Response:**
```json
{
  "success": true,
  "message": "Location updated successfully"
}
```

### 6. Employee Current Location

Get current location of a specific employee.

**Endpoint:** `GET /api/employee-location/<employee_id>/`

**Response:**
```json
{
  "employee_id": 1,
  "current_location": {
    "latitude": 40.7128,
    "longitude": -74.0060,
    "timestamp": "2025-06-10T18:54:39.560868Z"
  },
  "status": "checked_in"
}
```

## Security Features

### Input Validation
- All coordinates are validated for proper ranges
- Query length is limited to 1000 characters
- Request size is limited to 10KB
- SQL injection protection is active

### Audit Logging
All API requests are logged with:
- User information
- IP address
- Timestamp
- Request details
- Response status

### Error Handling
- Detailed error messages for development
- Generic error messages for production
- Proper HTTP status codes
- Structured error responses

## WebSocket Integration

For real-time updates, the system supports WebSocket connections:

**WebSocket URL:** `ws://your-domain.com/ws/location/<employee_id>/`

**Message Format:**
```json
{
  "type": "location_update",
  "employee_id": 1,
  "latitude": 40.7128,
  "longitude": -74.0060,
  "timestamp": "2025-06-10T18:54:39.560868Z"
}
```

## Integration Examples

### Python Example
```python
import requests

# Authentication
session = requests.Session()
session.post('http://your-domain.com/login/', {
    'username': 'your_username',
    'password': 'your_password'
})

# AI Assistant Query
response = session.post('http://your-domain.com/api/ai-assistant/query/', json={
    'query': 'How many employees are currently at work?'
})

data = response.json()
print(f"Response: {data['response']}")
print(f"Confidence: {data['confidence']}")
```

### JavaScript Example
```javascript
// AI Assistant Query
fetch('/api/ai-assistant/query/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-CSRFToken': getCookie('csrftoken')
  },
  body: JSON.stringify({
    query: 'Show me all employees currently checked in'
  })
})
.then(response => response.json())
.then(data => {
  console.log('AI Response:', data.response);
  console.log('Employee Data:', data.data);
});
```

### cURL Example
```bash
# AI Assistant Query
curl -X POST http://your-domain.com/api/ai-assistant/query/ \
  -H "Content-Type: application/json" \
  -H "Cookie: sessionid=your_session_id" \
  -d '{"query": "How many employees are checked in today?"}'

# Check-in
curl -X POST http://your-domain.com/api/check-in/ \
  -H "Content-Type: application/json" \
  -H "Cookie: sessionid=your_session_id" \
  -d '{
    "employee_id": 1,
    "latitude": 40.7128,
    "longitude": -74.0060,
    "notes": "Arrived at office"
  }'
```

## Error Codes

| HTTP Code | Description |
|-----------|-------------|
| 200 | Success |
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Authentication required |
| 403 | Forbidden - Insufficient permissions |
| 413 | Request Entity Too Large |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error |

## Best Practices

### For AI Assistant Integration
1. **Cache responses** when appropriate to reduce API calls
2. **Handle rate limits** gracefully with exponential backoff
3. **Validate queries** before sending to reduce errors
4. **Use specific queries** for better AI processing
5. **Monitor confidence scores** to ensure response quality

### For Location Tracking
1. **Batch location updates** when possible
2. **Implement offline support** for mobile applications
3. **Respect privacy settings** and user permissions
4. **Use geofencing** for automatic check-in/out
5. **Validate coordinates** before sending

### Security Considerations
1. **Always use HTTPS** in production
2. **Implement proper authentication** for all requests
3. **Monitor API usage** for unusual patterns
4. **Log security events** for audit purposes
5. **Keep API keys secure** and rotate regularly

## Support and Troubleshooting

### Common Issues
1. **Authentication Errors** - Ensure valid session or token
2. **Rate Limit Exceeded** - Implement proper throttling
3. **Invalid Coordinates** - Validate lat/lng ranges
4. **Query Too Long** - Keep queries under 1000 characters

### Contact Information
For technical support or API questions, please contact the development team.

---
*API Documentation Version: 1.0*
*Last Updated: June 10, 2025*
*Compatible with: HR-Max v2.0+*

