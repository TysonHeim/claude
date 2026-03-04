#!/usr/bin/env python3
"""Post comment to Jira issue.

IMPORTANT: Use MARKDOWN formatting, NOT Jira wiki markup!

Supported markdown:
  # H1, ## H2, ### H3     - Headings
  **bold**                 - Bold text (double asterisks)
  - item  or  * item       - Bullet lists
  1. item                  - Numbered lists
  `code`                   - Inline code
  ```code blocks```        - Code blocks
  [~accountid:xxx]         - User mentions (passed through)

NOT supported:
  h3. heading              - Jira wiki headings
  ||table||cells||         - Jira wiki tables
  *single asterisk*        - Won't render as bold/italic
  _underscores_            - Won't render as italic
  {code}...{code}          - Jira wiki code blocks
"""

import argparse
import json
import os
import sys

# Auto-load .env file
# Add parent dir to path for env_loader
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

        # Tables (detect by | at start and end, with separator row)
        if line.strip().startswith("|") and line.strip().endswith("|"):
            table_rows = []
            # Collect all table rows
            while i < len(lines) and lines[i].strip().startswith("|") and lines[i].strip().endswith("|"):
                row_text = lines[i].strip()
                # Skip separator rows (|---|---| or |:---|:---:|)
                if re.match(r'^\|[\s\-:\|]+\|$', row_text):
                    i += 1
                    continue
                # Parse cells
                cells = [c.strip() for c in row_text.split("|")[1:-1]]
                table_rows.append(cells)
                i += 1

            if table_rows:
                # Build ADF table
                adf_rows = []
                for row_idx, row in enumerate(table_rows):
                    adf_cells = []
                    for cell in row:
                        cell_type = "tableHeader" if row_idx == 0 else "tableCell"
                        adf_cells.append({
                            "type": cell_type,
                            "content": [{
                                "type": "paragraph",
                                "content": parse_inline(cell)
                            }]
                        })
                    adf_rows.append({
                        "type": "tableRow",
                        "content": adf_cells
                    })
                content.append({
                    "type": "table",
                    "attrs": {"isNumberColumnEnabled": False, "layout": "default"},
                    "content": adf_rows
                })
            continue

        # Headers
        if line.startswith("## "):
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
        elif line.startswith("### "):
            content.append({
                "type": "heading",
                "attrs": {"level": 3},
                "content": [{"type": "text", "text": line[4:]}]
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
        # Empty line or regular paragraph
        elif line.strip():
            content.append({
                "type": "paragraph",
                "content": parse_inline(line)
            })

        i += 1

    return {
        "version": 1,
        "type": "doc",
        "content": content if content else [{"type": "paragraph", "content": [{"type": "text", "text": text}]}]
    }


def parse_inline(text: str) -> list:
    """Parse inline markdown formatting."""
    result = []

    # Simple approach: just return as text for now
    # Could be enhanced to handle **bold**, *italic*, `code`, etc.
    if text:
        # Handle inline code
        parts = re.split(r'(`[^`]+`)', text)
        for part in parts:
            if part.startswith('`') and part.endswith('`'):
                result.append({
                    "type": "text",
                    "text": part[1:-1],
                    "marks": [{"type": "code"}]
                })
            elif part:
                # Handle bold
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


def post_comment(issue_key: str, comment_text: str) -> dict:
    """Post comment to Jira issue."""
    base_url = os.environ.get("JIRA_BASE_URL")
    if not base_url:
        print("Error: JIRA_BASE_URL environment variable required.", file=sys.stderr)
        sys.exit(1)

    url = f"{base_url.rstrip('/')}/rest/api/3/issue/{issue_key}/comment"

    body = {
        "body": markdown_to_adf(comment_text)
    }

    data = json.dumps(body).encode('utf-8')

    req = Request(url, data=data, method='POST')
    req.add_header("Authorization", get_auth_header())
    req.add_header("Accept", "application/json")
    req.add_header("Content-Type", "application/json")

    try:
        with urlopen(req) as response:
            return json.loads(response.read().decode())
    except HTTPError as e:
        if e.code == 404:
            print(f"Error: Ticket {issue_key} not found.", file=sys.stderr)
        elif e.code == 401:
            print("Error: Authentication failed. Check JIRA_TOKEN environment variable.", file=sys.stderr)
        elif e.code == 400:
            error_body = e.read().decode() if e.fp else ""
            print(f"Error: Bad request - {error_body}", file=sys.stderr)
        else:
            print(f"Error: HTTP {e.code} - {e.reason}", file=sys.stderr)
        sys.exit(1)
    except URLError as e:
        print(f"Error: Could not connect to Jira - {e.reason}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Post comment to Jira issue",
        epilog="""
FORMATTING: Use MARKDOWN, not Jira wiki markup!
  Supported: # headers, **bold**, - bullets, 1. numbered, `code`, ```blocks```
  NOT supported: h3. headings, ||tables||, *single asterisk*, _italic_
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("issue_key", help="Jira issue key (e.g., PROJ-1234)")
    parser.add_argument("comment", help="Comment text in MARKDOWN format")

    args = parser.parse_args()

    result = post_comment(args.issue_key, args.comment)

    comment_id = result.get("id", "unknown")
    print(f"Comment posted successfully to {args.issue_key}")
    print(f"Comment ID: {comment_id}")


if __name__ == "__main__":
    main()
