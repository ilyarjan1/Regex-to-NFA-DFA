# Campus Services Hub - API Documentation

## Base URL

**Local Development:** `http://localhost:3000`  
**Production:** `https://api.campus-services.example.com`

All API requests should go through the API Gateway.

## Authentication

Most endpoints require authentication using JWT tokens.

### Headers

```
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

## Error Responses

All errors follow this format:

```json
{
  "error": "Error message description",
  "correlationId": "uuid-for-request-tracing"
}
```

Common HTTP status codes:
- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `409` - Conflict
- `500` - Internal Server Error

---

## User Service Endpoints

### Register User

**POST** `/api/users/register`

Create a new user account.

**Request Body:**
```json
{
  "email": "student@campus.edu",
  "password": "securePassword123",
  "first_name": "John",
  "last_name": "Doe",
  "role": "Student"
}
```

**Response:** `201 Created`
```json
{
  "message": "User registered successfully",
  "user": {
    "id": "uuid",
    "email": "student@campus.edu",
    "role": "Student",
    "first_name": "John",
    "last_name": "Doe"
  }
}
```

### Login

**POST** `/api/users/login`

Authenticate and receive JWT token.

**Request Body:**
```json
{
  "email": "student@campus.edu",
  "password": "securePassword123"
}
```

**Response:** `200 OK`
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "uuid",
    "email": "student@campus.edu",
    "role": "Student",
    "first_name": "John",
    "last_name": "Doe"
  }
}
```

### Get Profile

**GET** `/api/users/profile`

Get current user's profile. Requires authentication.

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "email": "student@campus.edu",
  "role": "Student",
  "first_name": "John",
  "last_name": "Doe",
  "created_at": "2024-01-15T10:30:00Z"
}
```

### Update Profile

**PUT** `/api/users/profile`

Update user profile. Requires authentication.

**Request Body:**
```json
{
  "first_name": "John",
  "last_name": "Smith"
}
```

**Response:** `200 OK`
```json
{
  "message": "Profile updated successfully"
}
```

---

## Ticket Service Endpoints

### Create Ticket

**POST** `/api/tickets`

Create a new service ticket. Requires authentication.

**Request Body:**
```json
{
  "title": "Broken AC in Room 301",
  "description": "The air conditioning unit is not working properly",
  "category": "Maintenance",
  "priority": "High"
}
```

**Response:** `201 Created`
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "title": "Broken AC in Room 301",
  "description": "The air conditioning unit is not working properly",
  "category": "Maintenance",
  "priority": "High",
  "status": "Open",
  "created_at": "2024-01-15T10:30:00Z"
}
```

### List Tickets

**GET** `/api/tickets?status=Open&priority=High`

Get all tickets (filtered by user role). Requires authentication.

**Query Parameters:**
- `status` (optional): Filter by status (Open, In Progress, Resolved, Closed)
- `priority` (optional): Filter by priority (Low, Medium, High, Urgent)
- `category` (optional): Filter by category

**Response:** `200 OK`
```json
[
  {
    "id": "uuid",
    "user_id": "uuid",
    "title": "Broken AC in Room 301",
    "description": "The air conditioning unit is not working properly",
    "category": "Maintenance",
    "priority": "High",
    "status": "Open",
    "assigned_to": null,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
]
```

### Get Ticket Details

**GET** `/api/tickets/:id`

Get specific ticket details. Requires authentication.

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "title": "Broken AC in Room 301",
  "description": "The air conditioning unit is not working properly",
  "category": "Maintenance",
  "priority": "High",
  "status": "In Progress",
  "assigned_to": "staff-uuid",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T11:00:00Z"
}
```

### Update Ticket

**PUT** `/api/tickets/:id`

Update ticket details. Requires authentication. Staff can update status and assignment.

**Request Body:**
```json
{
  "status": "In Progress",
  "assigned_to": "staff-uuid"
}
```

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "status": "In Progress",
  "assigned_to": "staff-uuid",
  "updated_at": "2024-01-15T11:00:00Z"
}
```

### Delete Ticket

**DELETE** `/api/tickets/:id`

Delete a ticket. Requires authentication (Admin or ticket owner).

**Response:** `200 OK`
```json
{
  "message": "Ticket deleted successfully"
}
```

---

## Booking Service Endpoints

### List Rooms

**GET** `/api/rooms`

Get all available rooms. Requires authentication.

**Response:** `200 OK`
```json
[
  {
    "id": "uuid",
    "name": "Study Room A",
    "type": "Study Room",
    "capacity": 4,
    "amenities": {
      "whiteboard": true,
      "projector": false
    },
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```

