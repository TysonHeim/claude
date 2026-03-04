#!/usr/bin/env python3
"""Update Jira issue fields for AI workflow tracking."""

import argparse
import json
import os
import re
import sys

# Auto-load .env file
# Add parent dir to path for env_loader
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import env_loader  # noqa: F401

from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import base64


def parse_inline(text: str) -> list:
    """Parse inline markdown formatting (bold, code)."""
    result = []
    if text:
        parts = re.split(r'(`[^`]+`)', text)
        for part in parts:
            if part.startswith('`') and part.endswith('`'):
                result.append({
                    "type": "text",
                    "text": part[1:-1],
                    "marks": [{"type": "code"}]
                })
            elif part:
                bold_parts = re.split(r'(\*\*[^*]+\*\*)', part)
                for bp in bold_parts:
                    if bp.startswith('**') and bp.endswith('**'):
                        result.append({
                            "type": "text",
                            "text": bp[2:-2],
                            "marks": [{"type": "strong"}]
                        })
                    elif bp:
                        result.append({"type": "text", "text": bp})
    return result if result else [{"type": "text", "text": " "}]


def markdown_to_adf(text: str) -> dict:
    """Convert markdown text to Atlassian Document Format."""
    content = []
    lines = text.split("\n")
    i = 0

    while i < len(lines):
        line = lines[i]

        if line.startswith("### "):
            content.append({
                "type": "heading",
                "attrs": {"level": 3},
                "content": [{"type": "text", "text": line[4:]}]
            })
        elif line.startswith("## "):
            content.append({
                "type": "heading",
                "attrs": {"level": 2},
                "content": [{"type": "text", "text": line[3:]}]
            })
        elif line.startswith("# "):
            content.append({
                "type": "heading",
                "attrs": {"level": 1},
                "content": [{"type": "text", "text": line[2:]}]
            })
        elif line.startswith("- ") or line.startswith("* "):
            list_items = []
            while i < len(lines) and (lines[i].startswith("- ") or lines[i].startswith("* ")):
                item_text = lines[i][2:]
                list_items.append({
                    "type": "listItem",
                    "content": [{"type": "paragraph", "content": parse_inline(item_text)}]
                })
                i += 1
            content.append({"type": "bulletList", "content": list_items})
            continue
        elif re.match(r"^\d+\. ", line):
            list_items = []
            while i < len(lines) and re.match(r"^\d+\. ", lines[i]):
                item_text = re.sub(r"^\d+\. ", "", lines[i])
                list_items.append({
                    "type": "listItem",
                    "content": [{"type": "paragraph", "content": parse_inline(item_text)}]
                })
                i += 1
            content.append({"type": "orderedList", "content": list_items})
            continue
        elif line.startswith("```"):
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                code_lines.append(lines[i])
                i += 1
            content.append({
                "type": "codeBlock",
                "content": [{"type": "text", "text": "\n".join(code_lines)}]
            })
        elif line.strip():
            content.append({"type": "paragraph", "content": parse_inline(line)})

        i += 1

    return {
        "version": 1,
        "type": "doc",
        "content": content if content else [
            {"type": "paragraph", "content": [{"type": "text", "text": text}]}
        ]
    }


# Custom field mappings - Created 2025-01-07
# To find field IDs: GET /rest/api/3/field or check Jira admin
FIELD_MAPPINGS = {
    # AI Workflow Fields
    "ai_status": "customfield_10960",      # Single select: None, Planning, Awaiting Approval, Approved, Implementing, Verifying, PR Created, Done, Blocked
    "ai_mode": "customfield_10961",        # Single select: SE, PARTIAL, FULL
    "ai_branch": "customfield_10956",      # Short text
    "ai_pr_url": "customfield_10957",      # URL field
    "ai_plan_approved": "customfield_10958",  # Checkbox
    "ai_last_phase": "customfield_10959",  # Short text (phase1, phase2, etc.)

    # Story Points - uses env var override or common default
    "story_points": os.environ.get("JIRA_STORY_POINTS_FIELD", "customfield_10016"),

    # Standard fields (no customfield_ prefix needed)
    "summary": "summary",
    "description": "description",
    "assignee": "assignee",
    "labels": "labels",
}

# Valid values for select fields
AI_STATUS_VALUES = [
    "None",
    "Planning",
    "Awaiting Approval",
    "Approved",
    "Implementing",
    "Verifying",
    "PR Created",
    "Done",
    "Blocked"
]

AI_MODE_VALUES = ["SE", "PARTIAL", "FULL"]


