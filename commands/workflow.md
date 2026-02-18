---
description: Enforces disciplined workflow - plan first, research existing patterns, simplify, and validate
---

You MUST follow this workflow for the current task:

## 1. Plan First (MANDATORY)
Use TodoWrite to break down the task before any implementation.

## 2. Research Existing Patterns (MANDATORY)
Use Task tool with subagent_type=Explore to find existing similar implementations and understand project patterns.

## 3. Ask Questions (MANDATORY when unclear)
Use AskUserQuestion if requirements are ambiguous or multiple approaches exist.

## 4. Simplify (MANDATORY mindset)
- Prefer the simplest solution that works
- YAGNI principle - don't over-engineer
- Don't create new files when editing works
- Avoid premature abstraction

## 5. Implement Incrementally
Work through todos one at a time, marking complete immediately.

## Anti-Patterns to AVOID:
- Overcomplication - no elaborate abstractions for simple needs
- Skipping research - always check existing patterns first
- Assuming requirements - ask when unclear
- Creating files unnecessarily - prefer editing existing

Remember: Simple working code following project patterns > clever complex solutions
