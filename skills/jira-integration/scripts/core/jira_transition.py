#!/usr/bin/env python3
"""Transition Jira ticket to a new status."""

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


def get_available_transitions(issue_key: str) -> list[dict]:
    """Get available transitions for an issue."""
    base_url = os.environ.get("JIRA_BASE_URL")
    if not base_url:
        print("Error: JIRA_BASE_URL environment variable required.", file=sys.stderr)
        sys.exit(1)

    url = f"{base_url.rstrip('/')}/rest/api/3/issue/{issue_key}/transitions"

    req = Request(url)
    req.add_header("Authorization", get_auth_header())
    req.add_header("Accept", "application/json")

    try:
        with urlopen(req) as response:
            data = json.loads(response.read().decode())
            return data.get("transitions", [])
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


def find_transition_id(transitions: list[dict], status_name: str) -> str | None:
    """Find transition ID by status name (case-insensitive partial match)."""
    status_lower = status_name.lower()

    # First try exact match
    for transition in transitions:
        if transition.get("name", "").lower() == status_lower:
            return transition.get("id")
        if transition.get("to", {}).get("name", "").lower() == status_lower:
            return transition.get("id")

    # Then try partial match
    for transition in transitions:
        if status_lower in transition.get("name", "").lower():
            return transition.get("id")
        if status_lower in transition.get("to", {}).get("name", "").lower():
            return transition.get("id")

    return None


def transition_issue(issue_key: str, transition_id: str) -> bool:
    """Transition issue to new status."""
    base_url = os.environ.get("JIRA_BASE_URL")
    if not base_url:
        print("Error: JIRA_BASE_URL environment variable required.", file=sys.stderr)
        sys.exit(1)

    url = f"{base_url.rstrip('/')}/rest/api/3/issue/{issue_key}/transitions"

    body = {
        "transition": {
            "id": transition_id
        }
    }

    data = json.dumps(body).encode('utf-8')

    req = Request(url, data=data, method='POST')
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
    parser = argparse.ArgumentParser(description="Transition Jira ticket to new status")
    parser.add_argument("issue_key", help="Jira issue key (e.g., PROJ-1234)")
    parser.add_argument("status", nargs="?", help='Target status (e.g., "In Progress", "Done"). Omit to list available transitions.')
    parser.add_argument("--list", action="store_true", help="List available transitions")

    args = parser.parse_args()

    # Get available transitions
    transitions = get_available_transitions(args.issue_key)

    # If no status provided or --list flag, show available transitions
    if not args.status or args.list:
        if not transitions:
            print(f"No transitions available for {args.issue_key}")
            sys.exit(0)

        print(f"Available transitions for {args.issue_key}:")
        for t in transitions:
            transition_name = t.get("name", "Unknown")
            to_status = t.get("to", {}).get("name", "Unknown")
            print(f"  - {transition_name} -> {to_status}")
        sys.exit(0)

    # Find matching transition
    transition_id = find_transition_id(transitions, args.status)

    if not transition_id:
        print(f"Error: No transition found matching '{args.status}'", file=sys.stderr)
        print(f"\nAvailable transitions for {args.issue_key}:", file=sys.stderr)
        for t in transitions:
            transition_name = t.get("name", "Unknown")
            to_status = t.get("to", {}).get("name", "Unknown")
            print(f"  - {transition_name} -> {to_status}", file=sys.stderr)
        sys.exit(1)

    # Perform transition
    if transition_issue(args.issue_key, transition_id):
        # Get the target status name
        target_status = next(
            (t.get("to", {}).get("name") for t in transitions if t.get("id") == transition_id),
            args.status
        )
        print(f"Successfully transitioned {args.issue_key} to '{target_status}'")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
