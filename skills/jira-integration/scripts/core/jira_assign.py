#!/usr/bin/env python3
"""Assign Jira ticket to a user."""

import argparse
import json
import os
import sys

# Auto-load .env file
# Add parent dir to path for env_loader
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import env_loader  # noqa: F401

from urllib.parse import quote
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


def get_user_account_id(username: str) -> str | None:
    """Get Jira account ID for a username or email."""
    base_url = os.environ.get("JIRA_BASE_URL")
    if not base_url:
        print("Error: JIRA_BASE_URL environment variable required.", file=sys.stderr)
        sys.exit(1)

    # Special handling for "ai" user
    if username.lower() == "ai":
        # Search for AI service account
        username = os.environ.get("JIRA_AI_EMAIL", "ai@example.com")

    # Search for user by email or display name
    url = f"{base_url.rstrip('/')}/rest/api/3/user/search?query={quote(username)}"

    req = Request(url)
    req.add_header("Authorization", get_auth_header())
    req.add_header("Accept", "application/json")

    try:
        with urlopen(req) as response:
            users = json.loads(response.read().decode())
            if not users:
                return None
            # Return first match
            return users[0].get("accountId")
    except (HTTPError, URLError) as e:
        print(f"Error searching for user: {e}", file=sys.stderr)
        return None


def assign_issue(issue_key: str, assignee_id: str | None) -> bool:
    """Assign issue to user. Pass None to unassign."""
    base_url = os.environ.get("JIRA_BASE_URL")
    if not base_url:
        print("Error: JIRA_BASE_URL environment variable required.", file=sys.stderr)
        sys.exit(1)

    url = f"{base_url.rstrip('/')}/rest/api/3/issue/{issue_key}/assignee"

    # Build request body
    body = {
        "accountId": assignee_id
    }

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
            print("Error: Authentication failed. Check JIRA_TOKEN environment variable.", file=sys.stderr)
        elif e.code == 400:
            error_body = e.read().decode() if e.fp else ""
            print(f"Error: Bad request - {error_body}", file=sys.stderr)
        else:
            print(f"Error: HTTP {e.code} - {e.reason}", file=sys.stderr)
        return False
    except URLError as e:
        print(f"Error: Could not connect to Jira - {e.reason}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(description="Assign Jira ticket to a user")
    parser.add_argument("issue_key", help="Jira issue key (e.g., PROJ-1234)")
    parser.add_argument("username", help='Username, email, or "ai" for AI service account. Use "unassigned" to unassign.')

    args = parser.parse_args()

    # Handle unassignment
    if args.username.lower() == "unassigned":
        if assign_issue(args.issue_key, None):
            print(f"Successfully unassigned {args.issue_key}")
            sys.exit(0)
        else:
            sys.exit(1)

    # Get account ID for username
    account_id = get_user_account_id(args.username)

    if not account_id:
        print(f"Error: Could not find user '{args.username}'", file=sys.stderr)
        print("Try using full email address or display name.", file=sys.stderr)
        sys.exit(1)

    # Assign the issue
    if assign_issue(args.issue_key, account_id):
        print(f"Successfully assigned {args.issue_key} to {args.username}")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
