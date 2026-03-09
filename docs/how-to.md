# How-To Guides

Focused recipes for common tasks. Each guide is self-contained.

## Configure jobkit-mcp with Claude Code

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

Replace both paths with your actual directories. Restart Claude Code after saving.

## Configure jobkit-mcp with MCP Inspector

```bash
JOBKIT_WORKSPACE=~/Projects/resume uv run mcp dev src/jobkit_mcp/server.py
```

This opens the MCP Inspector UI where you can call tools directly and inspect responses.

## Save a job posting from a URL

> Save this job posting for Anthropic: https://anthropic.com/jobs/engineer

Claude calls `save_job_posting(company="Anthropic", url="https://...")`. The server fetches the page, strips HTML, and writes `job_posting.md` in the company directory.

If the URL requires authentication or the fetch fails, paste the text instead.

## Save a job posting from pasted text

> Save this job posting for Anthropic:
>
> We're looking for a software engineer to work on...

Claude calls `save_job_posting(company="Anthropic", content="We're looking for...")`. No HTTP request — the text is saved directly.

## Research a company and save notes

> Research Anthropic — their product roadmap, engineering culture, and recent funding. Save your findings as company research.

Claude will search the web, then call `save_application_file(company="Anthropic", filename="company_research.md", content=...)`.

You can use any filename. Common choices:
- `company_research.md` — general research
- `team_notes.md` — notes about specific teams
- `news.md` — recent press coverage

## Tailor and compile a LaTeX resume

### 1. Tailor the resume

> Tailor my resume for this Anthropic role. Emphasize ML infrastructure experience.

Claude reads your base `resume.tex` via `get_profile`, reads the job posting via `get_application`, then saves a tailored version:

```
save_application_file(company="Anthropic", filename="resume.tex", content=...)
```

### 2. Compile to PDF

> Compile my Anthropic resume.

```
compile_resume(company="Anthropic")
```

Runs `lualatex` in the `anthropic/` directory. The output PDF lands at `anthropic/resume.pdf`.

### Compile the base resume

> Compile my base resume.

```
compile_resume()
```

Runs `lualatex` in the workspace root. Output: `$JOBKIT_WORKSPACE/resume.pdf`.

### Fix compilation errors

If `lualatex` fails, Claude sees the full error output. Ask:

> Fix the LaTeX errors and recompile.

Claude will read the `.tex` file, fix issues, save it, and compile again.

## Run a mock interview

### Behavioral interview

> Run a mock behavioral interview for Anthropic.

```
mock_interview(company="Anthropic", interview_type="behavioral")
```

Uses the STAR method. Probes for specifics about past experiences — teamwork, conflict, failure, leadership.

### Technical interview

> Run a mock technical interview for Anthropic.

```
mock_interview(company="Anthropic", interview_type="technical")
```

Questions matched to the role's tech stack and seniority. Covers system design, coding concepts, trade-offs.

### Culture fit interview

> Run a mock culture interview for Anthropic.

```
mock_interview(company="Anthropic", interview_type="culture")
```

Explores alignment with company mission, values, and work environment preferences.

### Hiring manager interview

> Run a mock manager interview for Anthropic.

```
mock_interview(company="Anthropic", interview_type="manager")
```

Acts as the hiring manager. Covers role fit, career goals, 90-day expectations, and lets you ask questions.

### Save interview feedback

After any mock interview:

> Save the feedback from that interview.

Claude calls `save_application_file` with a filename like `interview_feedback.md`.

## Read, update, and delete application files

### List all applications

> Show me all my applications.

```
list_applications()
```

Returns each company directory name and its files (excluding build artifacts).

### Read all files for a company

> Show me everything for Anthropic.

```
get_application(company="Anthropic")
```

Returns the content of all text files (`.md`, `.tex`, `.txt`) in the company directory.

### Read a specific file

> Show me the Anthropic job posting.

```
read_application_file(company="Anthropic", filename="job_posting.md")
```

### Update a file

> Update my Anthropic strategy with these changes...

```
save_application_file(company="Anthropic", filename="META.md", content=...)
```

Overwrites the file if it exists, creates it if it doesn't.

### Delete an entire application

> Delete the Anthropic application.

```
delete_application(company="Anthropic")
```

Removes the entire company directory and all files. This is irreversible.

## Use a custom workspace directory

Every tool accepts an optional `workspace_dir` parameter that overrides `JOBKIT_WORKSPACE` for that single call.

> Read my profile from ~/Projects/alt-resume.

Claude calls `get_profile(workspace_dir="~/Projects/alt-resume")`.

This is useful if you maintain multiple workspace directories (e.g., one per field or resume variant). The override applies only to that one tool call — subsequent calls still use `JOBKIT_WORKSPACE`.
