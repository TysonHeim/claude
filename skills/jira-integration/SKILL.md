---
name: jira-integration
description: |
  Jira integration - fetch stories, post comments, update custom fields,
  assign tickets, transition status, add labels, and create issue links.

  Use when: "fetch Jira", "get story PROJ-XXXX", "post comment", "assign ticket",
  "move to status", "transition", "add label", "update fields", "link issues",
  or any Jira ticket interaction.
---

# Jira Integration

Complete Jira workflow for project board operations.

## Directory Structure

```
scripts/
├── env_loader.py           # Shared: loads .env credentials
└── core/                   # Jira operations
    ├── jira_fetch.py       # Fetch story details
    ├── jira_search.py      # Search issues with JQL + custom fields
    ├── jira_comment.py     # Post comments (Markdown → ADF)
    ├── jira_create.py      # Create new issues
    ├── jira_label.py       # Add/remove labels
    ├── jira_label_bulk.py  # Bulk label operations
    ├── jira_assign.py      # Assign tickets
    ├── jira_transition.py  # Change status
    ├── jira_attach.py      # Upload attachments
    ├── jira_update.py      # Update custom fields
    └── jira_link.py        # Create issue links (blocks, relates, etc.)
```

---

## CRITICAL: No Inline Python

**NEVER generate inline `python3 -c "..."` scripts for Jira operations.** Always use the provided scripts below.
The Jira REST API v2 is deprecated (returns **410 Gone**). All scripts use v3 endpoints.
If a script doesn't support a needed feature, add it to the script — don't write throwaway inline code.

---

## Quick Reference

### Fetch Story
```bash
python3 ~/.claude/skills/jira-integration/scripts/core/jira_fetch.py PROJ-1234
```

### Search Issues (JQL + AI Fields)
```bash
# Find tickets by assignee and status
python3 ~/.claude/skills/jira-integration/scripts/core/jira_search.py --assignee user@example.com --status "Dev Testing"

# Find all tickets with AI Status = "PR Created"
python3 ~/.claude/skills/jira-integration/scripts/core/jira_search.py --ai-status "PR Created"

# Find AI-assigned tickets
python3 ~/.claude/skills/jira-integration/scripts/core/jira_search.py --ai-assigned

# Combine filters
python3 ~/.claude/skills/jira-integration/scripts/core/jira_search.py --ai-assigned --ai-status "Implementing"

# Raw JQL query
python3 ~/.claude/skills/jira-integration/scripts/core/jira_search.py --jql 'project = YOUR_PROJECT AND status = "In Progress"'

# Skip AI fields for faster queries
python3 ~/.claude/skills/jira-integration/scripts/core/jira_search.py --status "In Progress" --no-ai-fields

# JSON output
python3 ~/.claude/skills/jira-integration/scripts/core/jira_search.py --ai-status "PR Created" --format json
```

### Post Comment
```bash
python3 ~/.claude/skills/jira-integration/scripts/core/jira_comment.py PROJ-1234 "Comment text"
```

**⚠️ Comment Formatting: Use MARKDOWN, not Jira wiki markup!**

The script converts Markdown → Atlassian Document Format (ADF). Supported syntax:

| Markdown | Result |
|----------|--------|
| `# Header` | H1 heading |
| `## Header` | H2 heading |
| `### Header` | H3 heading |
| `**bold**` | Bold text |
| `- item` or `* item` | Bullet list |
| `1. item` | Numbered list |
| `` `code` `` | Inline code |
| ` ``` ` blocks | Code blocks |
| `[~accountid:xxx]` | Mention user (passed through) |

**❌ Does NOT work:** `h3.`, `||table||`, `{code}`, `*bold*` (single asterisk), `_italic_`

Example well-formatted comment:
```bash
python3 ~/.claude/skills/jira-integration/scripts/core/jira_comment.py PROJ-1234 "### Summary

**Status:** Complete

- Item one
- Item two

