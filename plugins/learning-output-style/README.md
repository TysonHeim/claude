# Learning Output Style Plugin

Interactive learning mode that requests meaningful code contributions at decision points and provides educational insights.

## What it does

When enabled, this plugin encourages Claude to:

1. **Learning Mode:** Engage you in active learning by requesting meaningful code contributions at decision points
2. **Explanatory Mode:** Provide educational insights about implementation choices and codebase patterns

Instead of implementing everything automatically, Claude will:

1. Identify opportunities where you can write 5-10 lines of meaningful code
2. Focus on business logic and design choices where your input truly matters
3. Prepare the context and location for your contribution
4. Explain trade-offs and guide your implementation
5. Provide educational insights before and after writing code

## Installation

Copy this directory into your Claude Code plugins directory, or reference it as a local plugin.

## When Claude requests contributions

Claude will ask you to write code for:
- Business logic with multiple valid approaches
- Error handling strategies
- Algorithm implementation choices
- Data structure decisions

## When Claude won't request contributions

Claude will implement directly:
- Boilerplate or repetitive code
- Obvious implementations
- Configuration or setup code
- Simple CRUD operations

## Educational insights

Claude will provide educational insights using this format:

```
`★ Insight ─────────────────────────────────────`
[2-3 key educational points about the codebase or implementation]
`─────────────────────────────────────────────────`
```

## Philosophy

Learning by doing is more effective than passive observation. This plugin transforms your interaction with Claude from "watch and learn" to "build and understand."
