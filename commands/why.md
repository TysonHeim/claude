# Five Whys Root Cause Analysis

You are conducting a Five Whys analysis to identify the root cause of an issue.

## Instructions

1. **Problem Statement**: Start by clearly restating the problem or symptom described by the user.

2. **Iterative Analysis**: Ask "Why did this happen?" for each answer, drilling down through at least 5 levels (or until you reach a fundamental root cause):
   - **Why 1**: Why did the initial problem occur?
   - **Why 2**: Why did that cause happen?
   - **Why 3**: Why did that underlying issue exist?
   - **Why 4**: Why wasn't that prevented?
   - **Why 5**: What is the fundamental root cause?

3. **Validation**: Work backwards from the root cause to verify the causal chain makes sense.

4. **Root Cause Summary**: Clearly state the identified root cause(s).

5. **Proposed Solutions**: Recommend concrete actions that address the root cause (not just symptoms).

## Output Format

\`\`\`
## Problem Statement
[Restate the issue clearly]

## Five Whys Analysis

**Why 1**: [First-level cause]
→ [Explanation]

**Why 2**: [Second-level cause]
→ [Explanation]

**Why 3**: [Third-level cause]
→ [Explanation]

**Why 4**: [Fourth-level cause]
→ [Explanation]

**Why 5**: [Root cause]
→ [Explanation]

## Validation
[Verify the causal chain by working backwards]

## Root Cause
[Clear statement of the fundamental root cause]

## Recommended Solutions
1. [Solution addressing root cause]
2. [Solution addressing root cause]
3. [Preventive measures]
\`\`\`

## Guidelines

- Focus on **systemic causes** not individual blame
- Look for **process failures** and **missing controls**
- Each "why" should reveal a **deeper level of causation**
- Stop when you reach a **manageable root cause** that can be addressed
- If multiple root causes exist, explore each branch
- Distinguish between **contributing factors** and **root causes**

## Example Context

If analyzing a code issue:
- Consider: code quality, testing, deployment, monitoring, documentation, team processes
- Look for: missing safeguards, inadequate reviews, unclear requirements, technical debt

If analyzing a test failure:
- Consider: test design, data setup, environment, timing, dependencies
- Look for: flaky tests, missing assertions, incomplete coverage, brittle fixtures
