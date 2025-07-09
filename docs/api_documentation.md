# Cybercon Melbourne 2025 Speaker Presentation Management System
## API Documentation

**Version**: 1.0  
**Date**: July 2025  
**Author**: Manus AI Development Team  
**Classification**: Technical Documentation  

---

## Table of Contents

1. [API Overview](#api-overview)
2. [Authentication](#authentication)
3. [User Management APIs](#user-management-apis)
4. [Session Management APIs](#session-management-apis)
5. [File Management APIs](#file-management-apis)
6. [Review and Approval APIs](#review-and-approval-apis)
7. [Notification APIs](#notification-apis)
8. [Administrative APIs](#administrative-apis)
9. [Error Handling](#error-handling)
10. [Rate Limiting](#rate-limiting)

---

## API Overview

The Cybercon Melbourne 2025 Speaker Presentation Management System provides a comprehensive RESTful API that enables secure, efficient interaction with all system functionality. The API is designed following industry best practices for security, performance, and usability.

### Base URL
```
Production: https://api.cybercon2025.com
Staging: https://staging-api.cybercon2025.com
```

### API Versioning
All API endpoints are versioned using URL path versioning:
```
/api/v1/{endpoint}
```

### Content Types
- **Request Content-Type**: `application/json`
- **Response Content-Type**: `application/json`
- **File Upload Content-Type**: `multipart/form-data`

### Standard Response Format
```json
{
  "success": true,
  "data": {},
  "message": "Operation completed successfully",
  "timestamp": "2025-07-09T10:30:00Z",
  "request_id": "req_123456789"
}
```

## Authentication

### JWT Token Authentication
The API uses JSON Web Tokens (JWT) for authentication. Tokens must be included in the Authorization header:

```http
Authorization: Bearer <jwt_token>
```

### Login Endpoint
**POST** `/api/auth/login`

Request:
```json
{
  "email": "user@example.com",
  "password": "securepassword123",
  "mfa_code": "123456"
}
```

Response:
```json
{
  "success": true,
  "data": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "expires_in": 3600,
    "user": {
      "id": 1,
      "email": "user@example.com",
      "name": "John Doe",
      "roles": ["speaker"]
    }
  }
}
```

### Token Refresh
**POST** `/api/auth/refresh`

Request:
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### Multi-Factor Authentication Setup
**POST** `/api/auth/mfa/setup`

Response:
```json
{
  "success": true,
  "data": {
    "qr_code": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
    "secret": "JBSWY3DPEHPK3PXP",
    "backup_codes": ["12345678", "87654321"]
  }
}
```

## User Management APIs

### Get Current User Profile
**GET** `/api/users/profile`

Response:
```json
{
  "success": true,
  "data": {
    "id": 1,
    "email": "speaker@example.com",
    "first_name": "Jane",
    "last_name": "Smith",
    "organisation": "Tech Corp",
    "bio": "Experienced software developer...",
    "phone": "+61412345678",
    "roles": ["speaker"],
    "created_at": "2025-01-15T09:00:00Z",
    "last_login": "2025-07-09T08:30:00Z"
  }
}
```

### Update User Profile
**PUT** `/api/users/profile`

Request:
```json
{
  "first_name": "Jane",
  "last_name": "Smith",
  "organisation": "Tech Corp",
  "bio": "Updated biography...",
  "phone": "+61412345678"
}
```

### Change Password
**POST** `/api/users/change-password`

Request:
```json
{
  "current_password": "oldpassword123",
  "new_password": "newpassword456",
  "confirm_password": "newpassword456"
}
```

### User Registration
**POST** `/api/auth/register`

Request:
```json
{
  "email": "newuser@example.com",
  "password": "securepassword123",
  "first_name": "John",
  "last_name": "Doe",
  "organisation": "Example Corp",
  "phone": "+61412345678"
}
```

## Session Management APIs

### Create New Session
**POST** `/api/sessions`

Request:
```json
{
  "title": "Advanced Cybersecurity Techniques",
  "abstract": "This session covers advanced cybersecurity...",
  "description": "Detailed description of the session content...",
  "session_type_id": 1,
  "duration_minutes": 45,
  "target_audience": "intermediate",
  "learning_objectives": ["Understand advanced threats", "Learn mitigation strategies"],
  "additional_speakers": [
    {
      "name": "Co-Speaker Name",
      "email": "cospeaker@example.com",
      "organisation": "Security Corp"
    }
  ],
  "upload_comments": "Please review the attached presentation slides"
}
```

Response:
```json
{
  "success": true,
  "data": {
    "id": 123,
    "title": "Advanced Cybersecurity Techniques",
    "status": "draft",
    "submission_date": "2025-07-09T10:30:00Z",
    "session_type": {
      "id": 1,
      "name": "Technical Session",
      "duration_minutes": 45
    }
  }
}
```

### Get User Sessions
**GET** `/api/sessions`

Query Parameters:
- `status`: Filter by status (draft, submitted, under_review, approved, rejected)
- `page`: Page number (default: 1)
- `limit`: Items per page (default: 10)

Response:
```json
{
  "success": true,
  "data": {
    "sessions": [
      {
        "id": 123,
        "title": "Advanced Cybersecurity Techniques",
        "status": "under_review",
        "submission_date": "2025-07-09T10:30:00Z",
        "last_updated": "2025-07-09T14:20:00Z",
        "session_type": {
          "name": "Technical Session"
        }
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 10,
      "total": 1,
      "pages": 1
    }
  }
}
```

### Get Session Details
**GET** `/api/sessions/{session_id}`

Response:
```json
{
  "success": true,
  "data": {
    "id": 123,
    "title": "Advanced Cybersecurity Techniques",
    "abstract": "This session covers...",
    "description": "Detailed description...",
    "status": "under_review",
    "session_type": {
      "id": 1,
      "name": "Technical Session",
      "duration_minutes": 45
    },
    "speakers": [
      {
        "id": 1,
        "name": "Jane Smith",
        "email": "jane@example.com",
        "is_primary": true
      }
    ],
    "files": [
      {
        "id": 1,
        "filename": "presentation.pdf",
        "size": 2048576,
        "upload_date": "2025-07-09T11:00:00Z"
      }
    ],
    "reviews": [
      {
        "id": 1,
        "status": "pending",
        "reviewer": {
          "name": "Dr. Review Expert"
        },
        "assigned_date": "2025-07-09T12:00:00Z"
      }
    ]
  }
}
```

### Update Session
**PUT** `/api/sessions/{session_id}`

Request: Same format as create session

### Submit Session for Review
**POST** `/api/sessions/{session_id}/submit`

Response:
```json
{
  "success": true,
  "data": {
    "status": "submitted",
    "submission_date": "2025-07-09T15:30:00Z"
  },
  "message": "Session submitted for review successfully"
}
```

### Session Q&A
**POST** `/api/sessions/{session_id}/questions`

Request:
```json
{
  "question": "What is the expected audience size for this session?",
  "urgency": "normal"
}
```

**GET** `/api/sessions/{session_id}/questions`

Response:
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "question": "What is the expected audience size?",
      "urgency": "normal",
      "asked_date": "2025-07-09T16:00:00Z",
      "response": "We expect 50-75 attendees",
      "response_date": "2025-07-09T17:30:00Z",
      "responder": {
        "name": "Conference Manager"
      }
    }
  ]
}
```

## File Management APIs

### Upload File
**POST** `/api/sessions/{session_id}/files`

Request (multipart/form-data):
```
file: [binary file data]
description: "Main presentation slides"
```

Response:
```json
{
  "success": true,
  "data": {
    "id": 1,
    "filename": "presentation.pdf",
    "original_filename": "My Presentation.pdf",
    "size": 2048576,
    "mime_type": "application/pdf",
    "sha256_hash": "a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3",
    "upload_date": "2025-07-09T11:00:00Z",
    "version": 1
  }
}
```

### Get File List
**GET** `/api/sessions/{session_id}/files`

Response:
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "filename": "presentation.pdf",
      "size": 2048576,
      "upload_date": "2025-07-09T11:00:00Z",
      "version": 1,
      "is_current": true
    }
  ]
}
```

### Download File
**GET** `/api/files/{file_id}/download`

Response: Binary file data with appropriate headers

### View File in Browser
**GET** `/api/files/{file_id}/view`

Response: File content with appropriate MIME type for browser viewing

### Delete File
**DELETE** `/api/files/{file_id}`

Response:
```json
{
  "success": true,
  "message": "File deleted successfully"
}
```

## Review and Approval APIs

### Get Assigned Reviews (Manager)
**GET** `/api/reviews/assigned`

Query Parameters:
- `status`: Filter by review status
- `priority`: Filter by priority level
- `page`: Page number
- `limit`: Items per page

Response:
```json
{
  "success": true,
  "data": {
    "reviews": [
      {
        "id": 1,
        "session": {
          "id": 123,
          "title": "Advanced Cybersecurity Techniques",
          "speaker": {
            "name": "Jane Smith"
          }
        },
        "status": "pending",
        "assigned_date": "2025-07-09T12:00:00Z",
        "due_date": "2025-07-14T17:00:00Z",
        "priority": "normal"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 10,
      "total": 5,
      "pages": 1
    }
  }
}
```

### Submit Review
**POST** `/api/reviews/{review_id}/submit`

Request:
```json
{
  "decision": "approved",
  "overall_score": 8,
  "content_quality_score": 8,
  "relevance_score": 9,
  "presentation_quality_score": 7,
  "innovation_score": 8,
  "comments": "Excellent technical content with clear presentation structure...",
  "recommendations": "Consider adding more interactive elements",
  "public_feedback": "Great session topic that will benefit attendees"
}
```

### Add Review Comment
**POST** `/api/reviews/{review_id}/comments`

Request:
```json
{
  "comment": "Please clarify the target audience level",
  "is_public": true,
  "comment_type": "question"
}
```

### Respond to Speaker Question
**POST** `/api/questions/{question_id}/respond`

Request:
```json
{
  "response": "The expected audience size is 50-75 attendees based on registration data."
}
```

## Notification APIs

### Get Notifications
**GET** `/api/notifications`

Query Parameters:
- `unread_only`: Boolean to filter unread notifications
- `type`: Filter by notification type
- `page`: Page number
- `limit`: Items per page

Response:
```json
{
  "success": true,
  "data": {
    "notifications": [
      {
        "id": 1,
        "type": "session_status_change",
        "title": "Session Approved",
        "message": "Your session 'Advanced Cybersecurity Techniques' has been approved",
        "priority": "normal",
        "is_read": false,
        "created_at": "2025-07-09T18:00:00Z",
        "related_session_id": 123
      }
    ],
    "unread_count": 3,
    "pagination": {
      "page": 1,
      "limit": 10,
      "total": 15,
      "pages": 2
    }
  }
}
```

### Mark Notification as Read
**PUT** `/api/notifications/{notification_id}/read`

### Mark All Notifications as Read
**PUT** `/api/notifications/mark-all-read`

### Get Notification Preferences
**GET** `/api/notifications/preferences`

Response:
```json
{
  "success": true,
  "data": {
    "email_notifications": true,
    "session_updates": true,
    "review_notifications": true,
    "system_announcements": true,
    "digest_frequency": "daily"
  }
}
```

### Update Notification Preferences
**PUT** `/api/notifications/preferences`

Request:
```json
{
  "email_notifications": true,
  "session_updates": true,
  "review_notifications": false,
  "system_announcements": true,
  "digest_frequency": "weekly"
}
```

## Administrative APIs

### User Management (Admin)
**GET** `/api/admin/users`

Query Parameters:
- `role`: Filter by user role
- `status`: Filter by account status
- `search`: Search by name or email
- `page`: Page number
- `limit`: Items per page

Response:
```json
{
  "success": true,
  "data": {
    "users": [
      {
        "id": 1,
        "email": "user@example.com",
        "name": "John Doe",
        "roles": ["speaker"],
        "status": "active",
        "last_login": "2025-07-09T08:30:00Z",
        "created_at": "2025-01-15T09:00:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 150,
      "pages": 8
    }
  }
}
```

### Create User Invitation
**POST** `/api/admin/invitations`

Request:
```json
{
  "email": "newmanager@example.com",
  "role": "manager",
  "message": "Welcome to the Cybercon 2025 review team"
}
```

### System Statistics
**GET** `/api/admin/statistics`

Response:
```json
{
  "success": true,
  "data": {
    "total_users": 150,
    "total_sessions": 75,
    "sessions_by_status": {
      "draft": 10,
      "submitted": 25,
      "under_review": 20,
      "approved": 15,
      "rejected": 5
    },
    "reviews_completed": 40,
    "average_review_time_hours": 48,
    "file_storage_used_mb": 2048
  }
}
```

### Bulk Download Sessions
**POST** `/api/admin/bulk-download`

Request:
```json
{
  "session_ids": [123, 124, 125],
  "include_files": true,
  "filename_format": "{session_id}_{title}_{speaker_name}"
}
```

Response:
```json
{
  "success": true,
  "data": {
    "download_url": "https://api.cybercon2025.com/downloads/bulk_123456.zip",
    "expires_at": "2025-07-10T10:30:00Z"
  }
}
```

### FAQ Management
**GET** `/api/admin/faqs`

**POST** `/api/admin/faqs`

Request:
```json
{
  "question": "How do I upload large presentation files?",
  "answer": "Files up to 100MB are supported. For larger files, please contact support.",
  "category": "file_upload",
  "is_public": true
}
```

### Broadcast Messages
**POST** `/api/admin/broadcast`

Request:
```json
{
  "title": "Conference Update",
  "message": "Important update regarding session scheduling...",
  "audience": "all",
  "priority": "high",
  "send_email": true
}
```

## Error Handling

### Standard Error Response
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {
      "email": ["Email address is required"],
      "password": ["Password must be at least 8 characters"]
    }
  },
  "timestamp": "2025-07-09T10:30:00Z",
  "request_id": "req_123456789"
}
```

### HTTP Status Codes
- **200 OK**: Successful request
- **201 Created**: Resource created successfully
- **400 Bad Request**: Invalid request data
- **401 Unauthorized**: Authentication required
- **403 Forbidden**: Insufficient permissions
- **404 Not Found**: Resource not found
- **409 Conflict**: Resource conflict
- **422 Unprocessable Entity**: Validation errors
- **429 Too Many Requests**: Rate limit exceeded
- **500 Internal Server Error**: Server error

### Common Error Codes
- `AUTHENTICATION_REQUIRED`: User must log in
- `INSUFFICIENT_PERMISSIONS`: User lacks required permissions
- `VALIDATION_ERROR`: Request data validation failed
- `RESOURCE_NOT_FOUND`: Requested resource does not exist
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `FILE_TOO_LARGE`: Uploaded file exceeds size limit
- `UNSUPPORTED_FILE_TYPE`: File type not supported

## Rate Limiting

### Rate Limit Headers
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1625847600
```

### Rate Limits by Endpoint Type
- **Authentication**: 5 requests per minute
- **File Upload**: 10 requests per hour
- **General API**: 1000 requests per hour
- **Admin Operations**: 500 requests per hour

### Rate Limit Exceeded Response
```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests. Please try again later.",
    "retry_after": 3600
  }
}
```

---

**Document Information**
- **Version**: 1.0
- **Last Updated**: July 2025
- **Document Owner**: Manus AI Development Team
- **Review Schedule**: Monthly
- **Classification**: Technical Documentation

