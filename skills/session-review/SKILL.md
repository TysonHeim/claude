---
name: session-review
description: Review the current session for mistakes and log corrections. Use when user says "review session", "session review", or before exiting to capture learnings.
---

# Session Review

Review the current conversation for any mistakes made and log corrections for future improvement.

## Process

1. **Scan the conversation** for instances where:
   - You made an error that was corrected (by user feedback or self-correction)
   - You used the wrong approach and had to change it
   - You misunderstood requirements
   - You used a tool incorrectly
   - You made assumptions that turned out to be wrong

2. **For each mistake found**, create a correction entry in the format:
   ```
   - Don't X, instead Y
   ```

3. **If corrections are needed**, use the Edit tool to append them to `~/.claude/CLAUDE.md` under a `## Corrections` section.

4. **Respond with either**:
   - A brief summary of corrections added (if any mistakes were found)
   - A brief summary of what was accomplished (if no mistakes were made)

## Example Corrections

Good correction entries:
- `- Don't use Bash grep for searching code, instead use the Grep tool`
- `- Don't assume ticket IDs are short form, instead always use full format like PROJ-1234`
- `- Don't create new files when editing existing ones would work, instead prefer modifying existing code`

## Guidelines

- Be honest about mistakes - the goal is improvement
- Focus on actionable corrections that will help in future sessions
- Don't be overly critical - only log genuine errors that impacted the work
- Keep corrections concise and specific