1. First step
2. Second step"
```

### Add/Remove Labels
```bash
# Add labels
python3 ~/.claude/skills/jira-integration/scripts/core/jira_label.py PROJ-1234 AI engineer-review

# Remove labels
python3 ~/.claude/skills/jira-integration/scripts/core/jira_label.py PROJ-1234 --remove AI
```

### Assign Ticket
```bash
python3 ~/.claude/skills/jira-integration/scripts/core/jira_assign.py PROJ-1234 ai
python3 ~/.claude/skills/jira-integration/scripts/core/jira_assign.py PROJ-1234 user@email.com
python3 ~/.claude/skills/jira-integration/scripts/core/jira_assign.py PROJ-1234 unassigned
```

### Transition Status
```bash
python3 ~/.claude/skills/jira-integration/scripts/core/jira_transition.py PROJ-1234 "In Progress"
python3 ~/.claude/skills/jira-integration/scripts/core/jira_transition.py PROJ-1234 --list  # Show available
```

### Upload Attachments
```bash
python3 ~/.claude/skills/jira-integration/scripts/core/jira_attach.py PROJ-1234 screenshot.png
```

### Update Custom Fields
```bash
python3 ~/.claude/skills/jira-integration/scripts/core/jira_update.py PROJ-1234 \
  --field "Custom Field Name" --value "some value"

# List all custom fields
python3 ~/.claude/skills/jira-integration/scripts/core/jira_update.py --list-fields
```

### Link Issues (Blocks, Relates)
```bash
# PROJ-100 blocks PROJ-101 (PROJ-101 cannot start until PROJ-100 is done)
python3 ~/.claude/skills/jira-integration/scripts/core/jira_link.py PROJ-100 --blocks PROJ-101

# PROJ-100 blocks multiple issues
python3 ~/.claude/skills/jira-integration/scripts/core/jira_link.py PROJ-100 --blocks PROJ-101 PROJ-102 PROJ-103

# PROJ-100 is blocked by PROJ-99
python3 ~/.claude/skills/jira-integration/scripts/core/jira_link.py PROJ-100 --blocked-by PROJ-99
```

**⚠️ IMPORTANT: Jira "Blocks" Link Direction**

The Jira API uses **counter-intuitive naming** for the Blocks link type:
- `inwardIssue` = the issue that **blocks** (shows "blocks X")
- `outwardIssue` = the issue that **is blocked** (shows "is blocked by X")

When using the REST API directly, to make "A blocks B":
```json
{
  "type": { "name": "Blocks" },
  "outwardIssue": { "key": "B" },   // B is blocked
  "inwardIssue": { "key": "A" }     // A blocks
}
```

The `jira_link.py` script handles this correctly - just use `--blocks` or `--blocked-by` naturally.

---

## Script Reference

### Core Scripts (`scripts/core/`)

| Script | Purpose |
|--------|---------|
| `jira_fetch.py` | Get story details (title, description, AC, comments) |
| `jira_search.py` | Search issues with JQL, includes AI custom fields |
| `jira_comment.py` | Post comments to tickets |
| `jira_label.py` | Add or remove labels |
| `jira_assign.py` | Assign/unassign tickets |
| `jira_transition.py` | Change ticket status |
| `jira_attach.py` | Upload file attachments |
| `jira_update.py` | Update custom fields |
| `jira_create.py` | Create new issues |
| `jira_label_bulk.py` | Bulk label rename/remove |
| `jira_link.py` | Create issue links (blocks, relates, etc.) |

---

## Environment Variables

Required in `~/.claude/.env`:

```bash
JIRA_BASE_URL=https://your-org.atlassian.net
JIRA_EMAIL=your.email@example.com
JIRA_TOKEN=your-api-token
JIRA_PROJECT=YOUR_PROJECT          # Default project key for JQL queries
```

Scripts auto-load via `env_loader.py`.

---

## References

- [fetch-comment.md](references/fetch-comment.md) - Script details
- [story-creation.md](references/story-creation.md) - REST API format
- [ai-fields-setup.md](references/ai-fields-setup.md) - Custom field setup (optional)

