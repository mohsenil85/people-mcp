# Reference

Complete, authoritative reference for people-mcp.

## Configuration

### `PEOPLE_WORKSPACE` environment variable

The workspace root directory. Must be set unless every tool call provides `workspace_dir`.

```bash
export PEOPLE_WORKSPACE=~/Projects/resume
```

### `WorkspaceConfig`

Dataclass holding the workspace path.

```python
@dataclass
class WorkspaceConfig:
    workspace_dir: Path

    @classmethod
    def from_env(cls) -> "WorkspaceConfig":
        # Reads PEOPLE_WORKSPACE; raises WorkspaceError if unset
```

### `workspace_dir` override

Every tool accepts an optional `workspace_dir: str | None` parameter. When provided, it overrides `PEOPLE_WORKSPACE` for that call only.

---

## Tool Reference

### `get_profile`

Read `resume.tex` from the workspace root.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `workspace_dir` | `str \| None` | No | `None` | Override workspace path |

**Returns:** `str` — contents of `resume.tex`

**Errors:**
- `WorkspaceError` if `resume.tex` does not exist at workspace root

---

### `list_applications`

List all application directories and their files.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `workspace_dir` | `str \| None` | No | `None` | Override workspace path |

**Returns:** `list[dict]` — each dict has:
- `company: str` — directory name
- `files: list[str]` — filenames (excludes extensions in `SKIP_EXTENSIONS`)

Skips dotfile directories. Returns `[]` if workspace doesn't exist.

---

### `get_application`

Get all text file content for one company.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `company` | `str` | Yes | — | Company name (sanitized automatically) |
| `workspace_dir` | `str \| None` | No | `None` | Override workspace path |

**Returns:** `dict` with:
- `company: str` — sanitized directory name
- `files: dict[str, str]` — filename → content (only files with extensions in `TEXT_EXTENSIONS`)

**Errors:**
- `WorkspaceError` if company directory does not exist

---

### `read_application_file`

Read a single file from an application directory.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `company` | `str` | Yes | — | Company name |
| `filename` | `str` | Yes | — | File to read (e.g. `"resume.tex"`) |
| `workspace_dir` | `str \| None` | No | `None` | Override workspace path |

**Returns:** `str` — file contents

