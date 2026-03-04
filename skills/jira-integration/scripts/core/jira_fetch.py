#!/usr/bin/env python3
"""Fetch Jira story details."""

import argparse
import json
import os
import sys
import io

# Fix Windows encoding issues
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Auto-load .env file
# Add parent dir to path for env_loader
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import env_loader  # noqa: F401

from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import base64


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


def fetch_issue(issue_key: str) -> dict:
    """Fetch issue from Jira API."""
    base_url = os.environ.get("JIRA_BASE_URL")
    if not base_url:
        print("Error: JIRA_BASE_URL environment variable required.", file=sys.stderr)
        sys.exit(1)

    url = f"{base_url.rstrip('/')}/rest/api/3/issue/{issue_key}?expand=renderedFields"

    req = Request(url)
    req.add_header("Authorization", get_auth_header())
    req.add_header("Accept", "application/json")

    try:
        with urlopen(req) as response:
            return json.loads(response.read().decode())
    except HTTPError as e:
        if e.code == 404:
            print(f"Error: Ticket {issue_key} not found.", file=sys.stderr)
        elif e.code == 401:
            print("Error: Authentication failed. Check JIRA_TOKEN environment variable.", file=sys.stderr)
        else:
            print(f"Error: HTTP {e.code} - {e.reason}", file=sys.stderr)
        sys.exit(1)
    except URLError as e:
        print(f"Error: Could not connect to Jira - {e.reason}", file=sys.stderr)
        sys.exit(1)


def fetch_comments(issue_key: str) -> list:
    """Fetch comments for an issue."""
    base_url = os.environ.get("JIRA_BASE_URL")
    url = f"{base_url.rstrip('/')}/rest/api/3/issue/{issue_key}/comment"

    req = Request(url)
    req.add_header("Authorization", get_auth_header())
    req.add_header("Accept", "application/json")

    try:
        with urlopen(req) as response:
            data = json.loads(response.read().decode())
            return data.get("comments", [])
    except (HTTPError, URLError):
        return []


def extract_text_from_adf(content: dict) -> str:
    """Extract plain text from Atlassian Document Format."""
    if not content:
        return ""

    text_parts = []

    def traverse(node):
        if isinstance(node, dict):
            if node.get("type") == "text":
                text_parts.append(node.get("text", ""))
            elif node.get("type") == "hardBreak":
                text_parts.append("\n")
            for child in node.get("content", []):
                traverse(child)
        elif isinstance(node, list):
            for item in node:
                traverse(item)

    traverse(content)
    return "".join(text_parts)


def format_text_output(issue: dict, comments: list, remote_links: list = None) -> str:
    """Format issue as human-readable text."""
    fields = issue.get("fields", {})

    # Basic fields
    title = fields.get("summary", "No title")
    status = fields.get("status", {}).get("name", "Unknown")
    story_points = fields.get("customfield_10016") or "Not set"

    # Sprint
    sprint_field = fields.get("customfield_10020") or []
    sprint = "None"
    if sprint_field and isinstance(sprint_field, list) and len(sprint_field) > 0:
        sprint = sprint_field[-1].get("name", "Unknown")

    # Assignee
    assignee = fields.get("assignee")
    assignee_str = assignee.get("displayName", "Unassigned") if assignee else "Unassigned"

    # Reporter
    reporter = fields.get("reporter")
    reporter_str = reporter.get("displayName", "Unknown") if reporter else "Unknown"

    # Description
    description_adf = fields.get("description")
    description = extract_text_from_adf(description_adf) if description_adf else "No description"

    # Acceptance Criteria (custom field - adjust field ID as needed)
    ac_field = fields.get("customfield_10035") or fields.get("customfield_10034")
    acceptance_criteria = extract_text_from_adf(ac_field) if ac_field else "Not specified"

    # Issue links
    issue_links = fields.get("issuelinks", [])
    links_str = ""
    if issue_links:
        link_lines = []
        for link in issue_links:
            link_type = link.get("type", {}).get("name", "")
            if "inwardIssue" in link:
                linked_key = link["inwardIssue"].get("key", "")
                linked_summary = link["inwardIssue"].get("fields", {}).get("summary", "")
                link_lines.append(f"  [{link_type} - inward] {linked_key}: {linked_summary}")
            if "outwardIssue" in link:
                linked_key = link["outwardIssue"].get("key", "")
                linked_summary = link["outwardIssue"].get("fields", {}).get("summary", "")
                link_lines.append(f"  [{link_type} - outward] {linked_key}: {linked_summary}")
        links_str = "\n".join(link_lines)

    # Remote links (PR/web links from dev panel)
    remote_links_str = ""
    if remote_links:
        rl_lines = []
        for rl in remote_links:
            obj = rl.get("object", {})
            title = obj.get("title", "")
            url = obj.get("url", "")
            relationship = rl.get("relationship", "")
            rl_lines.append(f"  [{relationship}] {title}: {url}")
        remote_links_str = "\n".join(rl_lines)

    output = f"""Title: {title}
Status: {status}
Story Points: {story_points}
Sprint: {sprint}
Assignee: {assignee_str}
Reporter: {reporter_str}

Issue Links:
{links_str if links_str else "  None"}

Remote Links (PRs/Web):
{remote_links_str if remote_links_str else "  None"}

Description:
{description}

Acceptance Criteria:
{acceptance_criteria}
"""

    if comments:
        output += f"\nComments ({len(comments)}):\n"
        for comment in comments[-5:]:  # Last 5 comments
            author = comment.get("author", {}).get("displayName", "Unknown")
            created = comment.get("created", "")[:10]
            body = extract_text_from_adf(comment.get("body", {}))
            output += f"---\n[{created}] {author}:\n{body}\n"

    return output


