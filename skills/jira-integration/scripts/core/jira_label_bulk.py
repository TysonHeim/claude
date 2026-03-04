#!/usr/bin/env python3
"""Bulk label operations: rename or remove labels across all matching tickets."""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import env_loader  # noqa: F401

from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import base64


def get_auth_header():
    email = os.environ.get("JIRA_EMAIL")
    token = os.environ.get("JIRA_TOKEN")
    if not email or not token:
        print("Error: JIRA_EMAIL and JIRA_TOKEN required.", file=sys.stderr)
        sys.exit(1)
    return "Basic " + base64.b64encode(f"{email}:{token}".encode()).decode()


def jira_request(url, method="GET", body=None):
    req = Request(url, method=method)
    req.add_header("Authorization", get_auth_header())
    req.add_header("Accept", "application/json")
    if body is not None:
        req.add_header("Content-Type", "application/json")
        req.data = json.dumps(body).encode()
    try:
        with urlopen(req) as resp:
            raw = resp.read()
            return json.loads(raw) if raw else {}
    except HTTPError as e:
        body_text = e.read().decode() if e.fp else ""
        print(f"HTTP {e.code}: {body_text[:200]}", file=sys.stderr)
        sys.exit(1)
    except URLError as e:
        print(f"Connection error: {e.reason}", file=sys.stderr)
        sys.exit(1)


def search_all(label):
    """Return all issue keys that have this label (case-insensitive JQL)."""
    base = os.environ.get("JIRA_BASE_URL", "").rstrip("/")
    project = os.environ.get("JIRA_PROJECT", "YOUR_PROJECT")
    jql = f'project = {project} AND labels = "{label}" ORDER BY key ASC'
    keys = []
    next_token = None
    while True:
        payload = {"jql": jql, "fields": ["labels"], "maxResults": 100}
        if next_token:
            payload["nextPageToken"] = next_token
        data = jira_request(f"{base}/rest/api/3/search/jql", method="POST", body=payload)
        issues = data.get("issues", [])
        for issue in issues:
            keys.append((issue["key"], issue["fields"].get("labels", [])))
        next_token = data.get("nextPageToken")
        if not issues or not next_token:
            break
    return keys


def update_labels(issue_key, ops):
    """Apply label ops list like [{'add':'foo'}, {'remove':'bar'}] in one call."""
    base = os.environ.get("JIRA_BASE_URL", "").rstrip("/")
    url = f"{base}/rest/api/3/issue/{issue_key}"
    jira_request(url, method="PUT", body={"update": {"labels": ops}})


def main():
    parser = argparse.ArgumentParser(description="Bulk label rename/remove across project")
    sub = parser.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("rename", help="Rename OLD label to NEW across all matching tickets")
    r.add_argument("old", help="Label to remove")
    r.add_argument("new", help="Label to add")
    r.add_argument("--dry-run", action="store_true")

    d = sub.add_parser("remove", help="Remove a label from all tickets that have it")
    d.add_argument("label", help="Label to remove")
    d.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()

    if args.cmd == "rename":
        tickets = search_all(args.old)
        print(f"Found {len(tickets)} tickets with '{args.old}' (case-insensitive)")
        for key, labels in tickets:
            has_old = any(l == args.old for l in labels)
            has_new = any(l == args.new for l in labels)
            ops = []
            if not has_new:
                ops.append({"add": args.new})
            if has_old:
                ops.append({"remove": args.old})
            if not ops:
                print(f"  {key}: already canonical, skip")
                continue
            if args.dry_run:
                print(f"  {key}: would apply {ops}")
            else:
                update_labels(key, ops)
                print(f"  {key}: {args.old} → {args.new}")

    elif args.cmd == "remove":
        tickets = search_all(args.label)
        print(f"Found {len(tickets)} tickets with '{args.label}'")
        for key, labels in tickets:
            has_label = any(l == args.label for l in labels)
            if not has_label:
                print(f"  {key}: label not present (case diff), skip")
                continue
            if args.dry_run:
                print(f"  {key}: would remove '{args.label}'")
            else:
                update_labels(key, [{"remove": args.label}])
                print(f"  {key}: removed '{args.label}'")


if __name__ == "__main__":
    main()
