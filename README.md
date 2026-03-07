# people-mcp

MCP server for managing job application materials. Reads your resume from the workspace, fetches job postings and company info, compiles LaTeX resumes, and persists research, strategies, and interview prep per company.

The host Claude does all reasoning — this server handles data access and persistence.

## Setup

Requires Python 3.14+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone <repo-url>
cd people-mcp
uv sync
```

Set the workspace directory to your resume project:

```bash
export PEOPLE_WORKSPACE=~/Projects/resume
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
        "PEOPLE_WORKSPACE": "/Users/you/Projects/resume"
      }
    }
  }
}
```

### MCP Inspector

```bash
PEOPLE_WORKSPACE=~/Projects/resume uv run mcp dev src/people_mcp/server.py
```

## Tools

| Tool | Description |
|------|-------------|
| `get_profile` | Read resume.tex from workspace root as professional profile |
| `list_applications` | List all application directories with their files |
| `get_application` | Get all text file content for one company |
| `read_application_file` | Read any file from an application by filename |
| `save_application_file` | Save/update any file in an application |
| `delete_application` | Remove an entire application directory |
| `fetch_url` | Fetch a URL, return text with HTML stripped |
| `save_job_posting` | Fetch URL or accept pasted text, save as job posting |
| `compile_resume` | Compile resume.tex with lualatex (company dir or root) |
| `mock_interview` | Start a mock interview — returns briefing for Claude to play interviewer |

## Workspace Layout

Point `$PEOPLE_WORKSPACE` at your resume project. The root contains the base resume, and each company gets a subdirectory with tailored materials:

```
$PEOPLE_WORKSPACE/
├── resume.tex              # Base resume (used by get_profile)
├── coverletter.txt         # Base cover letter
├── META.md                 # Base strategy
├── Makefile
├── deel/
│   ├── resume.tex          # Tailored resume
│   ├── coverletter.txt     # Tailored cover letter
│   ├── META.md             # Application strategy
│   └── job_posting.md      # Saved job posting
├── gusto/
│   └── ...
└── rippling/
    └── ...
```

Any file can be stored in a company directory — there is no whitelist. Binary/build artifacts (`.aux`, `.log`, `.out`, `.pdf`) are skipped in listings.

## How It Works

- **Profile** is read from `resume.tex` at the workspace root — your single source of truth
- **Company names** are sanitized to `[a-z0-9_-]` for safe directory names ("Jane Street" becomes `jane-street`)
- **Filenames** are validated to prevent path traversal (no `/`, `\`, `..`, or dotfiles)
- **HTML stripping** uses regex — no external parsing deps; Claude interprets the output fine
- **HTTP** uses httpx for async fetching with redirects and a 30s timeout
- **LaTeX compilation** runs `lualatex` via asyncio subprocess
