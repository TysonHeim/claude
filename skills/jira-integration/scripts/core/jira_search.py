#!/usr/bin/env python3
"""Search Jira issues using JQL with AI field support."""

import argparse
import json
import os
import sys
import io

# Fix Windows encoding issues
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Auto-load .env file
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import env_loader  # noqa: F401

from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import base64

# AI custom field IDs
AI_FIELDS = {
    'ai_status': 'customfield_10960',
    'ai_mode': 'customfield_10961',
    'ai_branch': 'customfield_10956',
    'ai_pr_url': 'customfield_10957',
    'ai_plan_approved': 'customfield_10958',
    'ai_last_phase': 'customfield_10959',
    'ai_candidate': 'customfield_10995',
}


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


DEFAULT_FIELDS = ['key', 'summary', 'status', 'assignee', 'labels']


def _search_page(jql: str, fields: list, page_size: int, next_page_token: str = None) -> dict:
    """Fetch a single page of search results."""
    base_url = os.environ.get("JIRA_BASE_URL")
    if not base_url:
        print("Error: JIRA_BASE_URL environment variable required.", file=sys.stderr)
        sys.exit(1)

    url = f"{base_url.rstrip('/')}/rest/api/3/search/jql"

    payload = {
        'jql': jql,
        'fields': fields,
        'maxResults': page_size,
    }
    if next_page_token:
        payload['nextPageToken'] = next_page_token

    req = Request(url, method='POST')
    req.add_header("Authorization", get_auth_header())
    req.add_header("Accept", "application/json")
    req.add_header("Content-Type", "application/json")
    req.data = json.dumps(payload).encode()

    try:
        with urlopen(req) as response:
            return json.loads(response.read().decode())
    except HTTPError as e:
        error_body = e.read().decode() if e.fp else ""
        try:
            error_json = json.loads(error_body)
            error_msgs = error_json.get('errorMessages', [])
            if error_msgs:
                print(f"Error: {error_msgs[0]}", file=sys.stderr)
            else:
                print(f"Error: HTTP {e.code} - {e.reason}", file=sys.stderr)
        except json.JSONDecodeError:
            print(f"Error: HTTP {e.code} - {e.reason}", file=sys.stderr)
        sys.exit(1)
    except URLError as e:
        print(f"Error: Could not connect to Jira - {e.reason}", file=sys.stderr)
        sys.exit(1)


def search_issues(jql: str, max_results: int = 50, fields: list = None,
                  include_ai: bool = True, all_pages: bool = False) -> dict:
    """Search issues using the /rest/api/3/search/jql endpoint (POST).

    Note: Jira deprecated /rest/api/2/search (returns 410 Gone).
    Always use this v3 POST endpoint.
    """
    if fields is None:
        fields = DEFAULT_FIELDS + (list(AI_FIELDS.values()) if include_ai else [])

    if not all_pages:
        return _search_page(jql, fields, page_size=max_results)

    # Paginate through all results using nextPageToken cursor
    all_issues = []
    next_token = None
    page_size = 100  # Jira max per request

    while True:
        page = _search_page(jql, fields, page_size=page_size, next_page_token=next_token)
        issues = page.get('issues', [])
        all_issues.extend(issues)
        next_token = page.get('nextPageToken')
        print(f"  Fetched {len(all_issues)}...", file=sys.stderr)
        if not issues or not next_token:
            break

    return {'total': len(all_issues), 'issues': all_issues}


def get_ai_field_value(fields: dict, field_name: str) -> str:
    """Extract AI field value from issue fields."""
    field_id = AI_FIELDS.get(field_name)
    if not field_id:
        return None

    field_value = fields.get(field_id)
    if field_value is None:
        return None

    # Handle select/option fields
    if isinstance(field_value, dict) and 'value' in field_value:
        return field_value['value']

    # Handle array fields (like checkboxes)
    if isinstance(field_value, list):
        return ', '.join(v.get('value', str(v)) if isinstance(v, dict) else str(v) for v in field_value)

    return str(field_value) if field_value else None


def format_text_output(data: dict) -> str:
    """Format search results as human-readable text."""
    issues = data.get('issues', [])
    # Use actual count since API total can be unreliable
    total = len(issues)

    lines = [f"Found {total} issue(s):", ""]

    for issue in issues:
        key = issue.get('key')
        fields = issue.get('fields', {})
        summary = fields.get('summary', 'No summary')[:50]
        status = fields.get('status', {}).get('name', 'Unknown')
        assignee = fields.get('assignee', {})
        assignee_str = assignee.get('emailAddress', 'Unassigned') if assignee else 'Unassigned'
        labels = fields.get('labels', [])

        ai_status = get_ai_field_value(fields, 'ai_status') or '-'
        ai_branch = get_ai_field_value(fields, 'ai_branch') or '-'

        label_str = f"  [{', '.join(labels)}]" if labels else ''
        lines.append(f"{key}: {ai_status:15s} [{status:20s}] {summary}...{label_str}")
        if ai_branch != '-':
            lines.append(f"       Branch: {ai_branch}")

    return "\n".join(lines)


