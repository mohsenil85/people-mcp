# jobkit-mcp

[![CI](https://github.com/mohsenil85/jobkit-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/mohsenil85/jobkit-mcp/actions/workflows/ci.yml)
[![pyright: strict](https://img.shields.io/badge/pyright-strict-blue)](https://microsoft.github.io/pyright/)
[![Python 3.14+](https://img.shields.io/badge/python-3.14+-blue)](https://docs.python.org/3.14/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

MCP server for managing job application materials. Reads your resume from the workspace, fetches job postings and company info, compiles LaTeX resumes, and persists research, strategies, and interview prep per company. The host Claude does all reasoning — this server handles data access and persistence.

## Quickstart

Requires Python 3.14+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone <repo-url>
cd jobkit-mcp
uv sync
```

Add to `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "people": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/jobkit-mcp", "jobkit-mcp"],
      "env": {
        "JOBKIT_WORKSPACE": "/Users/you/Projects/resume"
      }
    }
  }
}
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

```
$JOBKIT_WORKSPACE/
├── resume.tex              # Base resume (used by get_profile)
├── coverletter.txt         # Base cover letter
├── META.md                 # Base strategy
├── stripe/
│   ├── resume.tex          # Tailored resume
│   ├── coverletter.txt     # Tailored cover letter
│   ├── META.md             # Application strategy
│   └── job_posting.md      # Saved job posting
└── anthropic/
    └── ...
```

Any file can be stored in a company directory — there is no whitelist. Build artifacts (`.aux`, `.log`, `.out`, `.pdf`, `.gz`, `.fls`, `.fdb_latexmk`) are skipped in listings.

## Documentation

- **[Tutorial](docs/tutorial.md)** — Walk through a complete application workflow end-to-end
- **[How-To Guides](docs/how-to.md)** — Focused recipes for specific tasks
- **[Reference](docs/reference.md)** — Complete tool parameters, return values, and internals
- **[Explanation](docs/explanation.md)** — Architecture decisions and design rationale
