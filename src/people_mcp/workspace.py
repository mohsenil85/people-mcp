"""Domain logic: filesystem operations and HTTP fetching for job application workspace."""

import os
import re
from dataclasses import dataclass
from importlib import resources
from pathlib import Path

import httpx

VALID_FILES = frozenset({
    "job_posting",
    "company_research",
    "strategy",
    "interview_prep",
    "notes",
})


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


def _validate_file_type(file_type: str) -> None:
    if file_type not in VALID_FILES:
        raise WorkspaceError(
            f"Invalid file type: {file_type}. Must be one of: {', '.join(sorted(VALID_FILES))}"
        )


def get_profile() -> str:
    """Return the bundled professional profile."""
    return resources.files("people_mcp").joinpath("profile.md").read_text()


def list_applications(config: WorkspaceConfig) -> list[dict]:
    """List all application directories with their file status."""
    workspace = config.workspace_dir
    if not workspace.exists():
        return []

    applications = []
    for entry in sorted(workspace.iterdir()):
        if not entry.is_dir():
            continue
        files = [f.stem for f in entry.iterdir() if f.is_file() and f.suffix == ".md"]
        applications.append({
            "company": entry.name,
            "files": sorted(files),
        })
    return applications


def get_application(config: WorkspaceConfig, company: str) -> dict:
    """Get all content for one application."""
    company_dir = config.workspace_dir / _sanitize_company(company)
    if not company_dir.exists():
        raise WorkspaceError(f"No application found for: {company}")

    content = {}
    for f in sorted(company_dir.iterdir()):
        if f.is_file() and f.suffix == ".md":
            content[f.stem] = f.read_text()
    return {"company": company_dir.name, "files": content}


def read_application_file(config: WorkspaceConfig, company: str, file_type: str) -> str:
    """Read a single file from an application directory."""
    _validate_file_type(file_type)
    file_path = config.workspace_dir / _sanitize_company(company) / f"{file_type}.md"
    if not file_path.exists():
        raise WorkspaceError(f"File not found: {file_type} for {company}")
    return file_path.read_text()


def save_application_file(
    config: WorkspaceConfig, company: str, file_type: str, content: str
) -> str:
    """Save or update a file in an application directory."""
    _validate_file_type(file_type)
    company_dir = config.workspace_dir / _sanitize_company(company)
    company_dir.mkdir(parents=True, exist_ok=True)
    file_path = company_dir / f"{file_type}.md"
    file_path.write_text(content)
    return f"Saved {file_type}.md for {company_dir.name}"


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

    return save_application_file(config, company, "job_posting", text)