def format_json_output(data: dict) -> str:
    """Format search results as JSON with AI fields extracted."""
    issues = data.get('issues', [])

    result = {
        'total': len(issues),
        'issues': []
    }

    for issue in issues:
        fields = issue.get('fields', {})
        assignee = fields.get('assignee')

        issue_data = {
            'key': issue.get('key'),
            'summary': fields.get('summary'),
            'status': fields.get('status', {}).get('name'),
            'assignee': assignee.get('emailAddress') if assignee else None,
            'labels': fields.get('labels', []),
            'ai_status': get_ai_field_value(fields, 'ai_status'),
            'ai_mode': get_ai_field_value(fields, 'ai_mode'),
            'ai_branch': get_ai_field_value(fields, 'ai_branch'),
            'ai_pr_url': get_ai_field_value(fields, 'ai_pr_url'),
            'ai_last_phase': get_ai_field_value(fields, 'ai_last_phase'),
        }
        result['issues'].append(issue_data)

    return json.dumps(result, indent=2)


def build_jql(args) -> str:
    """Build JQL query from arguments."""
    if args.jql:
        return args.jql

    project = os.environ.get("JIRA_PROJECT", "YOUR_PROJECT")
    conditions = [f'project = {project}']

    if args.ai_status:
        conditions.append(f'"AI Status" = "{args.ai_status}"')

    if args.ai_assigned:
        ai_email = os.environ.get("JIRA_AI_EMAIL", "ai@example.com")
        conditions.append(f'assignee = "{ai_email}"')

    if args.assignee:
        conditions.append(f'assignee = "{args.assignee}"')

    if args.status:
        conditions.append(f'status = "{args.status}"')

    return ' AND '.join(conditions) + ' ORDER BY key DESC'


def main():
    parser = argparse.ArgumentParser(
        description="Search Jira issues with AI field support",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Search by JQL
  %(prog)s --jql 'project = YOUR_PROJECT AND status = "In Progress"'

  # Find tickets by assignee and status
  %(prog)s --assignee user@example.com --status "Dev Testing"

  # Find all tickets with AI Status = "PR Created"
  %(prog)s --ai-status "PR Created"

  # Find AI-assigned tickets
  %(prog)s --ai-assigned

  # Combine filters
  %(prog)s --ai-assigned --ai-status "Implementing"

  # Output as JSON
  %(prog)s --ai-status "PR Created" --format json

  # Skip AI fields for faster queries
  %(prog)s --status "In Progress" --no-ai-fields
"""
    )

    parser.add_argument("--jql", help="Raw JQL query (overrides other filters)")
    parser.add_argument("--ai-status", dest="ai_status",
                        choices=["Planning", "Awaiting Approval", "Approved",
                                "Implementing", "Verifying", "Reviewing",
                                "PR Created", "Done", "Blocked"],
                        help="Filter by AI Status")
    parser.add_argument("--ai-assigned", dest="ai_assigned", action="store_true",
                        help="Filter to AI-assigned tickets only")
    parser.add_argument("--assignee", help="Filter by assignee email (e.g., user@example.com)")
    parser.add_argument("--status", help="Filter by Jira status")
    parser.add_argument("--fields", nargs='+',
                        help="Additional Jira fields to fetch (e.g., priority labels sprint)")
    parser.add_argument("--no-ai-fields", dest="no_ai_fields", action="store_true",
                        help="Exclude AI custom fields from query (faster)")
    parser.add_argument("--max", type=int, default=50, dest="max_results",
                        help="Maximum results (default: 50)")
    parser.add_argument("--all-pages", dest="all_pages", action="store_true",
                        help="Fetch all results via pagination (ignores --max)")
    parser.add_argument("--format", choices=["text", "json"], default="text",
                        help="Output format (default: text)")

    args = parser.parse_args()

    jql = build_jql(args)

    if args.format == "text":
        print(f"Query: {jql}", file=sys.stderr)
        print("", file=sys.stderr)

    # Build custom field list if --fields provided
    custom_fields = None
    if args.fields:
        custom_fields = DEFAULT_FIELDS + args.fields
        if not args.no_ai_fields:
            custom_fields += list(AI_FIELDS.values())

    data = search_issues(
        jql,
        max_results=args.max_results,
        fields=custom_fields,
        include_ai=not args.no_ai_fields,
        all_pages=args.all_pages,
    )

    if args.format == "json":
        print(format_json_output(data))
    else:
        print(format_text_output(data))


if __name__ == "__main__":
    main()
