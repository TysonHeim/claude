---
name: skill-creator
description: Use when creating or updating Claude Code skills. Covers SKILL.md structure, YAML frontmatter requirements, naming conventions (kebab-case), description best practices, and multi-file skill organization.
---

# Skill Creator

This skill provides guidance for creating effective Claude Code skills.

## About Skills

Skills are modular, self-contained packages that extend Claude's capabilities by providing specialized knowledge, workflows, and tools. They transform Claude from a general-purpose agent into a specialized agent equipped with procedural knowledge.

### What Skills Provide

1. Specialized workflows - Multi-step procedures for specific domains
2. Tool integrations - Instructions for working with specific file formats or APIs
3. Domain expertise - Company-specific knowledge, schemas, business logic
4. Bundled resources - Scripts, references, and assets for complex and repetitive tasks

## Core Principles

### Conciseness is Key

The context window is a shared resource. Only add context Claude doesn't already have. Challenge each piece: "Does Claude really need this?" and "Does this paragraph justify its token cost?"

### Set Appropriate Freedom Levels

- **High Freedom** (text instructions): Multiple approaches valid
- **Medium Freedom** (pseudocode): Preferred pattern exists
- **Low Freedom** (specific scripts): Fragile operations; exact sequence required

### Anatomy of a Skill

```
skill-name/
├── SKILL.md (required)
│   ├── YAML frontmatter metadata (required)
│   │   ├── name: (required)
│   │   └── description: (required)
│   └── Markdown instructions (required)
└── Bundled Resources (optional)
    ├── scripts/          - Executable code
    ├── references/       - Documentation for context
    └── assets/           - Files used in output
```

## SKILL.md Requirements

### YAML Frontmatter

**`name`** (Required)
- Max 64 characters, lowercase letters, numbers, and hyphens only
- Should match the directory name
- Prefer gerund form: `processing-pdfs`, `analyzing-data`

**`description`** (Required)
- Max 1024 characters
- Must answer: What does this skill do? When should Claude use it?
- Include trigger terms users would naturally say

Good: `Extract text and tables from PDF files, fill forms, merge documents. Use when working with PDF files or when the user mentions PDFs, forms, or document extraction.`

Bad: `Helps with documents` (too vague)

### Body (Markdown)

Instructions and guidance, loaded only AFTER the skill triggers. Keep under 500 lines.

## Progressive Disclosure

Skills use a three-level loading system:

1. **Metadata (name + description)** - Always in context (~100 tokens)
2. **SKILL.md body** - When skill triggers
3. **Bundled resources** - As needed by Claude

### Patterns

**High-level guide with references:**
```markdown
# PDF Processing
## Quick start
[code example]
## Advanced features
- **Form filling**: See [FORMS.md](FORMS.md)
- **API reference**: See [REFERENCE.md](REFERENCE.md)
```

**Domain-specific organization:**
```
bigquery-skill/
├── SKILL.md (overview and navigation)
└── reference/
    ├── finance.md
    ├── sales.md
    └── marketing.md
```

**Key Rule**: Keep references ONE level deep from SKILL.md.

## What NOT to Include

- README.md, INSTALLATION_GUIDE.md, CHANGELOG.md
- User-facing documentation
- Setup/testing procedures

## Creation Process

1. **Understand** - Gather concrete usage examples
2. **Plan** - Identify reusable resources (scripts, references, assets)
3. **Create** - Make the skill folder with SKILL.md
4. **Test** - Use on real tasks
5. **Iterate** - Improve based on actual usage

## Anti-Patterns

- Windows-style paths (`scripts\helper.py`) - use Unix paths
- Over-explaining what Claude already knows
- Too many options instead of opinionated defaults
- Vague descriptions that won't trigger
- Deeply nested references (A->B->C)
