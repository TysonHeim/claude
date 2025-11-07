---
name: performance-optimization
description: Use when implementing features that require performance optimization, React Query configuration, debouncing, database indexing, or bundle optimization.
trigger: performance, optimization, slow queries, bundle size, React Query, debouncing, caching
---

# Performance Optimization Skill

## React Query Patterns

### Query Configuration
- Set appropriate `staleTime` for cached data (default: 0, consider 5 minutes for stable data)
- Use `enabled` flag for dependent queries
- Implement optimistic updates for better UX
- Use `placeholderData` or `initialData` for instant feedback

### Dependent Queries
```typescript
// Only fetch relationships when entity is loaded
const { data: entity } = useGetEntityQuery(entityId);
const { data: relationships } = useGetEntityRelationshipsQuery(
  entityId,
  { enabled: !!entity }
);
```

### Optimistic Updates
```typescript
// Update UI before server responds
const mutation = useMutation({
  onMutate: async (newData) => {
    await queryClient.cancelQueries(['relationships', entityId]);
    const previous = queryClient.getQueryData(['relationships', entityId]);
    queryClient.setQueryData(['relationships', entityId], (old) => [...old, newData]);
    return { previous };
  },
  onError: (err, newData, context) => {
    queryClient.setQueryData(['relationships', entityId], context.previous);
  },
});
```

## Validation Strategy

### Client-Side (Immediate Feedback)
- Range validation: 0.001 - 100.000%
- Format validation: up to 3 decimal places
- Required field validation
- Date range logic (EffectiveTo > EffectiveFrom)

### Server-Side (Business Rules)
- Total ownership ≤ 100% (across all relationships)
- Bidirectional relationship deduplication
- Access control validation
- Concurrency conflict detection

### Debouncing
- Debounce real-time validation API calls (300ms)
- Show loading indicator during validation
- Cancel pending requests on unmount
- Use `useDebounce` hook:
  ```typescript
  const debouncedPercentage = useDebounce(percentage, 300);
  const { data: validation } = useValidateOwnershipQuery(
    { entityId, percentage: debouncedPercentage },
    { enabled: !!debouncedPercentage }
  );
  ```

## Database Optimization

### Indexes
Add indexes for frequently queried columns:
```sql
CREATE INDEX IX_EntityRelationships_TargetEntityId_RelationshipTypeId
ON EntityRelationships(TargetEntityId, RelationshipTypeId)
WHERE IsDeleted = 0;

CREATE INDEX IX_EntityRelationships_EffectiveDates
ON EntityRelationships(EffectiveFrom, EffectiveTo)
WHERE IsDeleted = 0 AND OwnershipPercentage IS NOT NULL;
```

### Query Optimization
- Use composite indexes for multi-column filters
- Avoid N+1 queries with proper joins/includes:
  ```csharp
  context.EntityRelationships
    .Include(r => r.RelationshipType)
    .Include(r => r.TargetEntity)
    .Include(r => r.SourceStaff)
    .Where(r => !r.IsDeleted && r.TargetEntityId == entityId)
    .ToListAsync();
  ```
- Use pagination for large result sets
- Project only needed fields in queries:
  ```csharp
  .Select(r => new EntityRelationshipDto {
    Id = r.Id,
    OwnershipPercentage = r.OwnershipPercentage,
    // ... only needed fields
  })
  ```

### Validation Query Optimization
- Single query to calculate total ownership
- Use aggregation in database:
  ```csharp
  var total = await context.EntityRelationships
    .Where(r => !r.IsDeleted
      && r.TargetEntityId == entityId
      && r.RelationshipTypeId == beneficialOwnerId
      && r.Id != currentRelationshipId // exclude current if updating
    )
    .SumAsync(r => r.OwnershipPercentage ?? 0);
  ```

## Frontend Bundle Optimization

### Code Splitting
- Lazy load heavy components:
  ```typescript
  const RelationshipDrawer = lazy(() => import('./RelationshipDrawer'));
  ```
- Code split by routes
- Use React.lazy with Suspense

### Dependency Management
- Minimize dependencies (check bundle size)
- Use tree-shaking for unused exports
- Import only needed lodash functions: `import debounce from 'lodash/debounce'`
- Prefer lightweight alternatives when possible

### Asset Optimization
- Lazy load images
- Use appropriate image formats (WebP with fallbacks)
- Compress assets
- Use CDN for static resources

## Component Performance

### Memoization
- Use `React.memo` for expensive components
- Use `useMemo` for expensive calculations:
  ```typescript
  const remainingPercentage = useMemo(() => {
    return 100 - (currentTotal + newPercentage);
  }, [currentTotal, newPercentage]);
  ```
- Use `useCallback` for event handlers passed to children

### Virtualization
- Use virtualization for long lists (react-window, react-virtuoso)
- Paginate large datasets
- Implement infinite scroll for better UX

### Render Optimization
- Avoid inline object/array creation in render
- Use stable references for dependencies
- Debounce expensive operations (validation, API calls)
- Show loading states with skeletons

## API Performance

### Request Optimization
- Batch multiple requests when possible
- Use GraphQL or OData for flexible queries
- Implement request caching
- Use ETags for conditional requests

### Response Optimization
- Return only needed fields in DTOs
- Paginate large responses
- Compress responses (gzip)
- Use appropriate cache headers

## Monitoring

### Client-Side
- Monitor query execution time
- Track cache hit rates
- Log slow renders (React DevTools Profiler)
- Monitor bundle size in CI

### Server-Side
- Log slow queries (> 1 second)
- Monitor database query plans
- Track API response times
- Alert on performance regressions

## Performance Budget
- Initial page load: < 3 seconds
- API responses: < 500ms (p95)
- Database queries: < 100ms (p95)
- Bundle size: < 500KB (gzipped)
- Time to Interactive: < 5 seconds
