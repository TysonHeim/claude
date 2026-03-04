#!/usr/bin/env python3
"""Upload attachments to Jira issues."""

import os
import sys

# Auto-load .env file
# Add parent dir to path for env_loader
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import env_loader  # noqa: F401

import requests
from requests.auth import HTTPBasicAuth

def upload_attachment(issue_key: str, file_path: str) -> bool:
    """Upload a file attachment to a Jira issue."""
    base_url = os.environ.get("JIRA_URL") or os.environ.get("JIRA_BASE_URL")
    email = os.environ.get("JIRA_EMAIL")
    token = os.environ.get("JIRA_API_TOKEN") or os.environ.get("JIRA_TOKEN")

    if not all([base_url, email, token]):
        print("Error: JIRA_URL, JIRA_EMAIL, and JIRA_API_TOKEN environment variables required.")
        return False

    url = f"{base_url}/rest/api/3/issue/{issue_key}/attachments"

    auth = HTTPBasicAuth(email, token)
    headers = {
        "X-Atlassian-Token": "no-check"
    }

    with open(file_path, "rb") as f:
        files = {"file": (os.path.basename(file_path), f)}
        response = requests.post(url, auth=auth, headers=headers, files=files)

    if response.status_code == 200:
        result = response.json()
        if result:
            print(f"Uploaded: {result[0].get('filename', file_path)}")
            return True
    else:
        print(f"Error uploading {file_path}: {response.status_code} - {response.text[:200]}")
        return False

def main():
    if len(sys.argv) < 3:
        print("Usage: python jira_attach.py <ISSUE_KEY> <FILE_PATH> [FILE_PATH2] ...")
        sys.exit(1)

    issue_key = sys.argv[1]
    files = sys.argv[2:]

    success_count = 0
    for file_path in files:
        if os.path.exists(file_path):
            if upload_attachment(issue_key, file_path):
                success_count += 1
        else:
            print(f"File not found: {file_path}")

    print(f"\nUploaded {success_count}/{len(files)} files to {issue_key}")

if __name__ == "__main__":
    main()
