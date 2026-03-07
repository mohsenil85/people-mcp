"""Domain logic: filesystem operations and HTTP fetching for job application workspace."""

import asyncio
import os
import re
from dataclasses import dataclass
from pathlib import Path

import httpx

# Binary/build artifacts to skip in listings
SKIP_EXTENSIONS = frozenset({".aux", ".log", ".out", ".pdf", ".gz", ".fls", ".fdb_latexmk"})

# Text file extensions to read in get_application / mock_interview_briefing
TEXT_EXTENSIONS = frozenset({".md", ".tex", ".txt"})


class WorkspaceError(Exception):
    pass


@dataclass
class WorkspaceConfig:
    workspace_dir: Path

    @classmethod
    def from_env(cls) -> "WorkspaceConfig":
        workspace = os.environ.get("PEOPLE_WORKSPACE")
        if not workspace:
            raise WorkspaceError("PEOPLE_WORKSPACE environment variable is not set")
        return cls(workspace_dir=Path(workspace))


def _sanitize_company(name: str) -> str:
    """Sanitize company name to [a-z0-9_-] for safe directory names."""
    name = name.lower().strip()
    name = re.sub(r"[^a-z0-9_\-\s]", "", name)
    name = re.sub(r"[\s]+", "-", name)
    name = re.sub(r"-+", "-", name)
    return name.strip("-")


def _validate_filename(filename: str) -> None:
    """Reject path traversal and absolute paths."""
    if not filename:
        raise WorkspaceError("Filename cannot be empty")
    if "/" in filename or "\\" in filename:
        raise WorkspaceError(f"Invalid filename (no path separators allowed): {filename}")
    if filename.startswith("."):
        raise WorkspaceError(f"Invalid filename (no dotfiles): {filename}")
    if ".." in filename:
        raise WorkspaceError(f"Invalid filename (no path traversal): {filename}")


def get_profile(config: WorkspaceConfig) -> str:
    """Read the base resume.tex from the workspace root as the professional profile."""
    resume_path = config.workspace_dir / "resume.tex"
    if not resume_path.exists():
        raise WorkspaceError(f"No resume.tex found at workspace root: {config.workspace_dir}")
    return resume_path.read_text()


def list_applications(config: WorkspaceConfig) -> list[dict]:
    """List all application directories with their files."""
    workspace = config.workspace_dir
    if not workspace.exists():
        return []

    applications = []
    for entry in sorted(workspace.iterdir()):
        if not entry.is_dir() or entry.name.startswith("."):
            continue
        files = [
            f.name for f in sorted(entry.iterdir())
            if f.is_file() and f.suffix not in SKIP_EXTENSIONS
        ]
        applications.append({
            "company": entry.name,
            "files": files,
        })
    return applications


def get_application(config: WorkspaceConfig, company: str) -> dict:
    """Get all text file content for one application."""
    company_dir = config.workspace_dir / _sanitize_company(company)
    if not company_dir.exists():
        raise WorkspaceError(f"No application found for: {company}")

    content = {}
    for f in sorted(company_dir.iterdir()):
        if f.is_file() and f.suffix in TEXT_EXTENSIONS:
            content[f.name] = f.read_text()
    return {"company": company_dir.name, "files": content}


def read_application_file(config: WorkspaceConfig, company: str, filename: str) -> str:
    """Read a single file from an application directory."""
    _validate_filename(filename)
    file_path = config.workspace_dir / _sanitize_company(company) / filename
    if not file_path.exists():
        raise WorkspaceError(f"File not found: {filename} for {company}")
    return file_path.read_text()


def save_application_file(
    config: WorkspaceConfig, company: str, filename: str, content: str
) -> str:
    """Save or update a file in an application directory."""
    _validate_filename(filename)
    company_dir = config.workspace_dir / _sanitize_company(company)
    company_dir.mkdir(parents=True, exist_ok=True)
    file_path = company_dir / filename
    file_path.write_text(content)
    return f"Saved {filename} for {company_dir.name}"


def delete_application(config: WorkspaceConfig, company: str) -> str:
    """Remove an entire application directory."""
    company_dir = config.workspace_dir / _sanitize_company(company)
    if not company_dir.exists():
        raise WorkspaceError(f"No application found for: {company}")

    import shutil

    shutil.rmtree(company_dir)
    return f"Deleted application: {company_dir.name}"


def _html_to_text(html: str) -> str:
    """Strip HTML tags and decode entities via regex. Imperfect but sufficient."""
    # Remove script and style blocks
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", html, flags=re.DOTALL | re.IGNORECASE)
    # Replace block elements with newlines
    text = re.sub(r"<(br|p|div|h[1-6]|li|tr)[^>]*>", "\n", text, flags=re.IGNORECASE)
    # Strip remaining tags
    text = re.sub(r"<[^>]+>", "", text)
    # Decode common entities
    for entity, char in [("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"),
                         ("&quot;", '"'), ("&#39;", "'"), ("&nbsp;", " ")]:
        text = text.replace(entity, char)
    # Collapse whitespace
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


