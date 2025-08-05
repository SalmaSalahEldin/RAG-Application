# Delete Endpoints Guide

## Overview

This guide documents the delete endpoints available in the RAG system. The system provides comprehensive deletion capabilities for projects and individual files.

## Available Delete Endpoints

### 1. **Delete Project** 
- **Endpoint**: `DELETE /api/v1/data/projects/{project_code}`
- **Description**: Delete a project and all its associated data (files, chunks, vectors)
- **Note**: This is equivalent to deleting all files in the project plus the project itself

### 2. **Delete Single File**
- **Endpoint**: `DELETE /api/v1/data/file/{project_code}/{asset_id}`
- **Description**: Delete a specific file from a project (including its chunks and vectors)

## Endpoint Details

### 1. **Delete Project**

**Purpose**: Completely remove a project and all its associated data.

**URL**: `DELETE /api/v1/data/projects/{project_code}`

**Parameters**:
- `project_code` (path parameter): The project code to delete

**Headers**:
```
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

**Response**:
```json
{
    "signal": "PROJECT_DELETED",
    "message": "Project 1 deleted successfully",
    "deleted_project": {
        "project_id": 1,
        "project_code": 1,
        "project_uuid": "123e4567-e89b-12d3-a456-426614174000",
        "asset_count": 3,
        "chunk_count": 15,
        "deleted_at": "2024-01-15T10:30:00Z"
    }
}
```

**Error Responses**:
```json
{
    "signal": "PROJECT_NOT_FOUND",
    "error": "Project not found",
    "message": "Project 1 not found or you don't have access to it"
}
```

```json
{
    "signal": "PROJECT_DELETION_FAILED",
    "error": "Failed to delete project",
    "message": "An error occurred while deleting the project. Please try again."
}
```

### 2. **Delete Single File**

**Purpose**: Remove a specific file from a project.

**URL**: `DELETE /api/v1/data/file/{project_code}/{asset_id}`

**Parameters**:
- `project_code` (path parameter): The project code containing the file
- `asset_id` (path parameter): The ID of the file to delete

**Headers**:
```
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

**Response**:
```json
{
    "signal": "FILE_DELETED",
    "message": "File 'document.pdf' deleted successfully",
    "deleted_file": {
        "asset_id": 3,
        "asset_name": "document.pdf",
        "asset_size": 1024000,
        "asset_type": "pdf",
        "chunk_count": 5,
        "deleted_at": "2024-01-15T10:30:00Z"
    }
}
```

**Error Responses**:
```json
{
    "signal": "FILE_NOT_FOUND",
    "error": "File not found",
    "message": "File with ID 3 not found in project 1"
}
```

```json
{
    "signal": "FILE_DELETION_FAILED",
    "error": "Failed to delete file",
    "message": "An error occurred while deleting the file. Please try again."
}
```

## Usage Examples

### Delete Project

```bash
# Delete project 1
curl -X DELETE \
  'http://localhost:8000/api/v1/data/projects/1' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...' \
  -H 'Content-Type: application/json'
```

### Delete Single File

```bash
# Delete file with ID 3 from project 1
curl -X DELETE \
  'http://localhost:8000/api/v1/data/file/1/3' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...' \
  -H 'Content-Type: application/json'
```

## Implementation Details

### Data Cleanup Process

When deleting a project, the system performs the following cleanup:

1. **Delete Vector Data**: Removes all vector embeddings from Qdrant
2. **Delete Chunks**: Removes all text chunks from PostgreSQL
3. **Delete Assets**: Removes all file assets from PostgreSQL
4. **Delete Project**: Removes the project record from PostgreSQL

When deleting a single file, the system performs:

1. **Delete Vector Data**: Removes vector embeddings for the specific file
2. **Delete Chunks**: Removes text chunks for the specific file
3. **Delete Asset**: Removes the file asset from PostgreSQL

### Error Handling

All delete operations include comprehensive error handling:

- **Validation**: Ensures user has access to the project/file
- **Transaction Safety**: Uses database transactions for data consistency
- **Graceful Degradation**: Continues deletion even if some steps fail
- **Detailed Logging**: Provides extensive logging for debugging

### Security Considerations

- **Authentication Required**: All endpoints require valid JWT tokens
- **User Isolation**: Users can only delete their own projects and files
- **Access Control**: Validates project ownership before deletion
- **Audit Trail**: Logs all deletion operations for security purposes

## Frontend Integration

### UI Elements

The frontend provides the following delete functionality:

1. **Delete Project Button**: Available in project management section
2. **Delete File Button**: Available for each individual file (🗑️ icon)

### User Experience

- **Confirmation Dialogs**: All deletions require user confirmation
- **Progress Indicators**: Shows deletion progress to users
- **Success/Error Messages**: Clear feedback on operation results
- **Automatic Refresh**: Updates UI after successful deletions

## Best Practices

1. **Always Confirm**: Use confirmation dialogs for destructive operations
2. **Provide Feedback**: Show clear success/error messages to users
3. **Handle Errors Gracefully**: Continue operation even if some steps fail
4. **Log Operations**: Maintain audit trail for security and debugging
5. **Test Thoroughly**: Verify deletion works in all scenarios

## Migration Notes

### Recent Changes

- **Removed Redundant Endpoint**: The `DELETE /api/v1/data/files/{project_code}` endpoint has been removed
- **Consolidated Functionality**: Project deletion now automatically handles all file deletion
- **Simplified UI**: Removed "Delete All Files" button from frontend

### Backward Compatibility

- **API Changes**: The removed endpoint will return 404 Not Found
- **Frontend Updates**: UI has been updated to reflect the simplified deletion model
- **Documentation**: Updated to reflect current endpoint structure 