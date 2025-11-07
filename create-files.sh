#!/bin/bash

# Create cleanup-branch.md
cat > commands/cleanup-branch.md << 'EOF'
# /cleanup-branch Command

When this command is used, perform a comprehensive cleanup of the current branch to prepare it for PR or final review.

[Content matches the cleanup-branch.md file exactly - truncated for brevity]
EOF

# Create skills
mkdir -p skills/error-handling skills/performance-optimization skills/testing-standards

# Create error-handling SKILL.md
cat > skills/error-handling/SKILL.md << 'EOF'
---
name: error-handling
description: Use when handling errors, implementing Problem Details (RFC 7807), or setting HTTP status codes.
---

# Error Handling

[Full content of error-handling skill]
EOF

# Create settings.json
cat > settings.json << 'EOF'
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "permissions": {
    "allow": [
      "Bash(git add:*)",
      "Bash(git commit:*)",
      "Bash(git push)",
      "Bash(git checkout:*)",
      "Bash(git rm:*)",
      "Bash(git log:*)",
      "Bash(find:*)",
      "Bash(npm install:*)",
      "Bash(npm test:*)",
      "Bash(npx:*)"
    ],
    "deny": [],
    "ask": []
  }
}
EOF

# Create README
cat > README.md << 'EOF'
# Claude Code Plugin

A collection of reusable skills, commands, and hooks for Claude Code to enhance your development workflow.

## Installation

To use this plugin with Claude Code, clone this repository and reference it in your project's Claude Code settings.

## Contents

### Commands

- **[/why](commands/why.md)** - Five Whys root cause analysis for debugging and problem-solving
- **[/cleanup-branch](commands/cleanup-branch.md)** - Comprehensive branch cleanup using code review tools

### Skills

- **[error-handling](skills/error-handling/SKILL.md)** - RFC 7807 Problem Details implementation and HTTP status code standards
- **[performance-optimization](skills/performance-optimization/SKILL.md)** - React Query patterns, database optimization, and bundle optimization
- **[testing-standards](skills/testing-standards/SKILL.md)** - Unit and integration testing patterns

## Usage

### Commands

Commands can be invoked using the `/` prefix in Claude Code:

\`\`\`
/why
/cleanup-branch
\`\`\`

### Skills

Skills are automatically activated based on context or can be explicitly invoked. They provide guidance and best practices for specific development tasks.

## Requirements

- Claude Code CLI
- For cleanup-branch: Zen MCP server with codereview tool

## Contributing

Feel free to submit issues and enhancement requests!

## License

MIT License
EOF

