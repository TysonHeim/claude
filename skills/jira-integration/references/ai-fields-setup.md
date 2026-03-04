# AI Workflow Custom Fields Setup

This guide documents the Jira custom fields needed for AI workflow tracking.

## Required Custom Fields

Create these fields in Jira Admin → Issues → Custom Fields:

### 1. AI Status (Single Select)

| Setting | Value |
|---------|-------|
| **Name** | AI Status |
| **Type** | Select List (single choice) |
| **Context** | your project (or global) |
| **Options** | None, Planning, Awaiting Approval, Approved, Implementing, Verifying, PR Created, Done, Blocked |
| **Default** | None |

**Purpose:** Tracks current phase of AI automation workflow.

### 2. AI Mode (Single Select)

| Setting | Value |
|---------|-------|
| **Name** | AI Mode |
| **Type** | Select List (single choice) |
| **Options** | SE, PARTIAL, FULL |
| **Default** | (none) |

**Purpose:** Indicates automation level.
- **SE**: Engineer-assisted (normal workflow)
- **PARTIAL**: AI works in background, engineer reviews
- **FULL**: Fully autonomous (frontend/controller only)

### 3. AI Branch (Text)

| Setting | Value |
|---------|-------|
| **Name** | AI Branch |
| **Type** | Text Field (single line) |

**Purpose:** Stores the git branch name (e.g., `story/proj-1234`).

### 4. AI PR URL (URL)

| Setting | Value |
|---------|-------|
| **Name** | AI PR URL |
| **Type** | URL Field |

**Purpose:** Link to the pull request in Azure DevOps.

### 5. AI Plan Approved (Checkbox)

| Setting | Value |
|---------|-------|
| **Name** | AI Plan Approved |
| **Type** | Checkboxes |
| **Options** | Approved |

**Purpose:** Explicit approval flag for implementation plan.

### 6. AI Last Phase (Text)

| Setting | Value |
|---------|-------|
| **Name** | AI Last Phase |
| **Type** | Text Field (single line) |

**Purpose:** Stores last completed phase (phase1, phase2, etc.) for debugging.

---

## After Creating Fields

### 1. Fields Created (2025-01-07)

| Field | ID | Type |
|-------|-----|------|
| AI Status | `customfield_10960` | Select |
| AI Mode | `customfield_10961` | Select |
| AI Branch | `customfield_10956` | Text |
| AI PR URL | `customfield_10957` | URL |
| AI Plan Approved | `customfield_10958` | Checkbox |
| AI Last Phase | `customfield_10959` | Text |

### 2. Add Fields to Screens (REQUIRED)

The fields are created but **must be added to issue screens** before they can be edited via API.

**Steps (requires Jira Admin):**

1. Go to **Jira Settings** → **Issues** → **Screens**
2. Find the screen used by your project (usually "Default Screen" or a project-specific screen)
3. Click **Configure** on that screen
4. Add these fields:
   - AI Status
   - AI Mode
   - AI Branch
   - AI PR URL
   - AI Plan Approved
   - AI Last Phase

**Alternative: Field Configuration Scheme**

1. Go to **Jira Settings** → **Issues** → **Field configurations**
2. Edit the configuration used by your project
3. Ensure AI fields are not "hidden"

### 3. Verify

```bash
python ~/.claude/skills/jira-integration/scripts/core/jira_update.py PROJ-502 --ai-status "Planning"
```

---

**Current Status:** ✅ Custom fields configured and working (2025-01-07).

---

## Recommended Board Configuration

### Board Columns with AI Status Filter

Create a board filter or swimlane:

| Swimlane | Filter |
|----------|--------|
| AI Working | `"AI Status" IN ("Planning", "Implementing", "Verifying")` |
| Awaiting Approval | `"AI Status" = "Awaiting Approval"` |
| Normal | `"AI Status" IS EMPTY OR "AI Status" = "None"` |

### Quick Filters

| Filter Name | JQL |
|-------------|-----|
| AI Tickets | `"AI Mode" IS NOT EMPTY` |
| Full Auto | `"AI Mode" = "FULL"` |
| Needs Approval | `"AI Status" = "Awaiting Approval"` |
| AI Blocked | `"AI Status" = "Blocked"` |

---

## Dashboard Gadgets

### AI Automation Stats

Create a pie chart gadget with:
```jql
project = YOUR_PROJECT AND "AI Mode" IS NOT EMPTY AND created >= -30d
```
Group by: AI Status

### Pending Approvals

Create a filter results gadget:
```jql
project = YOUR_PROJECT AND "AI Status" = "Awaiting Approval" ORDER BY created ASC
```

---

## Field Visibility

Consider hiding AI fields from non-engineering views:
- **Board Card:** Don't add AI fields to card layout
- **Issue Detail:** Add to a collapsible "AI Automation" panel
- **Create Screen:** Don't add (AI sets these programmatically)
