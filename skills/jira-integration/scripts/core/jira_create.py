#!/usr/bin/env python3
"""Create a new Jira issue.

Usage:
  python3 jira_create.py "Summary title"
  python3 jira_create.py "Summary title" --description "Markdown description"
  python3 jira_create.py "Summary title" --type Task --labels tech-debt debt4 --points 3
"""

import argparse
import json
import os
import sys

# Auto-load .env file
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import env_loader  # noqa: F401

from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import base64
import re


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


def markdown_to_adf(text: str) -> dict:
    """Convert markdown text to Atlassian Document Format."""
    content = []
    lines = text.split("\n")
    i = 0

    while i < len(lines):
        line = lines[i]

        # Headers
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
        # Bullet points
        elif line.startswith("- ") or line.startswith("* "):
            list_items = []
            while i < len(lines) and (lines[i].startswith("- ") or lines[i].startswith("* ")):
                item_text = lines[i][2:]
                list_items.append({
                    "type": "listItem",
                    "content": [{
                        "type": "paragraph",
                        "content": parse_inline(item_text)
                    }]
                })
                i += 1
            content.append({
                "type": "bulletList",
                "content": list_items
            })
            continue
        # Numbered lists
        elif re.match(r"^\d+\. ", line):
            list_items = []
            while i < len(lines) and re.match(r"^\d+\. ", lines[i]):
                item_text = re.sub(r"^\d+\. ", "", lines[i])
                list_items.append({
                    "type": "listItem",
                    "content": [{
                        "type": "paragraph",
                        "content": parse_inline(item_text)
                    }]
                })
                i += 1
            content.append({
                "type": "orderedList",
                "content": list_items
            })
            continue
        # Code blocks
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
        # Regular paragraph
        elif line.strip():
            content.append({
                "type": "paragraph",
                "content": parse_inline(line)
            })

        i += 1

    return {
        "version": 1,
        "type": "doc",
        "content": content if content else [
            {"type": "paragraph", "content": [{"type": "text", "text": text}]}
        ]
    }


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


def create_issue(summary: str, description: str | None = None,
                 issue_type: str = "Story", labels: list[str] | None = None,
                 points: int | None = None, component: str | None = None,
                 epic: str | None = None) -> dict:
    """Create a Jira issue."""
    base_url = os.environ.get("JIRA_BASE_URL")
    if not base_url:
        print("Error: JIRA_BASE_URL environment variable required.", file=sys.stderr)
        sys.exit(1)

    url = f"{base_url.rstrip('/')}/rest/api/3/issue"

    fields = {
        "project": {"key": os.environ.get("JIRA_PROJECT", "YOUR_PROJECT")},
        "summary": summary,
        "issuetype": {"name": issue_type},
    }

    if description:
        fields["description"] = markdown_to_adf(description)

    if labels:
        fields["labels"] = labels

    if points is not None:
        fields["customfield_10016"] = points

    if component:
        fields["components"] = [{"name": component}]

    if epic:
        fields["parent"] = {"key": epic}

    data = json.dumps({"fields": fields}).encode('utf-8')

    req = Request(url, data=data, method='POST')
    req.add_header("Authorization", get_auth_header())
    req.add_header("Accept", "application/json")
    req.add_header("Content-Type", "application/json")

    try:
        with urlopen(req) as response:
            return json.loads(response.read().decode())
    except HTTPError as e:
        error_body = e.read().decode() if e.fp else ""
        if e.code == 400:
            print(f"Error: Bad request - {error_body}", file=sys.stderr)
        elif e.code == 401:
            print("Error: Authentication failed. Check JIRA_TOKEN.", file=sys.stderr)
        elif e.code == 403:
            print("Error: Permission denied.", file=sys.stderr)
        else:
            print(f"Error: HTTP {e.code} - {e.reason}\n{error_body}", file=sys.stderr)
        sys.exit(1)
    except URLError as e:
        print(f"Error: Could not connect to Jira - {e.reason}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Create a new Jira issue",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("summary", help="Issue title/summary")
    parser.add_argument("--description", "-d", help="Issue description in Markdown")
    parser.add_argument("--type", "-t", default="Story",
                        help="Issue type (default: Story). Options: Story, Task, Bug, Sub-task")
    parser.add_argument("--labels", "-l", nargs="+", help="Labels to add")
    parser.add_argument("--points", "-p", type=int, help="Story points (1,2,3,5,8,13)")
    parser.add_argument("--component", "-c", help="Component name (e.g., Debt4, Cash4)")
    parser.add_argument("--epic", "-e", help="Epic key to link to (e.g., PROJ-2500)")

    args = parser.parse_args()

    result = create_issue(
        summary=args.summary,
        description=args.description,
        issue_type=args.type,
        labels=args.labels,
        points=args.points,
        component=args.component,
        epic=args.epic,
    )

    key = result.get("key", "unknown")
    issue_id = result.get("id", "unknown")
    base_url = os.environ.get("JIRA_BASE_URL", "")
    browse_url = f"{base_url.rstrip('/')}/browse/{key}"

    print(f"Created {key}")
    print(f"URL: {browse_url}")
    print(f"ID: {issue_id}")


if __name__ == "__main__":
    main()