def fetch_remote_links(issue_key: str) -> list:
    """Fetch remote links (PR/dev panel links) for an issue."""
    base_url = os.environ.get("JIRA_BASE_URL")
    url = f"{base_url.rstrip('/')}/rest/api/3/issue/{issue_key}/remotelink"

    req = Request(url)
    req.add_header("Authorization", get_auth_header())
    req.add_header("Accept", "application/json")

    try:
        with urlopen(req) as response:
            data = json.loads(response.read().decode())
            return data if isinstance(data, list) else []
    except (HTTPError, URLError):
        return []


def format_json_output(issue: dict, comments: list, remote_links: list = None) -> str:
    """Format issue as JSON."""
    fields = issue.get("fields", {})

    sprint_field = fields.get("customfield_10020") or []
    sprint = None
    if sprint_field and isinstance(sprint_field, list) and len(sprint_field) > 0:
        sprint = sprint_field[-1].get("name")

    description_adf = fields.get("description")
    ac_field = fields.get("customfield_10035") or fields.get("customfield_10034")

    reporter = fields.get("reporter")
    issue_links = fields.get("issuelinks", [])
    formatted_links = []
    for link in issue_links:
        link_type = link.get("type", {}).get("name", "")
        if "inwardIssue" in link:
            formatted_links.append({
                "type": link_type,
                "direction": "inward",
                "key": link["inwardIssue"].get("key"),
                "summary": link["inwardIssue"].get("fields", {}).get("summary")
            })
        if "outwardIssue" in link:
            formatted_links.append({
                "type": link_type,
                "direction": "outward",
                "key": link["outwardIssue"].get("key"),
                "summary": link["outwardIssue"].get("fields", {}).get("summary")
            })

    formatted_remote_links = []
    for rl in (remote_links or []):
        obj = rl.get("object", {})
        formatted_remote_links.append({
            "title": obj.get("title"),
            "url": obj.get("url"),
            "relationship": rl.get("relationship")
        })

    result = {
        "key": issue.get("key"),
        "title": fields.get("summary"),
        "status": fields.get("status", {}).get("name"),
        "storyPoints": fields.get("customfield_10016"),
        "sprint": sprint,
        "assignee": fields.get("assignee", {}).get("displayName") if fields.get("assignee") else None,
        "reporter": reporter.get("displayName") if reporter else None,
        "description": extract_text_from_adf(description_adf) if description_adf else None,
        "acceptanceCriteria": extract_text_from_adf(ac_field) if ac_field else None,
        "issueLinks": formatted_links,
        "remoteLinks": formatted_remote_links,
        "comments": [
            {
                "author": c.get("author", {}).get("displayName"),
                "created": c.get("created"),
                "body": extract_text_from_adf(c.get("body", {}))
            }
            for c in comments
        ]
    }

    return json.dumps(result, indent=2)


def main():
    parser = argparse.ArgumentParser(description="Fetch Jira story details")
    parser.add_argument("issue_key", help="Jira issue key (e.g., PROJ-1234)")
    parser.add_argument("--format", choices=["text", "json"], default="text",
                        help="Output format (default: text)")

    args = parser.parse_args()

    issue = fetch_issue(args.issue_key)
    comments = fetch_comments(args.issue_key)
    remote_links = fetch_remote_links(args.issue_key)

    if args.format == "json":
        print(format_json_output(issue, comments, remote_links))
    else:
        print(format_text_output(issue, comments, remote_links))


if __name__ == "__main__":
    main()
