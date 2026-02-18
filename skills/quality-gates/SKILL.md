---
name: quality-gates
description: Run build, test, lint, and typecheck validation before PR creation. Use when user says "run quality gates", "check build", "validate changes", or before submitting a pull request.
---

# Quality Gates

## Tests Are Mandatory

**Tests MUST be run for verification to pass. There is no skip option.**

Skipping tests has caused PR failures. Build and typecheck do NOT validate runtime behavior.

---

## Required Steps

Customize these commands for your project's stack:

### Backend
```bash
# Example for .NET:
# dotnet build --no-restore
# dotnet test --no-build --verbosity minimal

# Example for Node.js:
# npm run build
# npm test

# Example for Python:
# python -m pytest
```

### Frontend (if applicable)
```bash
# Example for React/TypeScript:
# npm run lint
# npm run typecheck
# npm run test
```

---

## Feature-Specific Verification

**After automated gates pass, verify the actual feature works:**

### Step 1: Identify Affected Features
Ask: "What UI or functionality does this code power?"

### Step 2: Visual/Functional Verification
If the app is running, use Playwright or manual testing:
1. Navigate to affected pages
2. Check for failure indicators (404s, empty components, console errors)
3. Verify expected content loads and interactive elements respond

---

## Track Results

```
QUALITY_GATES:
- BUILD: {PASS|FAIL}
- TESTS: {PASS|FAIL}        <- REQUIRED, no skip allowed
- LINT: {PASS|FAIL}         <- REQUIRED, no skip allowed
- TYPECHECK: {PASS|FAIL}    <- REQUIRED, no skip allowed
- FEATURE_VERIFY: {PASS|FAIL|SKIPPED}
```

**Verification FAILS if any required gate is not run or fails.**

---

## On Failure

### Step Back and Analyze (DO NOT FIX ONE ERROR AT A TIME)

**Before fixing ANY error, analyze ALL errors together:**

1. **Run the gate and capture ALL errors** (not just the first one)
2. **Look for patterns:**
   - Multiple "unused import" errors -> You added imports you didn't use
   - Multiple type errors in same file -> You don't understand the type system
   - Cascading errors -> One root cause creating many symptoms
3. **Identify the ROOT CAUSE** before making any fix
4. **Fix the root cause** - don't play whack-a-mole with individual errors

**Example of WRONG approach (causes infinite loops):**
```
See error: "unused import X" -> Remove X -> See "unused import Y" -> Remove Y -> ...
```

**Example of CORRECT approach:**
```
See errors: "unused import X", "unused import Y", "unused import Z"
-> STOP and ask: "Why did I add imports I'm not using?"
-> Answer: "I copied from reference but didn't use all the features"
-> Fix: Review what I actually need, remove all unused at once
```

### Fix Attempt Limits (Prevents Infinite Loops)

**You have a maximum of 3 fix attempts per gate.** Track your attempts:

```
FIX_ATTEMPTS:
- LINT: 0/3
- TYPECHECK: 0/3
- BUILD: 0/3
- TESTS: 0/3
```

**Rules:**
1. Each time you modify code to fix a gate failure, increment that gate's counter
2. If a gate still fails after 3 fix attempts, **STOP and ESCALATE**
3. Do NOT keep trying different fixes indefinitely

### Escalation Protocol

**After 3 failed fix attempts, you MUST:**

1. **STOP** - Do not attempt more fixes
2. **Document** the error and what you tried:
   ```
   ESCALATION REQUIRED:
   Gate: {LINT|TYPECHECK|BUILD|TESTS}
   Attempts: 3/3
   Last Error: [exact error message]
   Fixes Tried:
   1. [what you tried]
   2. [what you tried]
   3. [what you tried]
   Root Cause Analysis: [why fixes aren't working]
   ```
3. **Notify the user** and pause for human intervention

---

## Gate Summary

```
**Quality Gates:**
- {icon} Build: {status}
- {icon} Tests: {status}       <- REQUIRED
- {icon} Lint: {status}        <- REQUIRED
- {icon} TypeCheck: {status}   <- REQUIRED
- {icon} Feature Verify: {status}
```

**If tests were not run, verification has NOT passed.**