### Check Room Availability

**GET** `/api/rooms/:id/availability?date=2024-01-15`

Check room availability for a specific date. Requires authentication.

**Query Parameters:**
- `date` (optional): Date in YYYY-MM-DD format (defaults to today)

**Response:** `200 OK`
```json
{
  "room": {
    "id": "uuid",
    "name": "Study Room A",
    "type": "Study Room",
    "capacity": 4
  },
  "date": "2024-01-15",
  "bookings": [
    {
      "id": "uuid",
      "start_time": "2024-01-15T10:00:00Z",
      "end_time": "2024-01-15T12:00:00Z",
      "status": "Active"
    }
  ]
}
```

### Create Booking

**POST** `/api/bookings`

Create a new room booking. Requires authentication.

**Request Body:**
```json
{
  "room_id": "uuid",
  "start_time": "2024-01-15T14:00:00Z",
  "end_time": "2024-01-15T16:00:00Z",
  "purpose": "Group study session"
}
```

**Response:** `201 Created`
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "room_id": "uuid",
  "start_time": "2024-01-15T14:00:00Z",
  "end_time": "2024-01-15T16:00:00Z",
  "purpose": "Group study session",
  "status": "Active",
  "created_at": "2024-01-15T10:30:00Z"
}
```

### List My Bookings

**GET** `/api/bookings?status=Active`

Get current user's bookings. Requires authentication.

**Query Parameters:**
- `status` (optional): Filter by status (Active, Cancelled)

**Response:** `200 OK`
```json
[
  {
    "id": "uuid",
    "user_id": "uuid",
    "room_id": "uuid",
    "room_name": "Study Room A",
    "room_type": "Study Room",
    "start_time": "2024-01-15T14:00:00Z",
    "end_time": "2024-01-15T16:00:00Z",
    "purpose": "Group study session",
    "status": "Active",
    "created_at": "2024-01-15T10:30:00Z"
  }
]
```

### Cancel Booking

**DELETE** `/api/bookings/:id`

Cancel a booking. Requires authentication (booking owner or Admin).

**Response:** `200 OK`
```json
{
  "message": "Booking cancelled successfully"
}
```

---

## Notification Service Endpoints

### List Notifications

**GET** `/api/notifications?unread_only=true`

Get user notifications. Requires authentication.

**Query Parameters:**
- `unread_only` (optional): Set to "true" to get only unread notifications

**Response:** `200 OK`
```json
[
  {
    "_id": "mongodb-id",
    "user_id": "uuid",
    "type": "ticket_created",
    "title": "Ticket Created",
    "message": "Your ticket 'Broken AC in Room 301' has been created successfully.",
    "metadata": {
      "ticket_id": "uuid"
    },
    "read": false,
    "created_at": "2024-01-15T10:30:00Z"
  }
]
```

### Mark Notification as Read

**PUT** `/api/notifications/:id/read`

Mark a notification as read. Requires authentication.

**Response:** `200 OK`
```json
{
  "message": "Notification marked as read"
}
```

### Mark All as Read

**PUT** `/api/notifications/read-all`

Mark all notifications as read. Requires authentication.

**Response:** `200 OK`
```json
{
  "message": "5 notifications marked as read"
}
```

### Get Unread Count

**GET** `/api/notifications/unread-count`

Get count of unread notifications. Requires authentication.

**Response:** `200 OK`
```json
{
  "count": 3
}
```

### Delete Notification

**DELETE** `/api/notifications/:id`

Delete a notification. Requires authentication.

**Response:** `200 OK`
```json
{
  "message": "Notification deleted successfully"
}
```

---

## Health Check

### API Gateway Health

**GET** `/health`

Check health of all services. No authentication required.

**Response:** `200 OK`
```json
{
  "status": "healthy",
  "service": "api-gateway",
  "services": {
    "user-service": "healthy",
    "ticket-service": "healthy",
    "booking-service": "healthy",
    "notification-service": "healthy"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

## Notification Types

The system automatically sends notifications for these events:

- `ticket_created` - When a user creates a ticket
- `ticket_updated` - When a ticket status changes
- `booking_confirmation` - When a booking is created
- `booking_cancelled` - When a booking is cancelled

---

## Rate Limiting

Currently, no rate limiting is implemented. In production, consider:
- 100 requests per minute per user
- 1000 requests per minute per IP

## Correlation IDs

All requests receive a correlation ID in the response header:
```
x-correlation-id: uuid
```

Use this ID for request tracing and debugging.

---

**API Documentation Version 1.0**