async def fetch_url(url: str) -> str:
    """Fetch a URL and return text content with HTML stripped."""
    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        response = await client.get(
            url,
            headers={"User-Agent": "people-mcp/0.1.0"},
        )
        response.raise_for_status()

    content_type = response.headers.get("content-type", "")
    text = response.text
    if "html" in content_type:
        text = _html_to_text(text)
    return text


async def save_job_posting(
    config: WorkspaceConfig, company: str, *, url: str | None = None, content: str | None = None
) -> str:
    """Fetch URL or accept pasted text, save as job posting."""
    if url:
        text = await fetch_url(url)
    elif content:
        text = content
    else:
        raise WorkspaceError("Must provide either url or content")

    return save_application_file(config, company, "job_posting.md", text)


async def compile_resume(config: WorkspaceConfig, company: str | None = None) -> str:
    """Run lualatex to compile resume.tex in a company directory (or workspace root)."""
    if company:
        target_dir = config.workspace_dir / _sanitize_company(company)
        if not target_dir.exists():
            raise WorkspaceError(f"No application found for: {company}")
    else:
        target_dir = config.workspace_dir

    tex_file = target_dir / "resume.tex"
    if not tex_file.exists():
        raise WorkspaceError(f"No resume.tex found in: {target_dir}")

    proc = await asyncio.create_subprocess_exec(
        "lualatex", "-interaction=nonstopmode", "resume.tex",
        cwd=target_dir,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()

    output = stdout.decode(errors="replace")
    errors = stderr.decode(errors="replace")
    pdf_path = target_dir / "resume.pdf"

    if proc.returncode != 0:
        raise WorkspaceError(
            f"lualatex failed (exit {proc.returncode}):\n{output}\n{errors}"
        )

    return f"Compiled successfully: {pdf_path}\n\n{output}"


INTERVIEW_TYPES = {
    "behavioral": {
        "description": "Behavioral interview focusing on past experiences, teamwork, conflict resolution, and leadership using the STAR method.",
        "guidance": (
            "Ask behavioral questions using the STAR method (Situation, Task, Action, Result). "
            "Probe for specifics — don't let the candidate stay vague. Ask follow-ups like "
            "'What was YOUR specific role?' and 'What would you do differently?' "
            "Cover: teamwork, conflict, failure, leadership, ambiguity. "
            "Tailor questions to the seniority level and role described in the job posting."
        ),
    },
    "technical": {
        "description": "Technical interview covering system design, coding concepts, and architecture relevant to the role.",
        "guidance": (
            "Ask technical questions matched to the role's tech stack and seniority. "
            "Start with a warm-up concept question, then move to a design or coding problem. "
            "Ask the candidate to talk through their thinking. Probe trade-offs: "
            "'Why that approach over X?' Push on scalability, error handling, edge cases. "
            "For senior roles, focus on architecture and system design over syntax."
        ),
    },
    "culture": {
        "description": "Culture fit and values interview exploring alignment with company mission and team dynamics.",
        "guidance": (
            "Ask questions that explore alignment with the company's mission and values. "
            "Use the company research to reference specific initiatives or cultural traits. "
            "Probe: 'Why this company?', 'What work environment do you thrive in?', "
            "'How do you approach disagreements on technical direction?' "
            "Look for genuine enthusiasm and specific knowledge of the company."
        ),
    },
    "manager": {
        "description": "Hiring manager interview covering role fit, career goals, and mutual expectations.",
        "guidance": (
            "Act as the hiring manager for this role. Ask about: motivation for applying, "
            "relevant experience, what success looks like in the first 90 days, career goals, "
            "and questions the candidate has about the team. Be conversational but evaluative. "
            "Probe gaps between the candidate's experience and the job requirements. "
            "End by asking what questions they have for you — and answer them in character."
        ),
    },
}


def mock_interview_briefing(
    config: WorkspaceConfig, company: str, interview_type: str = "behavioral"
) -> dict:
    """Assemble a mock interview briefing from application materials and profile."""
    if interview_type not in INTERVIEW_TYPES:
        raise WorkspaceError(
            f"Invalid interview type: {interview_type}. "
            f"Must be one of: {', '.join(sorted(INTERVIEW_TYPES))}"
        )

    company_dir = config.workspace_dir / _sanitize_company(company)
    if not company_dir.exists():
        raise WorkspaceError(f"No application found for: {company}")

    # Gather all text materials
    materials = {}
    for f in sorted(company_dir.iterdir()):
        if f.is_file() and f.suffix in TEXT_EXTENSIONS:
            materials[f.name] = f.read_text()

    if not any("job_posting" in name for name in materials):
        raise WorkspaceError(
            f"No job posting found for {company}. Save one first with save_job_posting."
        )

    interview = INTERVIEW_TYPES[interview_type]

    return {
        "interview_type": interview_type,
        "interview_description": interview["description"],
        "interviewer_guidance": interview["guidance"],
        "company": company_dir.name,
        "profile": get_profile(config),
        "materials": materials,
    }
