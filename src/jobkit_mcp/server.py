"""FastMCP server for job application workspace management."""

from pathlib import Path

from mcp.server.fastmcp import FastMCP

from jobkit_mcp import workspace

mcp = FastMCP("jobkit")


def _config(workspace_dir: str | None = None) -> workspace.WorkspaceConfig:
    if workspace_dir:
        return workspace.WorkspaceConfig(workspace_dir=Path(workspace_dir))
    return workspace.WorkspaceConfig.from_env()


@mcp.tool()
def get_profile(workspace_dir: str | None = None) -> str:
    """Return the professional profile by reading resume.tex from the workspace root."""
    return workspace.get_profile(_config(workspace_dir))


@mcp.tool()
def list_applications(workspace_dir: str | None = None) -> list[workspace.ApplicationSummary]:
    """List all job application directories with their files.

    Each application directory may contain resume.tex, coverletter.txt, META.md,
    job_posting.md, and any other research or strategy documents.
    """
    return workspace.list_applications(_config(workspace_dir))


@mcp.tool()
def get_application(company: str, workspace_dir: str | None = None) -> workspace.ApplicationDetail:
    """Get all text file content for one application.

    Args:
        company: Company name (e.g. "stripe", "Anthropic")
    """
    return workspace.get_application(_config(workspace_dir), company)


@mcp.tool()
def read_application_file(
    company: str, filename: str, workspace_dir: str | None = None
) -> str:
    """Read a single file from an application directory.

    Args:
        company: Company name
        filename: Name of the file to read (e.g. "resume.tex", "META.md", "job_posting.md")
    """
    return workspace.read_application_file(_config(workspace_dir), company, filename)


@mcp.tool()
def save_application_file(
    company: str, filename: str, content: str, workspace_dir: str | None = None
) -> str:
    """Save or update a file in an application directory.

    Args:
        company: Company name
        filename: Name of the file to save (e.g. "notes.md", "company_research.md")
        content: Content to save
    """
    return workspace.save_application_file(_config(workspace_dir), company, filename, content)


@mcp.tool()
def delete_application(company: str, workspace_dir: str | None = None) -> str:
    """Remove an entire application directory and all its files.

    Args:
        company: Company name
    """
    return workspace.delete_application(_config(workspace_dir), company)


@mcp.tool()
async def fetch_url(url: str) -> str:
    """Fetch a URL and return its text content (HTML tags stripped).

    Args:
        url: Full URL to fetch
    """
    return await workspace.fetch_url(url)


@mcp.tool()
async def save_job_posting(
    company: str,
    url: str | None = None,
    content: str | None = None,
    workspace_dir: str | None = None,
) -> str:
    """Fetch a job posting URL or accept pasted text, and save it for a company.

    Args:
        company: Company name
        url: URL of the job posting to fetch (provide url or content, not both)
        content: Pasted job posting text (provide url or content, not both)
    """
    return await workspace.save_job_posting(
        _config(workspace_dir), company, url=url, content=content
    )


@mcp.tool()
async def compile_resume(
    company: str | None = None, workspace_dir: str | None = None
) -> str:
    """Compile resume.tex using lualatex. Compiles in a company directory, or the
    workspace root if no company is specified.

    Args:
        company: Company name (optional — omit to compile the base resume)
    """
    return await workspace.compile_resume(_config(workspace_dir), company)


@mcp.tool()
def mock_interview(
    company: str,
    interview_type: str = "behavioral",
    workspace_dir: str | None = None,
) -> workspace.InterviewBriefing:
    """Start a mock interview session. Returns a briefing with all application materials,
    your profile, and interviewer guidance so Claude can play the interviewer role.

    After the session, save feedback and areas to improve using save_application_file.

    Args:
        company: Company name
        interview_type: One of: behavioral, technical, culture, manager
    """
    return workspace.mock_interview_briefing(
        _config(workspace_dir), company, interview_type
    )


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
