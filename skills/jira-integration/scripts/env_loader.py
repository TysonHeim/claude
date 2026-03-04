#!/usr/bin/env python3
"""Load environment variables from .env file without external dependencies."""

import os
from pathlib import Path


def find_env_file() -> Path | None:
    """Find .env file by walking up from script location to project root."""
    # Start from the scripts directory
    current = Path(__file__).resolve().parent

    # Walk up to find .env (up to 10 levels)
    for _ in range(10):
        env_path = current / ".env"
        if env_path.exists():
            return env_path

        # Also check if we're in a project root
        if (current / ".git").exists():
            env_path = current / ".env"
            if env_path.exists():
                return env_path

        parent = current.parent
        if parent == current:  # Reached filesystem root
            break
        current = parent

    return None


def parse_env_file(env_path: Path) -> dict[str, str]:
    """Parse .env file and return key-value pairs."""
    env_vars = {}

    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue

            # Parse KEY=VALUE
            if "=" in line:
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip()

                # Remove surrounding quotes if present
                if (value.startswith('"') and value.endswith('"')) or \
                   (value.startswith("'") and value.endswith("'")):
                    value = value[1:-1]

                env_vars[key] = value

    return env_vars


def load_env():
    """Load .env file into os.environ if variables aren't already set."""
    env_path = find_env_file()

    if not env_path:
        return  # No .env found, rely on environment variables

    env_vars = parse_env_file(env_path)

    # Map common variations to expected names
    key_mappings = {
        "JIRA_URL": "JIRA_BASE_URL",
        "JIRA_API_TOKEN": "JIRA_TOKEN",
    }

    for key, value in env_vars.items():
        # Don't overwrite existing environment variables
        if key not in os.environ:
            os.environ[key] = value

        # Also set mapped keys if the target isn't set
        if key in key_mappings:
            mapped_key = key_mappings[key]
            if mapped_key not in os.environ:
                os.environ[mapped_key] = value


# Auto-load on import
load_env()
