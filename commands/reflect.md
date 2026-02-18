---
description: Propose updates to skills used in this session based on learnings and improvements discovered
---

# Skill Reflection

Review skills used during this session and propose improvements based on learnings.

## Process

1. **Identify Skills Used**
   - Review the conversation for any `Skill(...)` invocations
   - Note which skills were loaded/referenced
   - Identify patterns that emerged during implementation

2. **Analyze Each Skill for Improvements**
   For each skill used, consider:
   - **Missing information**: Did you need to look up something not in the skill?
   - **Outdated patterns**: Did you use a better pattern than what the skill suggested?
   - **New edge cases**: Did you encounter scenarios the skill doesn't cover?
   - **Redundant content**: Is there information that wasn't useful?
   - **Better examples**: Did you write code that would make a good example?
   - **Corrections**: Did the skill have any errors or misleading guidance?

3. **Generate Suggestions**
   For each proposed update, document:
   - **Skill name**: Which skill to update
   - **Section**: Where in the skill the change applies
   - **Current state**: Brief description of what exists (or "missing")
   - **Proposed change**: Specific improvement with example content
   - **Rationale**: Why this improves the skill

4. **Log Suggestions**
   Append suggestions to `.claude/skill-suggestions.md` with timestamp.
   Create the file if it doesn't exist.

## Output Format

```markdown
## Skill Reflection - [DATE]

### Skills Used This Session
- skill-name-1
- skill-name-2

### Proposed Updates

#### [skill-name] - [Brief Title]
**Section:** [section name or "new section"]
**Current:** [what exists now or "missing"]
**Proposed:**
[proposed content/changes]
**Rationale:** [why this helps]

---

[Repeat for each suggestion]
```

## After Reflection

Ask user:
1. "Would you like me to apply any of these updates now?"
2. If yes, use the skills-manager agent to make the edits
3. Mark applied suggestions as "APPLIED" in the log

## Important Notes

- Focus on **actionable, specific** improvements
- Prefer small, targeted changes over large rewrites
- Include actual code/text examples when proposing additions
- If no improvements found, acknowledge the skills worked well
- Don't suggest changes for hypothetical scenarios - only actual session learnings
