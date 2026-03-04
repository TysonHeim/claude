# Fetch & Comment Scripts

Detailed usage for Jira Python scripts.

## jira_fetch.py

### Basic Usage
```bash
python .claude/skills/jira-integration/scripts/jira_fetch.py PROJ-1234
python .claude/skills/jira-integration/scripts/jira_fetch.py PROJ-1234 --format text
python .claude/skills/jira-integration/scripts/jira_fetch.py PROJ-1234 --format json
```

### Output Format (text)
```
Title: Add payment template filtering
Status: In Progress
Story Points: 5
Sprint: Sprint 42
Assignee: developer@company.com

Description:
As a user, I want to filter payment templates...

Acceptance Criteria:
- [ ] Filter by initiator access
- [ ] Filter by beneficiary access
- [ ] Update repository method

Comments (3):
---
[2024-01-15 10:30] John Doe:
Please also consider edge cases...
---
[2024-01-14 09:00] Jane Smith:
Approved for implementation
```

### Output Format (json)
```json
{
  "key": "PROJ-1234",
  "title": "Add payment template filtering",
  "status": "In Progress",
  "storyPoints": 5,
  "sprint": "Sprint 42",
  "description": "As a user...",
  "acceptanceCriteria": ["AC1", "AC2"],
  "comments": [...]
}
```

### Error Handling
```bash
# Invalid ticket
python .claude/skills/jira-integration/scripts/jira_fetch.py INVALID-999
# Error: Ticket not found

# Auth failure
# Error: Authentication failed. Check JIRA_TOKEN environment variable.
```

## jira_comment.py

### Basic Usage
```bash
python .claude/skills/jira-integration/scripts/jira_comment.py PROJ-1234 "Simple comment"
```

### Multiline Comments
```bash
python .claude/skills/jira-integration/scripts/jira_comment.py PROJ-1234 "## Header
- Point 1
- Point 2

More text here"
```

### With File Content
```bash
python .claude/skills/jira-integration/scripts/jira_comment.py PROJ-1234 "$(cat plan.md)"
```

### Formatting Support

**Markdown (converted to Jira wiki):**
```markdown
## Heading
**bold** and *italic*
- bullet point
1. numbered
`inline code`
```

**Code Blocks:**
```bash
python .claude/skills/jira-integration/scripts/jira_comment.py PROJ-1234 "{code:java}
public void method() {
    // code here
}
{code}"
```

### Response
```
Comment posted successfully to PROJ-1234
Comment ID: 12345
```

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `JIRA_BASE_URL` | Jira instance URL |
| `JIRA_TOKEN` | API token for auth |
| `JIRA_EMAIL` | Account email |

## Common Patterns

### Fetch → Analyze → Comment
```bash
# Get story
output=$(python .claude/skills/jira-integration/scripts/jira_fetch.py PROJ-1234 --format text)

# ... analyze and plan ...

# Post plan
python .claude/skills/jira-integration/scripts/jira_comment.py PROJ-1234 "[AUTONOMOUS-PLAN]
Based on the story requirements...
"
```

### Check Before Acting
```bash
# Always fetch latest before posting
python .claude/skills/jira-integration/scripts/jira_fetch.py PROJ-1234 --format text | grep "Status:"
```
