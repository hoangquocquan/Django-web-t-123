# AI Chat API

## Endpoint

`POST /api/v1/ai/chat/`

## Authentication

Use the Django foundation Bearer token:

```http
Authorization: Bearer <token>
```

The user must have `ai:write` permission or a wildcard admin permission.

## Request

```json
{
  "message": "MecPrecision co gia cong CNC khong?"
}
```

## Success Response

```json
{
  "success": true,
  "data": {
    "answer": "AI response",
    "model": "llama3.1",
    "provider": "ollama-local",
    "user": {
      "id": 1,
      "email": "admin@example.com"
    }
  }
}
```

## Error Responses

Missing or invalid token:

```json
{
  "success": false,
  "error": {
    "code": "permission_denied",
    "message": "Bearer token is required."
  }
}
```

Ollama unavailable:

```json
{
  "success": false,
  "error": {
    "code": "ollama_unavailable",
    "message": "Ollama local API is not available."
  }
}
```