**Errors:**
- `WorkspaceError` if filename fails validation (see [Filename Validation](#filename-validation))
- `WorkspaceError` if file does not exist

---

### `save_application_file`

Save or update a file in an application directory. Creates the company directory if needed.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `company` | `str` | Yes | — | Company name |
| `filename` | `str` | Yes | — | File to save |
| `content` | `str` | Yes | — | Content to write |
| `workspace_dir` | `str \| None` | No | `None` | Override workspace path |

**Returns:** `str` — `"Saved {filename} for {sanitized_company}"`

**Errors:**
- `WorkspaceError` if filename fails validation

---

### `delete_application`

Remove an entire application directory and all its files.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `company` | `str` | Yes | — | Company name |
| `workspace_dir` | `str \| None` | No | `None` | Override workspace path |

**Returns:** `str` — `"Deleted application: {sanitized_company}"`

**Errors:**
- `WorkspaceError` if company directory does not exist

---

### `fetch_url`

Fetch a URL and return text content with HTML stripped.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `url` | `str` | Yes | — | Full URL to fetch |

**Returns:** `str` — page text (HTML stripped if content-type contains `"html"`)

**Errors:**
- `httpx.HTTPStatusError` on non-2xx responses

**Details:**
- Uses `httpx.AsyncClient` with `follow_redirects=True` and `timeout=30.0`
- User-Agent: `people-mcp/0.1.0`
- HTML stripping via `_html_to_text` (see [Internals](#html-stripping))

---

### `save_job_posting`

Fetch a job posting URL or accept pasted text, save as `job_posting.md`.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `company` | `str` | Yes | — | Company name |
| `url` | `str \| None` | No | `None` | URL to fetch |
| `content` | `str \| None` | No | `None` | Pasted text |
| `workspace_dir` | `str \| None` | No | `None` | Override workspace path |

Provide `url` or `content`, not both.

**Returns:** `str` — `"Saved job_posting.md for {sanitized_company}"`

**Errors:**
- `WorkspaceError` if neither `url` nor `content` provided

---

### `compile_resume`

Compile `resume.tex` with `lualatex`.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `company` | `str \| None` | No | `None` | Company name (omit for base resume) |
| `workspace_dir` | `str \| None` | No | `None` | Override workspace path |

**Returns:** `str` — `"Compiled successfully: {pdf_path}\n\n{stdout}"`

**Errors:**
- `WorkspaceError` if company directory does not exist (when `company` is specified)
- `WorkspaceError` if `resume.tex` does not exist in the target directory
- `WorkspaceError` if `lualatex` exits with non-zero code (includes stdout and stderr)

**Details:**
- Runs `lualatex -interaction=nonstopmode resume.tex` via `asyncio.create_subprocess_exec`
- Working directory is the company directory (or workspace root)

---

### `mock_interview`

Start a mock interview session. Returns a briefing for Claude to play interviewer.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `company` | `str` | Yes | — | Company name |
| `interview_type` | `str` | No | `"behavioral"` | One of: `behavioral`, `technical`, `culture`, `manager` |
| `workspace_dir` | `str \| None` | No | `None` | Override workspace path |

**Returns:** `dict` with:
- `interview_type: str`
- `interview_description: str`
- `interviewer_guidance: str`
- `company: str` — sanitized name
- `profile: str` — contents of base `resume.tex`
- `materials: dict[str, str]` — all text files from the company directory

**Errors:**
- `WorkspaceError` if `interview_type` is not one of the four valid types
- `WorkspaceError` if company directory does not exist
- `WorkspaceError` if no file containing `"job_posting"` in its name exists

---

## Workspace Layout

```
$PEOPLE_WORKSPACE/
├── resume.tex              # Base resume (read by get_profile)
├── coverletter.txt         # Base cover letter (optional)
├── META.md                 # Base strategy (optional)
├── Makefile                # Your build tooling (optional)
├── stripe/
│   ├── resume.tex          # Tailored resume
│   ├── coverletter.txt     # Tailored cover letter
│   ├── META.md             # Application strategy
│   └── job_posting.md      # Saved job posting
├── anthropic/
│   └── ...
└── gusto/
    └── ...
```

### `SKIP_EXTENSIONS`

Extensions excluded from `list_applications` file listings:

```python
frozenset({".aux", ".log", ".out", ".pdf", ".gz", ".fls", ".fdb_latexmk"})
```

### `TEXT_EXTENSIONS`

Extensions read by `get_application` and `mock_interview_briefing`:

```python
frozenset({".md", ".tex", ".txt"})
```

Files with other extensions are stored but not included in bulk reads — use `read_application_file` to access them directly.

---

## Internals

### Company Name Sanitization

`_sanitize_company(name: str) -> str`

Transforms a human-readable company name into a safe directory name:

1. Lowercase and strip whitespace
2. Remove characters not matching `[a-z0-9_\-\s]`
3. Replace whitespace runs with `-`
4. Collapse consecutive `-` into one
5. Strip leading/trailing `-`

Examples:
| Input | Output |
|-------|--------|
| `"Stripe"` | `"stripe"` |
| `"Jane Street"` | `"jane-street"` |
| `"Anthropic, Inc."` | `"anthropic-inc"` |
| `"  Deel  "` | `"deel"` |

### Filename Validation

`_validate_filename(filename: str) -> None`

Rejects filenames that could cause path traversal or access hidden files:

- Empty string → error
- Contains `/` or `\` → error
- Starts with `.` → error
- Contains `..` → error

### HTML Stripping

`_html_to_text(html: str) -> str`

Regex-based HTML-to-text conversion:

1. Remove `<script>` and `<style>` blocks (with content)
2. Replace block elements (`<br>`, `<p>`, `<div>`, `<h1>`–`<h6>`, `<li>`, `<tr>`) with newlines
3. Strip all remaining tags
4. Decode entities: `&amp;`, `&lt;`, `&gt;`, `&quot;`, `&#39;`, `&nbsp;`
5. Collapse horizontal whitespace (spaces/tabs)
6. Collapse 3+ consecutive newlines into 2

### Interview Types

```python
INTERVIEW_TYPES = {
    "behavioral": {
        "description": "Behavioral interview focusing on past experiences, teamwork, "
                       "conflict resolution, and leadership using the STAR method.",
        "guidance": "Ask behavioral questions using the STAR method..."
    },
    "technical": {
        "description": "Technical interview covering system design, coding concepts, "
                       "and architecture relevant to the role.",
        "guidance": "Ask technical questions matched to the role's tech stack..."
    },
    "culture": {
        "description": "Culture fit and values interview exploring alignment with "
                       "company mission and team dynamics.",
        "guidance": "Ask questions that explore alignment with the company's mission..."
    },
    "manager": {
        "description": "Hiring manager interview covering role fit, career goals, "
                       "and mutual expectations.",
        "guidance": "Act as the hiring manager for this role..."
    },
}
```

Each type provides a `description` (shown in the briefing) and `guidance` (instructions for Claude's interviewer persona).

### HTTP Client

`fetch_url` uses `httpx.AsyncClient` with:
- `follow_redirects=True`
- `timeout=30.0` seconds
- `User-Agent: people-mcp/0.1.0`
- HTML auto-detected via `content-type` header

### LaTeX Compilation

`compile_resume` uses `asyncio.create_subprocess_exec` to run:

```
lualatex -interaction=nonstopmode resume.tex
```

- Working directory: company dir or workspace root
- Captures both stdout and stderr
- Non-zero exit raises `WorkspaceError` with full output
