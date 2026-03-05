"""FastMCP server for job application workspace management."""

from mcp.server.fastmcp import FastMCP

from people_mcp import workspace

mcp = FastMCP("people")


def _config(workspace_dir: str | None = None) -> workspace.WorkspaceConfig:
    if workspace_dir:
        from pathlib import Path
        return workspace.WorkspaceConfig(workspace_dir=Path(workspace_dir))
    return workspace.WorkspaceConfig.from_env()


@mcp.tool()
def get_profile() -> str:
    """Return the professional profile (resume summary, skills, experience)."""
    return workspace.get_profile()


@mcp.tool()
def list_applications(workspace_dir: str | None = None) -> list[dict]:
    """List all job application directories with their file status.

    Each application may contain: job_posting, company_research, strategy, interview_prep, notes.
    """
    return workspace.list_applications(_config(workspace_dir))


@mcp.tool()
def get_application(company: str, workspace_dir: str | None = None) -> dict:
    """Get all content for one application.

    Args:
        company: Company name (e.g. "stripe", "Anthropic")
    """
    return workspace.get_application(_config(workspace_dir), company)


@mcp.tool()
def read_application_file(
    company: str, file_type: str, workspace_dir: str | None = None
) -> str:
    """Read a single file from an application directory.

    Args:
        company: Company name
        file_type: One of: job_posting, company_research, strategy, interview_prep, notes
    """
    return workspace.read_application_file(_config(workspace_dir), company, file_type)


@mcp.tool()
def save_application_file(
    company: str, file_type: str, content: str, workspace_dir: str | None = None
) -> str:
    """Save or update a file in an application directory.

    Args:
        company: Company name
        file_type: One of: job_posting, company_research, strategy, interview_prep, notes
        content: Markdown content to save
    """
    return workspace.save_application_file(_config(workspace_dir), company, file_type, content)


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


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