def get_auth_header():
    """Get base64 encoded auth header."""
    email = os.environ.get("JIRA_EMAIL")
    token = os.environ.get("JIRA_TOKEN")

    if not email or not token:
        print("Error: JIRA_EMAIL and JIRA_TOKEN environment variables required.", file=sys.stderr)
        sys.exit(1)

    credentials = f"{email}:{token}"
    encoded = base64.b64encode(credentials.encode()).decode()
    return f"Basic {encoded}"


def get_base_url():
    """Get Jira base URL."""
    base_url = os.environ.get("JIRA_BASE_URL")
    if not base_url:
        print("Error: JIRA_BASE_URL environment variable required.", file=sys.stderr)
        sys.exit(1)
    return base_url.rstrip('/')


def update_issue(issue_key: str, fields: dict) -> bool:
    """Update issue fields via Jira API."""
    url = f"{get_base_url()}/rest/api/3/issue/{issue_key}"

    body = {"fields": fields}
    data = json.dumps(body).encode('utf-8')

    req = Request(url, data=data, method='PUT')
    req.add_header("Authorization", get_auth_header())
    req.add_header("Accept", "application/json")
    req.add_header("Content-Type", "application/json")

    try:
        with urlopen(req) as response:
            return True
    except HTTPError as e:
        if e.code == 404:
            print(f"Error: Ticket {issue_key} not found.", file=sys.stderr)
        elif e.code == 401:
            print("Error: Authentication failed.", file=sys.stderr)
        elif e.code == 400:
            error_body = e.read().decode() if e.fp else ""
            print(f"Error: Bad request - {error_body}", file=sys.stderr)
        else:
            print(f"Error: HTTP {e.code} - {e.reason}", file=sys.stderr)
        return False
    except URLError as e:
        print(f"Error: Could not connect to Jira - {e.reason}", file=sys.stderr)
        return False


def build_field_value(field_name: str, value: str) -> any:
    """Build the appropriate field value structure for Jira API."""
    # Select fields need {"value": "..."} format
    if field_name in ["ai_status", "ai_mode"]:
        return {"value": value}

    # Checkbox fields need [{"value": "..."}] array format
    if field_name == "ai_plan_approved":
        if value.lower() in ["true", "yes", "1"]:
            return [{"value": "Approved"}]
        return []  # Empty array to uncheck

    # Assignee needs {"accountId": "..."} or {"emailAddress": "..."}
    if field_name == "assignee":
        if value.lower() == "unassigned":
            return None
        return {"emailAddress": value}

    # Labels need array format
    if field_name == "labels":
        return value.split(",")

    # Story points need numeric value
    if field_name == "story_points":
        return float(value)

    # Description needs ADF format
    if field_name == "description":
        return markdown_to_adf(value)

    # Text fields are just strings
    return value


def get_ai_state(issue_key: str) -> dict:
    """Read AI state from custom fields."""
    url = f"{get_base_url()}/rest/api/3/issue/{issue_key}?fields={','.join([
        FIELD_MAPPINGS['ai_status'],
        FIELD_MAPPINGS['ai_mode'],
        FIELD_MAPPINGS['ai_branch'],
        FIELD_MAPPINGS['ai_pr_url'],
        FIELD_MAPPINGS['ai_plan_approved'],
        FIELD_MAPPINGS['ai_last_phase'],
    ])}"

    req = Request(url)
    req.add_header("Authorization", get_auth_header())
    req.add_header("Accept", "application/json")

    state = {
        "ai_status": None,
        "ai_mode": None,
        "ai_plan_approved": False,
        "ai_last_phase": None,
        "ai_branch": None,
        "ai_pr_url": None,
    }

    try:
        with urlopen(req) as response:
            data = json.loads(response.read().decode())
            fields = data.get("fields", {})

            # Extract select field values
            status_field = fields.get(FIELD_MAPPINGS["ai_status"])
            if status_field and isinstance(status_field, dict):
                state["ai_status"] = status_field.get("value")

            mode_field = fields.get(FIELD_MAPPINGS["ai_mode"])
            if mode_field and isinstance(mode_field, dict):
                state["ai_mode"] = mode_field.get("value")

            # Extract text fields
            state["ai_branch"] = fields.get(FIELD_MAPPINGS["ai_branch"])
            state["ai_pr_url"] = fields.get(FIELD_MAPPINGS["ai_pr_url"])
            state["ai_last_phase"] = fields.get(FIELD_MAPPINGS["ai_last_phase"])

            # Extract checkbox (array of selected options)
            approved_field = fields.get(FIELD_MAPPINGS["ai_plan_approved"])
            if approved_field and isinstance(approved_field, list):
                state["ai_plan_approved"] = any(opt.get("value") == "Approved" for opt in approved_field)

    except (HTTPError, URLError) as e:
        print(f"Error reading fields: {e}", file=sys.stderr)

    return state


