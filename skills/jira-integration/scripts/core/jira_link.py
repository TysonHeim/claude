#!/usr/bin/env python3
"""Create issue links in Jira."""

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
from urllib.error import HTTPError
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


def create_link(blocker_issue: str, blocked_issue: str, link_type: str = "Blocks"):
    """
    Create an issue link in Jira.

    For "Blocks" link type: blocker_issue blocks blocked_issue
    - blocker_issue will show "blocks blocked_issue"
    - blocked_issue will show "is blocked by blocker_issue"

    Args:
        blocker_issue: The issue that blocks (must be done first)
        blocked_issue: The issue that is blocked (cannot start until blocker is done)
        link_type: The link type name (default: "Blocks")

    Note: Jira API uses counter-intuitive naming:
        - inwardIssue = the blocker (shows "blocks X")
        - outwardIssue = the blocked (shows "is blocked by X")
    """
    base_url = os.environ.get("JIRA_BASE_URL")
    if not base_url:
        print("Error: JIRA_BASE_URL environment variable required.", file=sys.stderr)
        sys.exit(1)

    url = f"{base_url.rstrip('/')}/rest/api/3/issueLink"

    # IMPORTANT: Jira's naming is counter-intuitive!
    # inwardIssue = the one that "blocks" (shows "blocks X" on this issue)
    # outwardIssue = the one that "is blocked by" (shows "is blocked by X" on this issue)
    payload = {
        "type": {
            "name": link_type
        },
        "outwardIssue": {
            "key": blocked_issue   # This issue will show "is blocked by blocker_issue"
        },
        "inwardIssue": {
            "key": blocker_issue   # This issue will show "blocks blocked_issue"
        }
    }

    req = Request(url, data=json.dumps(payload).encode('utf-8'), method='POST')
    req.add_header("Authorization", get_auth_header())
    req.add_header("Accept", "application/json")
    req.add_header("Content-Type", "application/json")

    try:
        with urlopen(req) as response:
            print(f"Created link: {blocker_issue} blocks {blocked_issue}")
            return True
    except HTTPError as e:
        error_body = e.read().decode() if e.fp else ""
        if e.code == 404:
            print(f"Error: One of the tickets not found: {blocker_issue}, {blocked_issue}", file=sys.stderr)
        elif e.code == 401:
            print("Error: Authentication failed.", file=sys.stderr)
        else:
            print(f"Error: HTTP {e.code} - {e.reason}: {error_body}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Create issue links in Jira',
        epilog='Example: jira_link.py PROJ-100 --blocks PROJ-101 PROJ-102 PROJ-103'
    )
    parser.add_argument('source', help='The source issue key (the one that blocks)')
    parser.add_argument('--blocks', nargs='+', help='Issues that are blocked by the source')
    parser.add_argument('--blocked-by', nargs='+', dest='blocked_by',
                        help='Issues that block the source')
    parser.add_argument('--link-type', default='Blocks', help='Link type name (default: Blocks)')

    args = parser.parse_args()

    if not args.blocks and not args.blocked_by:
        parser.error("Must specify --blocks or --blocked-by")

    success_count = 0
    fail_count = 0

    if args.blocks:
        for target in args.blocks:
            if create_link(args.source, target, args.link_type):
                success_count += 1
            else:
                fail_count += 1

    if args.blocked_by:
        for target in args.blocked_by:
            if create_link(target, args.source, args.link_type):
                success_count += 1
            else:
                fail_count += 1

    print(f"\nCompleted: {success_count} links created, {fail_count} failed")
    sys.exit(0 if fail_count == 0 else 1)


if __name__ == "__main__":
    main()
