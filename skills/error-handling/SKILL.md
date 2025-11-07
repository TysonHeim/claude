---
name: error-handling
description: Use when handling errors, implementing Problem Details (RFC 7807), or setting HTTP status codes.
---

# Error Handling

Use this skill when handling errors, implementing Problem Details (RFC 7807), or setting HTTP status codes.

## HTTP Status Code Standards

**ALWAYS** use appropriate HTTP status codes for different error scenarios:

- **200 OK**: Success with data (use `ApiResult<T>` wrapper)
- **400 Bad Request**: Client validation errors (use `ValidationProblemDetails`)
- **404 Not Found**: Resource not found (use `ProblemDetails`)
- **500 Internal Server Error**: Server/system errors (use `ProblemDetails`)

## Exception Hierarchy

- **NEVER** throw exceptions for business rule violations
- **ALWAYS** use `ProcessResult` pattern for business errors in Application layer (from `Common.Application.Results`)
- **ONLY** throw exceptions for technical failures (DB connection, etc.)
- **ALWAYS** log exceptions with structured logging
- **ALWAYS** handle ProcessResult.IsSuccess in controllers

## Error Response Patterns

### Success Response (200 OK)

```json
{
  "data": {
    "id": 1,
    "name": "Entity",
    "aspects": [...]
  }
}
```

### Validation Error (400 Bad Request)

```json
{
  "type": "https://tools.ietf.org/html/rfc7231#section-6.5.1",
  "title": "One or more validation errors occurred",
  "status": 400,
  "detail": "Please refer to the errors property for additional details",
  "instance": "/api/v2/entity-types",
  "errors": {
    "name": ["Name is required", "Name cannot exceed 100 characters"]
  }
}
```

### Not Found Error (404 Not Found)

```json
{
  "type": "https://tools.ietf.org/html/rfc7231#section-6.5.1",
  "title": "Entity type not found",
  "status": 404,
  "detail": "No entity type exists with ID 999",
  "instance": "/api/v2/entity-types/999"
}
```

### Server Error (500 Internal Server Error)

```json
{
  "type": "https://tools.ietf.org/html/rfc7231#section-6.5.1",
  "title": "Internal server error",
  "status": 500,
  "detail": "An unexpected error occurred while processing the request",
  "instance": "/api/v2/entity-types/1"
}
```

## Problem Details Benefits

- **Standardized**: RFC 7807 is the industry standard
- **Machine Readable**: Clients can programmatically handle different error types
- **Rich Information**: Type, title, detail, instance, extensions
- **Consistent**: All APIs return errors in the same structure
- **HTTP Semantics**: Status codes clearly indicate success vs. different error types

## Controller Error Handling Pattern

**ALWAYS** use this pattern in V2 controllers:

```csharp
[HttpGet("{id:int}")]
public async Task<IActionResult> GetEntityTypeById(int id, CancellationToken cancellationToken = default)
{
    logger.LogInformation("Retrieving entity type with ID {EntityTypeId}", id);

    try
    {
        var processResult = await mediator.Send(new GetEntityTypeByIdQuery(id), cancellationToken);

        if (processResult.IsSuccess)
        {
            logger.LogInformation("Successfully retrieved entity type with ID {EntityTypeId}", id);
            return HandleSuccess(processResult.Data!); // 200 OK + ApiResult<T>
        }

        // ProcessResult.Failure means entity not found (404)
        logger.LogWarning("Entity type with ID {EntityTypeId} not found", id);
        return CreateProblemDetailsResponse(
            "Entity type not found",
            $"No entity type exists with ID {id}",
            StatusCodes.Status404NotFound);
    }
    catch (Exception ex)
    {
        // Unexpected exception means server error (500)
        logger.LogError(ex, "Unexpected error occurred while retrieving entity type with ID {EntityTypeId}", id);
        return CreateProblemDetailsResponse(
            "Internal server error",
            "An unexpected error occurred while processing the request",
            StatusCodes.Status500InternalServerError);
    }
}
```

## Key Principles

- **Success**: Use `HandleSuccess()` with `ApiResult<T>` wrapper
- **Business Logic Failure**: Use `CreateProblemDetailsResponse()` with 404 status
- **System Exception**: Use `CreateProblemDetailsResponse()` with 500 status
- **Validation Errors**: Use `HandleValidationErrors()` with 400 status
- **NEVER** nest Problem Details inside wrapper objects
- **ALWAYS** use appropriate HTTP status codes
