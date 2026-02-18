# Claude Code Toolkit

A battle-tested collection of agents, skills, commands, hooks, and scripts for [Claude Code](https://docs.claude.com/en/docs/claude-code). Built from real-world daily use, stripped of project-specific details for general use.

## What's Included

### Agents (`agents/`)

Custom agent definitions that extend Claude Code's Task tool with specialized behaviors.

| Agent | Purpose |
|-------|---------|
| **[code-explorer](agents/code-explorer.md)** | Deep codebase analysis — traces execution paths, maps architecture layers, documents dependencies |
| **[code-reviewer](agents/code-reviewer.md)** | Confidence-scored code review (only reports issues >= 80/100 confidence) |
| **[playwright-manager](agents/playwright-manager.md)** | Playwright MCP instance pool with file-based locking for multi-terminal use |
| **[skills-manager](agents/skills-manager.md)** | Creates, edits, and organizes skills and profiles |

### Commands (`commands/`)

Slash commands invokable with `/command-name` in Claude Code.

| Command | Purpose |
|---------|---------|
| **[/critique](commands/critique.md)** | Senior engineer code review using 5-Whys to drill to root causes |
| **[/design](commands/design.md)** | Adversarial design gate — forces YOU to propose architecture before Claude implements |
| **[/tdd](commands/tdd.md)** | TDD enforcer — makes YOU write tests first, critiques them harshly |
| **[/why](commands/why.md)** | Five Whys root cause analysis for any problem |
| **[/workflow](commands/workflow.md)** | Enforces plan-first, research-existing-patterns, simplify workflow |
| **[/report](commands/report.md)** | Developer growth report card tracking design and TDD progress |
| **[/reflect](commands/reflect.md)** | Session retrospective — proposes skill improvements based on learnings |
| **[/cleanup-branch](commands/cleanup-branch.md)** | Comprehensive branch cleanup for PR preparation |

### Skills (`skills/`)

Contextual knowledge packages that activate when relevant.

| Skill | Purpose |
|-------|---------|
| **[design-gate](skills/design-gate/)** | Adversarial architectural critic — attacks your design until it's solid |
| **[tdd-enforcer](skills/tdd-enforcer/)** | Forces TDD by making you write tests, then critiquing them |
| **[quality-gates](skills/quality-gates/)** | Build/test/lint/typecheck validation with fix-attempt limits |
| **[session-review](skills/session-review/)** | Reviews session for mistakes and logs corrections to CLAUDE.md |
| **[skill-creator](skills/skill-creator/)** | Guide for writing effective Claude Code skills |

### Plugins (`plugins/`)

| Plugin | Purpose |
|--------|---------|
| **[learning-output-style](plugins/learning-output-style/)** | Interactive learning mode — requests meaningful code contributions at decision points and provides educational insights |

### Hooks (`hooks/`)

Shell scripts triggered by Claude Code events.

| Hook | Purpose |
|------|---------|
| **[track-usage.sh](hooks/track-usage.sh)** | Tracks agent and skill invocations per session (PostToolUse hook) |
| **[format-usage.sh](hooks/format-usage.sh)** | Formats usage stats for the status line (e.g., `A:3(exp,cr) S:2`) |

### Scripts (`scripts/`)

Standalone utilities.

| Script | Purpose |
|--------|---------|
| **[activate-profile.js](scripts/activate-profile.js)** | Manages skill profiles via symlinks — activate subsets of skills by context |
| **[playwright-lock/](scripts/playwright-lock/)** | File-based locking for Playwright MCP instances across terminals |

## Installation

### Quick Start

1. Clone this repo:
   ```bash
   git clone https://github.com/TysonHeim/claude.git ~/claude-toolkit
   ```

2. Copy what you want into `~/.claude/`:
   ```bash
   # Agents
   cp ~/claude-toolkit/agents/*.md ~/.claude/agents/

   # Commands
   cp ~/claude-toolkit/commands/*.md ~/.claude/commands/

   # Hooks (make executable)
   cp ~/claude-toolkit/hooks/*.sh ~/.claude/hooks/
   chmod +x ~/.claude/hooks/*.sh

   # Skills
   cp -r ~/claude-toolkit/skills/* ~/.claude/skills/

   # Scripts
   cp ~/claude-toolkit/scripts/activate-profile.js ~/.claude/
   cp -r ~/claude-toolkit/scripts/playwright-lock ~/.claude/scripts/
   chmod +x ~/.claude/scripts/playwright-lock/*.sh
   ```

3. Configure hooks in `~/.claude/settings.json` (see [examples/settings.json](examples/settings.json))

### Skill Profile System

The profile system lets you activate different subsets of skills depending on what you're working on:

```bash
# Create profile directories
mkdir -p ~/.claude/skill-profiles/core
mkdir -p ~/.claude/skill-profiles/quality
mkdir -p ~/.claude/skills-repo

# Move skills to the repo (source of truth)
mv ~/.claude/skills/* ~/.claude/skills-repo/

# Create profile symlinks
cd ~/.claude/skill-profiles/core
ln -s ../../skills-repo/session-review .
ln -s ../../skills-repo/skill-creator .

cd ~/.claude/skill-profiles/quality
ln -s ../../skills-repo/design-gate .
ln -s ../../skills-repo/tdd-enforcer .
ln -s ../../skills-repo/quality-gates .

# Activate profiles
node ~/.claude/activate-profile.js core quality
```

### Plugin Installation

Install the learning output style plugin:

```bash
# Copy to your plugins directory
cp -r ~/claude-toolkit/plugins/learning-output-style ~/.claude/plugins/

# Enable in settings.json
# Add: "enabledPlugins": { "learning-output-style": true }
```

## Philosophy

These tools are built around a few core ideas:

1. **Learning through adversarial feedback** — `/design` and `/tdd` force you to propose solutions before Claude implements them. Claude attacks your design, not to be mean, but to make it solid.

2. **Confidence-based filtering** — The code reviewer only reports issues it's >= 80% confident about. No noise, no false positives.

3. **Self-improving system** — `/reflect` and `session-review` create a feedback loop where skills get better over time based on actual usage.

4. **Context efficiency** — The profile system means you only load skills relevant to your current work, keeping the context window lean.

5. **Multi-terminal safety** — The Playwright lock system and per-session usage tracking support running multiple Claude Code instances simultaneously.

## Customization

Most files work as-is, but you'll want to customize:

- **`quality-gates/SKILL.md`** — Replace placeholder build/test commands with your project's actual commands
- **`hooks/format-usage.sh`** — Add abbreviation mappings for your custom agents/skills
- **`examples/settings.json`** — Adapt the status line command and permissions for your workflow
- **Agent tools lists** — Update `allowed-tools` in agent frontmatter to match your MCP server names

## Requirements

- [Claude Code](https://docs.claude.com/en/docs/claude-code) CLI
- `jq` (for hooks and status line)
- Node.js (for activate-profile.js)
- Playwright MCP server (for playwright-manager agent)

## License

MIT
