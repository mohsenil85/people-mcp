# Explanation

Design decisions and architecture behind people-mcp.

## Architecture: Claude reasons, server persists

people-mcp follows the MCP pattern strictly: the server is a dumb data layer, and all intelligence lives in the host (Claude).

The server never decides *what* to write — it only handles *where* and *how*. Claude reads the job posting, reasons about how to tailor a resume, and sends the finished content to `save_application_file`. The server writes it to disk.

This split keeps the server simple and testable. There's no prompt engineering in the server, no LLM calls, no complex orchestration. It's file I/O, HTTP fetching, and subprocess management.

The `mock_interview` tool is the most interesting case: it doesn't *run* an interview. It assembles a briefing — your profile, the job posting, company materials, and interviewer guidance — then hands it all back to Claude. Claude plays the interviewer role using its own reasoning.

## The workspace model

### Why flat company directories

Each company gets one directory: `$PEOPLE_WORKSPACE/stripe/`, `$PEOPLE_WORKSPACE/anthropic/`, etc. No nesting, no hierarchy.

This keeps the mental model simple: one company, one folder. `list_applications` scans one level deep. There's no need for a database, no config file tracking which directory maps to which company. The directory name *is* the identifier.

### Why no filename whitelist

Company directories accept any file. There's no enum of allowed names like `["resume.tex", "coverletter.txt", "META.md"]`.

This is intentional. Users store different things per application — `company_research.md`, `interview_feedback.md`, `team_notes.md`, `referral_contact.txt`. A whitelist would force every new use case through a code change. Instead, `save_application_file` writes whatever Claude sends.

The tradeoff: `get_application` and `mock_interview_briefing` only read `TEXT_EXTENSIONS` (`.md`, `.tex`, `.txt`), so binary files won't accidentally get dumped into context. If you need a specific file, `read_application_file` reads anything.

### Why sanitize company names

Company names become directory names, so they need to be filesystem-safe. `_sanitize_company` lowercases, strips special characters, and replaces spaces with hyphens:

- "Jane Street" → `jane-street`
- "Anthropic, Inc." → `anthropic-inc`

This makes directories predictable and cross-platform safe. Lowercase prevents case-sensitivity issues between macOS (case-insensitive by default) and Linux (case-sensitive).

## Security model

### Filename validation

`_validate_filename` blocks four patterns:
1. Empty filenames
2. Path separators (`/`, `\`) — prevents writing outside the company directory
3. Leading dots — prevents creating dotfiles (`.env`, `.git`)
4. `..` anywhere — prevents path traversal (`../../etc/passwd`)

This is a defense-in-depth measure. The server already constructs paths from sanitized components, but validating filenames at the boundary catches mistakes and makes the security invariant explicit.

### Path traversal prevention

Paths are always constructed by joining known components:

```python
file_path = config.workspace_dir / _sanitize_company(company) / filename
```

Each piece is validated:
- `workspace_dir` comes from a trusted environment variable (or explicit override)
- `_sanitize_company` strips everything except `[a-z0-9_-]`
- `_validate_filename` rejects traversal patterns

There's no user-controlled path concatenation or string interpolation.

## Profile as resume.tex

The profile is read from `resume.tex` at the workspace root — not from a config file, not from a database, not bundled with the server.

Why: your resume is your single source of truth. It already has your skills, experience, and education in a structured format. Reading it directly means people-mcp always has the current version. No sync issues, no "remember to update your profile" step.

LaTeX format specifically because this is a tool for people who maintain LaTeX resumes. Claude reads LaTeX fluently — the markup doesn't impede comprehension and actually provides structural hints (sections, itemize environments, etc.).

## HTML stripping

`_html_to_text` uses regex, not an HTML parser like BeautifulSoup.

Why regex:
- **No extra dependency.** The server has two runtime deps: `mcp` and `httpx`. Adding `beautifulsoup4` + `lxml` would triple the surface area for something used in one function.
- **Good enough.** The output goes to Claude, which handles messy text well. Perfect HTML-to-text conversion isn't needed — we just need to remove tags so the text is readable.
- **Predictable.** The regex approach handles the common cases (strip tags, decode entities, normalize whitespace) in ~15 lines. Edge cases in malformed HTML won't cause parser crashes.

The tradeoff: deeply nested HTML, unusual entities, or JS-rendered content may produce noisy output. In practice, job posting pages are simple enough that this works well.

## LaTeX compilation

### Why lualatex

`lualatex` instead of `pdflatex` because:
- Native Unicode support — no `inputenc` package needed
- OpenType font support via `fontspec` — use system fonts directly
- Modern default that handles most LaTeX documents without configuration

The tradeoff: slightly slower compilation than `pdflatex`. Irrelevant for a single-file resume.

### Why async subprocess

`compile_resume` uses `asyncio.create_subprocess_exec` rather than `subprocess.run`. This keeps the MCP server's event loop responsive during compilation. A `lualatex` run can take several seconds — blocking the event loop would prevent the server from handling other requests.

The `-interaction=nonstopmode` flag tells LaTeX to not stop for user input on errors. Instead, it logs errors and exits. The server captures both stdout and stderr, and if the exit code is non-zero, wraps everything in a `WorkspaceError` so Claude can diagnose the failure.

## Interview types

The four interview types map to the most common interview stages in tech hiring:

- **Behavioral** — STAR method, past experiences. Universal across companies.
- **Technical** — System design, coding concepts. Matched to the role's tech stack.
- **Culture** — Mission alignment, work style. Uses saved company research.
- **Manager** — Hiring manager conversation. Role fit, career goals, mutual evaluation.

Each type has a `description` (what kind of interview this is) and `guidance` (instructions for Claude's interviewer persona). The guidance is prescriptive — it tells Claude *how* to conduct the interview, not just *what* to ask. This produces consistent, realistic interview practice.

The briefing includes all text materials from the company directory. This means the interviewer persona has access to the job posting, company research, strategy notes, and the candidate's tailored resume — just like a real interviewer would have context about the role and candidate.
