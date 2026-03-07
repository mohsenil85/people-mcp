import pytest

from people_mcp.workspace import WorkspaceConfig


@pytest.fixture
def workspace(tmp_path):
    """Create a WorkspaceConfig pointing at a temporary directory with a base resume."""
    resume = tmp_path / "resume.tex"
    resume.write_text("\\documentclass{article}\n\\begin{document}\nJohn Doe\n\\end{document}")
    return WorkspaceConfig(workspace_dir=tmp_path)
