---
name: testing-standards
description: Use when writing tests, setting up test infrastructure, or reviewing test coverage.
---

# Testing Standards

Use this skill when writing tests, setting up test infrastructure, or reviewing test coverage.

## Unit Test Patterns

- **ALWAYS** test handlers in isolation
- **ALWAYS** mock external dependencies
- **ALWAYS** test both success and failure scenarios
- **ALWAYS** use descriptive test names

```csharp
[Test]
public async Task Handle_WhenEntityExists_ReturnsSuccessResult()
{
    // Arrange
    var query = new GetEntityQuery(Guid.NewGuid());
    var entity = new Entity { Id = query.Id, Name = "Test" };
    _repository.GetByIdAsync(query.Id).Returns(entity);

    // Act
    var result = await _handler.Handle(query, CancellationToken.None);

    // Assert
    result.IsSuccess.Should().BeTrue();
    result.Data.Should().BeEquivalentTo(entity);
}
```

## Integration Test Setup

- **ALWAYS** use test containers for database tests
- **ALWAYS** clean up test data after each test
- **ALWAYS** test the full request/response cycle
- **ALWAYS** use realistic test data

## Implementation Checklist

For each new endpoint:

- [ ] Created V2 query/command record (returns `ProcessResult<T>` or `ProcessResult`)
- [ ] Created validator for query/command (using FluentValidation)
- [ ] Created handler with optimized query (efficient DAL, `AsNoTracking()`)
- [ ] Created request/response models in `Common.Contracts` (proper naming: `Entity` not `EntityDto`)
- [ ] Created V2 controller endpoint (extends `ApiControllerBase`, route: `api/v2/[controller]`)
- [ ] Verified `ProcessResult` pattern used consistently in handlers
- [ ] Verified `ApiResult` pattern used consistently in controllers
- [ ] Added unit tests (handler tests with mocked dependencies)
- [ ] Added integration tests (full request/response cycle)
- [ ] Updated API documentation (Swagger/OpenAPI)
- [ ] Performance tested (profiled queries)
- [ ] Security reviewed (auth, input validation)
