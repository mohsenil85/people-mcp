# people-mcp

MCP server for managing job application materials. Stores your professional profile, fetches job postings and company info, and persists research, strategies, and interview prep per company.

The host Claude does all reasoning — this server handles data access and persistence.

## Setup

Requires Python 3.14+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone <repo-url>
cd people-mcp
uv sync
```

Set the workspace directory where application materials are stored:

```bash
export PEOPLE_WORKSPACE=~/job-applications
```

## Usage

### Claude Code

Add to your Claude Code MCP config (`~/.claude/settings.json`):

```json
{
  "mcpServers": {
    "people": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/people-mcp", "people-mcp"],
      "env": {
        "PEOPLE_WORKSPACE": "/path/to/job-applications"
      }
    }
  }
}
```

### MCP Inspector

```bash
PEOPLE_WORKSPACE=/tmp/test-workspace uv run mcp dev src/people_mcp/server.py
```

## Tools

| Tool | Description |
|------|-------------|
| `get_profile` | Return bundled professional profile |
| `list_applications` | List all application directories with file status |
| `get_application` | Get all content for one company |
| `read_application_file` | Read a single file from an application |
| `save_application_file` | Save/update a file in an application |
| `delete_application` | Remove an entire application directory |
| `fetch_url` | Fetch a URL, return text with HTML stripped |
| `save_job_posting` | Fetch URL or accept pasted text, save as job posting |

## Workspace Layout

Each company gets a directory under `$PEOPLE_WORKSPACE` with markdown files:

```
$PEOPLE_WORKSPACE/
├── stripe/
│   ├── job_posting.md
│   ├── company_research.md
│   ├── strategy.md
│   ├── interview_prep.md
│   └── notes.md
└── anthropic/
    └── ...
```

File types: `job_posting`, `company_research`, `strategy`, `interview_prep`, `notes`.

## How It Works

- **Profile** is bundled in the package (`src/people_mcp/profile.md`) — edit it directly
- **Company names** are sanitized to `[a-z0-9_-]` for safe directory names ("Jane Street" becomes `jane-street`)
- **HTML stripping** uses regex — no external parsing deps; Claude interprets the output fine
- **HTTP** uses httpx for async fetching with redirects and a 30s timeout
