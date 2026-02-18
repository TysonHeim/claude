# /cleanup-branch Command

When this command is used, perform a comprehensive cleanup of the current branch to prepare it for PR or final review.

## Step 1: Identify Current Branch & Scope

1. Get the current branch name and recent commits
2. Identify all modified, added, and untracked files in this branch
3. Show a summary of what will be cleaned up

## Step 2: Move Documentation to Git-Ignored Folder

**Target folder:** `.claude-plans/`

### Files to move:
- Any `*.md` files that are:
  - Migration guides (e.g., `MIGRATION_*.md`)
  - Implementation notes
  - Design documents
  - Planning documents
  - Documentation that's not user-facing

### Keep in place:
- `README.md` files
- User-facing documentation
- API documentation that should be committed

**Actions:**
1. Create `.claude-plans/` folder if it doesn't exist
2. Move identified documentation files to `.claude-plans/`
3. Organize by topic/feature if needed
4. Git remove the old locations

## Step 3: Code Quality Scan

### Review Focus Areas:

**1. Dead Code Detection**
- Unused imports/using statements
- Commented-out code blocks
- Unreachable code
- Unused variables/functions
- Duplicate code

**2. Comment Quality**
- Outdated comments that don't match the code
- Redundant comments (explaining obvious code)
- TODO/FIXME comments that should be addressed
- Commented-out code that should be removed
- Keep: Meaningful business logic explanations

**3. Code Smells**
- Long methods/functions (>50 lines)
- Complex conditionals that need refactoring
- Magic numbers/strings without explanation
- Inconsistent naming
- Missing error handling

**4. Red Flags (Critical Issues)**
- Security vulnerabilities (SQL injection, XSS, auth bypass, etc.)
- Hardcoded credentials or secrets
- Unhandled exceptions in critical paths
- Memory leaks or resource leaks
- Race conditions or threading issues
- Breaking API changes without migration path
- Missing input validation
- Improper error messages exposing internals

## Step 4: Generate Cleanup Report

Create a detailed cleanup report with:

### Branch Summary
- Branch name
- Files changed count
- Lines added/removed
- Commit count

### Documentation Moved
- List of files moved to `.claude-plans/`

### Code Changes Needed

#### Dead Code Found
- [ ] File: path/to/file:123 - Unused import
- [ ] File: path/to/file:456 - Commented out code block

#### Comments to Remove/Update
- [ ] File: path/to/file:100 - Outdated comment
- [ ] File: path/to/file:250 - TODO that should be addressed

#### Code Smells
- [ ] File: path/to/file:300 - Method too long
- [ ] File: path/to/file:50 - Magic number

### RED FLAGS (Critical)
- [ ] **SECURITY**: Description and location
- [ ] **CRITICAL**: Description and location
- [ ] **BREAKING**: Description and location

### Already Clean
- List areas that are already in good shape

## Step 5: Interactive Cleanup

After presenting the report, ask the user:

```
Found X issues to clean up:
- Y documentation files to move
- Z dead code items
- N comments to remove/update
- M code smells
- P RED FLAGS

Would you like me to:
1. Fix all automatically (except RED FLAGS - those need review)
2. Fix category by category with your approval
3. Show me the RED FLAGS first
4. Generate detailed report only (no changes)

Your choice (1-4)?
```

## Step 6: Execute Cleanup

Based on user choice, perform the cleanup:

### Automatic Fixes (if approved):
- Move documentation files
- Remove dead code (unused imports, commented code, unused functions)
- Remove/update outdated comments
- Fix simple code smells (extract magic numbers, etc.)

### Manual Review Required:
- All RED FLAGS
- Complex refactoring suggestions
- Breaking changes
- Security issues

## Step 7: Summary & Next Steps

After cleanup:
1. Show git diff summary
2. List what was changed
3. Highlight any remaining RED FLAGS that need manual attention
4. Suggest running tests
5. Suggest creating a commit with cleanup changes
