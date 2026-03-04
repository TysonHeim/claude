# Story Creation

Create stories via Jira REST API with ADF format.

## REST API Endpoint

```bash
POST https://your-org.atlassian.net/rest/api/3/issue
Authorization: Basic {base64(email:token)}
Content-Type: application/json
```

## Minimal Payload

```json
{
  "fields": {
    "project": { "key": "YOUR_PROJECT" },
    "summary": "Story title here",
    "issuetype": { "name": "Story" },
    "description": {
      "type": "doc",
      "version": 1,
      "content": [
        {
          "type": "paragraph",
          "content": [{ "type": "text", "text": "Description text" }]
        }
      ]
    }
  }
}
```

## Full Story Template

```json
{
  "fields": {
    "project": { "key": "YOUR_PROJECT" },
    "summary": "[Module] Brief description",
    "issuetype": { "name": "Story" },
    "description": {
      "type": "doc",
      "version": 1,
      "content": [
        {
          "type": "heading",
          "attrs": { "level": 2 },
          "content": [{ "type": "text", "text": "User Story" }]
        },
        {
          "type": "paragraph",
          "content": [{ "type": "text", "text": "As a [role], I want [feature] so that [benefit]." }]
        },
        {
          "type": "heading",
          "attrs": { "level": 2 },
          "content": [{ "type": "text", "text": "Acceptance Criteria" }]
        },
        {
          "type": "bulletList",
          "content": [
            {
              "type": "listItem",
              "content": [
                {
                  "type": "paragraph",
                  "content": [{ "type": "text", "text": "Given X, when Y, then Z" }]
                }
              ]
            }
          ]
        },
        {
          "type": "heading",
          "attrs": { "level": 2 },
          "content": [{ "type": "text", "text": "Technical Notes" }]
        },
        {
          "type": "paragraph",
          "content": [{ "type": "text", "text": "Implementation details here." }]
        }
      ]
    },
    "customfield_10016": 3,
    "labels": ["cash4", "backend"],
    "components": [{ "name": "Cash4" }]
  }
}
```

## ADF Building Blocks

### Paragraph
```json
{
  "type": "paragraph",
  "content": [{ "type": "text", "text": "Plain text" }]
}
```

### Heading
```json
{
  "type": "heading",
  "attrs": { "level": 2 },
  "content": [{ "type": "text", "text": "Heading Text" }]
}
```

### Bullet List
```json
{
  "type": "bulletList",
  "content": [
    {
      "type": "listItem",
      "content": [
        { "type": "paragraph", "content": [{ "type": "text", "text": "Item 1" }] }
      ]
    }
  ]
}
```

### Code Block
```json
{
  "type": "codeBlock",
  "attrs": { "language": "typescript" },
  "content": [{ "type": "text", "text": "const x = 1;" }]
}
```

### Bold/Italic
```json
{
  "type": "text",
  "text": "bold text",
  "marks": [{ "type": "strong" }]
}
```

## Field Reference

| Field | ID | Example Value |
|-------|-----|---------------|
| Project | `project` | `{ "key": "YOUR_PROJECT" }` |
| Summary | `summary` | String |
| Type | `issuetype` | `{ "name": "Story" }` |
| Story Points | `customfield_10016` | Number (1,2,3,5,8,13) |
| Sprint | `customfield_10020` | Sprint ID |
| Labels | `labels` | `["cash4", "frontend"]` |
| Components | `components` | `[{ "name": "Cash4" }]` |
| Epic Link | `customfield_10014` | Epic key |

## Story Point Guidelines

| Points | Scope |
|--------|-------|
| 1 | Config change, typo fix |
| 2 | Single file change, simple logic |
| 3 | Multi-file, straightforward |
| 5 | Feature with tests, multiple layers |
| 8 | Complex feature, many files |
| 13 | Large feature, needs breakdown |

## Example: Create via curl

```bash
curl -X POST "https://your-org.atlassian.net/rest/api/3/issue" \
  -H "Authorization: Basic $(echo -n "$JIRA_EMAIL:$JIRA_TOKEN" | base64)" \
  -H "Content-Type: application/json" \
  -d '{
    "fields": {
      "project": { "key": "YOUR_PROJECT" },
      "summary": "[Cash4] Add bank filter to dashboard",
      "issuetype": { "name": "Story" },
      "description": {
        "type": "doc",
        "version": 1,
        "content": [
          {
            "type": "paragraph",
            "content": [{ "type": "text", "text": "Add dropdown to filter by bank." }]
          }
        ]
      },
      "customfield_10016": 3,
      "labels": ["cash4", "frontend"]
    }
  }'
```
