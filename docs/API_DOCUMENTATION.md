# TrackIT API Documentation

## Table of Contents
- [Authentication](#authentication)
- [Tickets](#tickets)
- [Users](#users)
- [Comments](#comments)
- [Analytics](#analytics)
- [Health Check](#health-check)

## Base URL
All API endpoints are prefixed with `/api/v1`

## Authentication

### Sign Up
- **Endpoint**: `POST /api/v1/auth/signup`
- **Description**: Register a new user
- **Request Body**:
  ```json
  {
    "email": "user@example.com",
    "password": "securepassword123",
    "full_name": "John Doe"
  }
  ```
- **Response**:
  - 201 Created: User created successfully
  - 409 Conflict: User already exists

### Login
- **Endpoint**: `POST /api/v1/auth/login`
- **Description**: Authenticate user and get access token
- **Request Body**:
  ```json
  {
    "email": "user@example.com",
    "password": "securepassword123"
  }
  ```
- **Response**:
  - 200 OK: Authentication successful
    ```json
    {
      "access_token": "jwt_token_here",
      "refresh_token": "refresh_token_here",
      "token_type": "bearer",
      "user": {
        "email": "user@example.com",
        "user_id": "uuid_here",
        "role": "user"
      }
    }
    ```
  - 401 Unauthorized: Invalid credentials

### Refresh Token
- **Endpoint**: `POST /api/v1/auth/refresh`
- **Description**: Get new access token using refresh token
- **Headers**:
  - `Authorization: Bearer <refresh_token>`
- **Response**:
  - 200 OK: New access token generated
  - 401 Unauthorized: Invalid or expired refresh token

## Tickets

### Create Ticket
- **Endpoint**: `POST /api/v1/ticket/create`
- **Description**: Create a new support ticket
- **Authentication**: Required (All roles)
- **Request Body (multipart/form-data)**:
  - `subject`: String (required, 5-200 chars)
  - `description`: String (required, min 10 chars)
  - `types_of_issue`: String (required)
  - `priority`: String (optional, default: "medium")
  - `assigned_to`: UUID (optional)
  - `files`: File[] (optional)
- **Response**:
  - 201 Created: Ticket created successfully
  - 400 Bad Request: Invalid input data
  - 401 Unauthorized: Not authenticated
  - 403 Forbidden: Insufficient permissions

### Update Ticket
- **Endpoint**: `PATCH /api/v1/ticket/update/{ticket_id}`
- **Description**: Update an existing ticket
- **Authentication**: Required (All roles)
- **Path Parameters**:
  - `ticket_id`: UUID of the ticket to update
- **Request Body (multipart/form-data)**:
  - `subject`: String (optional, 5-200 chars)
  - `description`: String (optional, min 10 chars)
  - `types_of_issue`: String (optional)
  - `priority`: String (optional)
  - `status`: String (optional)
  - `assigned_to`: UUID (optional)
  - `files`: File[] (optional)
- **Response**:
  - 200 OK: Ticket updated successfully
  - 400 Bad Request: Invalid input data
  - 401 Unauthorized: Not authenticated
  - 403 Forbidden: Insufficient permissions
  - 404 Not Found: Ticket not found

### Get My Tickets
- **Endpoint**: `GET /api/v1/ticket/my-tickets`
- **Description**: Get all tickets created by the current user
- **Authentication**: Required (All roles)
- **Response**:
  - 200 OK: List of user's tickets

### Get Unassigned Tickets
- **Endpoint**: `GET /api/v1/ticket/unassigned`
- **Description**: Get all unassigned tickets (Admin/Manager/IT Support only)
- **Authentication**: Required (Admin/Manager/IT Support)
- **Response**:
  - 200 OK: List of unassigned tickets

### Get Ticket by ID
- **Endpoint**: `GET /api/v1/ticket/{ticket_id}`
- **Description**: Get ticket details by ID
- **Authentication**: Required
- **Path Parameters**:
  - `ticket_id`: UUID of the ticket
- **Response**:
  - 200 OK: Ticket details
  - 403 Forbidden: Not authorized to view this ticket
  - 404 Not Found: Ticket not found

### Delete Ticket
- **Endpoint**: `DELETE /api/v1/ticket/{ticket_id}`
- **Description**: Delete a ticket (Admin/Manager only)
- **Authentication**: Required (Admin/Manager)
- **Path Parameters**:
  - `ticket_id`: UUID of the ticket to delete
- **Response**:
  - 200 OK: Ticket deleted successfully
  - 403 Forbidden: Insufficient permissions
  - 404 Not Found: Ticket not found

## Comments

### Add Comment
- **Endpoint**: `POST /api/v1/comment`
- **Description**: Add a comment to a ticket
- **Authentication**: Required (All roles)
- **Request Body**:
  ```json
  {
    "ticket_id": "uuid_here",
    "content": "This is a comment"
  }
  ```
- **Response**:
  - 201 Created: Comment added successfully
  - 400 Bad Request: Invalid input data
  - 401 Unauthorized: Not authenticated
  - 404 Not Found: Ticket not found

### Get Ticket Comments
- **Endpoint**: `GET /api/v1/comment/ticket/{ticket_id}`
- **Description**: Get all comments for a ticket
- **Authentication**: Required
- **Path Parameters**:
  - `ticket_id`: UUID of the ticket
- **Response**:
  - 200 OK: List of comments
  - 403 Forbidden: Not authorized to view these comments
  - 404 Not Found: Ticket not found

## Analytics

### Get Ticket Statistics
- **Endpoint**: `GET /api/v1/analytics/stats`
- **Description**: Get ticket statistics (Admin/Manager only)
- **Authentication**: Required (Admin/Manager)
- **Response**:
  - 200 OK: Ticket statistics
  ```json
  {
    "total_tickets": 42,
    "open_tickets": 10,
    "in_progress_tickets": 15,
    "resolved_tickets": 17,
    "high_priority_tickets": 5,
    "avg_resolution_time_hours": 24.5
  }
  ```

## Health Check

### Check API Status
- **Endpoint**: `GET /api/v1/health`
- **Description**: Check if API is running
- **Response**:
  - 200 OK: API is running
  ```json
  {
    "status": "ok"
  }
  ```

## Error Responses

### Common Error Responses
- **400 Bad Request**: Invalid request data
- **401 Unauthorized**: Missing or invalid authentication
- **403 Forbidden**: Insufficient permissions
- **404 Not Found**: Resource not found
- **409 Conflict**: Resource already exists
- **422 Unprocessable Entity**: Validation error
- **500 Internal Server Error**: Server error

### Error Response Format
```json
{
  "detail": "Error message here"
}
```

## Rate Limiting
API is rate limited to 1000 requests per hour per IP address. Exceeding this limit will result in a 429 Too Many Requests response.

## Authentication
All authenticated endpoints require a valid JWT token in the Authorization header:
```
Authorization: Bearer <access_token>
```

## Pagination
Endpoints that return lists of items support pagination using query parameters:
- `page`: Page number (default: 1)
- `limit`: Items per page (default: 20, max: 100)

## Data Types

### UUID
A universally unique identifier (e.g., "123e4567-e89b-12d3-a456-426614174000")

### Timestamp
ISO 8601 format (e.g., "2023-01-01T12:00:00Z")

## WebSocket Support
WebSocket endpoints are available for real-time updates. Connect to `wss://api.example.com/ws` with a valid JWT token.

## Changelog
- **v1.0.0 (2024-02-01)**: Initial release


