---
description: Senior engineer code review using 5-Whys to drill from surface issues to root causes. Use after making changes to understand deeper patterns.
---

Act as a senior engineer critiquing recent changes. Use the "5 Whys" technique to drill past surface issues to root causes.

## Process

1. **Surface Issues**: List concrete problems (code quality, patterns, architecture)

2. **5 Whys Drill-Down**: For each significant issue, ask "Why?" 5 times:
   - Issue -> Why problem? -> Why matter? -> Why? -> Why? -> ROOT CAUSE

3. **Categorize Root Causes**:
   - Knowledge gap (don't know the pattern)
   - Process gap (skipped design/testing/reading code)
   - Habit (repeated bad practice)
   - Tooling (missing guardrails)

4. **Prescribe Actions**: What to learn, practice, or stop doing

## Output

For each major issue:
- **Surface**: What's wrong
- **Why 1-4**: Drill down
- **Root Cause**: Big picture issue

Then:
- **Patterns**: Themes across issues
- **Growth Actions**: Specific next steps
- **Verdict**: Harsh but fair assessment

## Rules

- Don't stop at surface - always drill to root cause
- Connect to bigger patterns when possible
- Update `.claude/report-card.md` if significant patterns emerge

Start by reviewing uncommitted changes or ask what to review.
