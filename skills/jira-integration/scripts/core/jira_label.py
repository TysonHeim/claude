#!/usr/bin/env python3
"""Add or remove labels from Jira issues."""

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


def add_labels(issue_key: str, labels: list[str]) -> bool:
    """Add labels to a Jira issue."""
    base_url = os.environ.get("JIRA_BASE_URL")
    if not base_url:
        print("Error: JIRA_BASE_URL environment variable required.", file=sys.stderr)
        sys.exit(1)

    url = f"{base_url.rstrip('/')}/rest/api/3/issue/{issue_key}"

    body = {
        "update": {
            "labels": [{"add": label} for label in labels]
        }
    }

    data = json.dumps(body).encode('utf-8')

    req = Request(url, data=data, method='PUT')
    req.add_header("Authorization", get_auth_header())
    req.add_header("Accept", "application/json")
    req.add_header("Content-Type", "application/json")

    try:
        with urlopen(req) as response:
            # Successful PUT returns 204 No Content
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
        sys.exit(1)
    except URLError as e:
        print(f"Error: Could not connect to Jira - {e.reason}", file=sys.stderr)
        sys.exit(1)


def rename_label(issue_key: str, old_label: str, new_label: str) -> bool:
    """Atomically add new_label and remove old_label in one API call."""
    base_url = os.environ.get("JIRA_BASE_URL")
    if not base_url:
        print("Error: JIRA_BASE_URL environment variable required.", file=sys.stderr)
        sys.exit(1)

    url = f"{base_url.rstrip('/')}/rest/api/3/issue/{issue_key}"

    body = {
        "update": {
            "labels": [{"add": new_label}, {"remove": old_label}]
        }
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
        sys.exit(1)
    except URLError as e:
        print(f"Error: Could not connect to Jira - {e.reason}", file=sys.stderr)
        sys.exit(1)


def remove_labels(issue_key: str, labels: list[str]) -> bool:
    """Remove labels from a Jira issue."""
    base_url = os.environ.get("JIRA_BASE_URL")
    if not base_url:
        print("Error: JIRA_BASE_URL environment variable required.", file=sys.stderr)
        sys.exit(1)

    url = f"{base_url.rstrip('/')}/rest/api/3/issue/{issue_key}"

    body = {
        "update": {
            "labels": [{"remove": label} for label in labels]
        }
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
        sys.exit(1)
    except URLError as e:
        print(f"Error: Could not connect to Jira - {e.reason}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Add or remove labels from Jira issue")
    parser.add_argument("issue_key", help="Jira issue key (e.g., PROJ-1234)")
    parser.add_argument("labels", nargs="*", help="Label(s) to add or remove")
    parser.add_argument("--remove", "-r", action="store_true",
                        help="Remove labels instead of adding them")
    parser.add_argument("--rename", nargs=2, metavar=("OLD", "NEW"),
                        help="Atomically rename a label (add NEW, remove OLD) in one API call")

    args = parser.parse_args()

    if args.rename:
        old_label, new_label = args.rename
        rename_label(args.issue_key, old_label, new_label)
        print(f"Label renamed on {args.issue_key}: {old_label} → {new_label}")
    elif args.remove:
        remove_labels(args.issue_key, args.labels)
        print(f"Labels removed from {args.issue_key}: {', '.join(args.labels)}")
    else:
        add_labels(args.issue_key, args.labels)
        print(f"Labels added to {args.issue_key}: {', '.join(args.labels)}")


if __name__ == "__main__":
    main()