def list_fields():
    """Fetch and list all available fields."""
    url = f"{get_base_url()}/rest/api/3/field"

    req = Request(url)
    req.add_header("Authorization", get_auth_header())
    req.add_header("Accept", "application/json")

    try:
        with urlopen(req) as response:
            fields = json.loads(response.read().decode())

            print("Custom Fields (look for AI-related ones):")
            print("-" * 60)
            for field in sorted(fields, key=lambda f: f.get("name", "")):
                if field.get("custom", False):
                    field_id = field.get("id", "")
                    name = field.get("name", "")
                    field_type = field.get("schema", {}).get("type", "unknown")
                    print(f"  {field_id}: {name} ({field_type})")

            return True
    except HTTPError as e:
        print(f"Error: HTTP {e.code} - {e.reason}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Update Jira issue fields for AI workflow tracking",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Set AI status to "Implementing"
  %(prog)s PROJ-1234 --ai-status "Implementing"

  # Set multiple fields at once
  %(prog)s PROJ-1234 --ai-status "PR Created" --ai-branch "story/proj-1234" --ai-pr-url "https://..."

  # Clear AI tracking (reset to None)
  %(prog)s PROJ-1234 --ai-status "None" --ai-mode "" --ai-branch ""

  # List all custom fields (to find field IDs)
  %(prog)s --list-fields
"""
    )

    parser.add_argument("issue_key", nargs="?", help="Jira issue key (e.g., PROJ-1234)")
    parser.add_argument("--list-fields", action="store_true", help="List all custom fields")
    parser.add_argument("--get", action="store_true", help="Get current AI state (read-only)")

    # AI workflow fields
    parser.add_argument("--ai-status", choices=AI_STATUS_VALUES, metavar="STATUS",
                        help=f"AI Status: {', '.join(AI_STATUS_VALUES)}")
    parser.add_argument("--ai-mode", choices=AI_MODE_VALUES, metavar="MODE",
                        help=f"AI Mode: {', '.join(AI_MODE_VALUES)}")
    parser.add_argument("--ai-branch", metavar="BRANCH", help="Git branch name")
    parser.add_argument("--ai-pr-url", metavar="URL", help="Pull request URL")
    parser.add_argument("--ai-plan-approved", choices=["true", "false"],
                        help="Plan approved flag")
    parser.add_argument("--ai-last-phase", metavar="PHASE", help="Last completed phase")
    parser.add_argument("--story-points", metavar="POINTS", type=float,
                        help="Story points estimate (1, 2, 3, 5, 8, 13)")

    # Standard issue fields
    parser.add_argument("--summary", metavar="TEXT", help="Issue summary/title")
    parser.add_argument("--description", metavar="MARKDOWN",
                        help="Issue description in Markdown (converted to ADF)")

    args = parser.parse_args()

    # Handle --list-fields
    if args.list_fields:
        list_fields()
        sys.exit(0)

    # Require issue key for updates
    if not args.issue_key:
        parser.error("issue_key is required unless using --list-fields")

    # Handle --get (read current AI state)
    if args.get:
        state = get_ai_state(args.issue_key)
        print(f"AI State for {args.issue_key}:")
        print(f"  ai_status: {state['ai_status'] or '(not set)'}")
        print(f"  ai_mode: {state['ai_mode'] or '(not set)'}")
        print(f"  ai_branch: {state['ai_branch'] or '(not set)'}")
        print(f"  ai_pr_url: {state['ai_pr_url'] or '(not set)'}")
        print(f"  ai_plan_approved: {state['ai_plan_approved']}")
        print(f"  ai_last_phase: {state['ai_last_phase'] or '(not set)'}")
        # Also output as JSON for parsing
        print(f"\nJSON: {json.dumps(state)}")
        sys.exit(0)

    # Collect AI field updates
    field_args = [
        ("ai_status", args.ai_status),
        ("ai_mode", args.ai_mode),
        ("ai_branch", args.ai_branch),
        ("ai_pr_url", args.ai_pr_url),
        ("ai_plan_approved", args.ai_plan_approved),
        ("ai_last_phase", args.ai_last_phase),
        ("story_points", str(args.story_points) if args.story_points is not None else None),
        ("summary", args.summary),
        ("description", args.description),
    ]

    # Build fields for custom field update
    fields = {}
    for field_name, value in field_args:
        if value is not None:
            jira_field = FIELD_MAPPINGS.get(field_name)
            if jira_field is None:
                print(f"Warning: {field_name} field ID not configured.", file=sys.stderr)
                continue
            fields[jira_field] = build_field_value(field_name, value)

    if not fields:
        parser.error("At least one field to update is required")

    # Perform update
    if update_issue(args.issue_key, fields):
        print(f"Successfully updated {args.issue_key}")
        for field_name, value in field_args:
            if value is not None:
                print(f"  {field_name}: {value}")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
