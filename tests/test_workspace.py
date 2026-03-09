"""Tests for jobkit_mcp.workspace."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from jobkit_mcp.workspace import (
    WorkspaceConfig,
    WorkspaceError,
    _html_to_text,
    _sanitize_company,
    _validate_filename,
    compile_resume,
    delete_application,
    fetch_url,
    get_application,
    get_profile,
    list_applications,
    mock_interview_briefing,
    read_application_file,
    save_application_file,
    save_job_posting,
)


# --- _sanitize_company ---

class TestSanitizeCompany:
    def test_lowercases(self):
        assert _sanitize_company("Stripe") == "stripe"

    def test_replaces_spaces(self):
        assert _sanitize_company("Some Company") == "some-company"

    def test_removes_special_chars(self):
        assert _sanitize_company("Acme, Inc.") == "acme-inc"

    def test_collapses_dashes(self):
        assert _sanitize_company("a - b") == "a-b"

    def test_strips_leading_trailing_dashes(self):
        assert _sanitize_company("  --hello--  ") == "hello"

    def test_empty_string(self):
        assert _sanitize_company("") == ""

    def test_only_special_chars(self):
        assert _sanitize_company("!!!") == ""

    def test_preserves_underscores(self):
        assert _sanitize_company("my_company") == "my_company"


# --- _validate_filename ---

class TestValidateFilename:
    def test_valid(self):
        _validate_filename("notes.md")  # should not raise

    def test_empty(self):
        with pytest.raises(WorkspaceError, match="empty"):
            _validate_filename("")

    def test_slash(self):
        with pytest.raises(WorkspaceError, match="path separators"):
            _validate_filename("../etc/passwd")

    def test_backslash(self):
        with pytest.raises(WorkspaceError, match="path separators"):
            _validate_filename("..\\etc\\passwd")

    def test_dotfile(self):
        with pytest.raises(WorkspaceError, match="dotfiles"):
            _validate_filename(".secret")

    def test_dot_dot(self):
        with pytest.raises(WorkspaceError, match="path traversal"):
            _validate_filename("foo..bar")


# --- _html_to_text ---

class TestHtmlToText:
    def test_strips_tags(self):
        assert _html_to_text("<b>hello</b>") == "hello"

    def test_decodes_entities(self):
        assert _html_to_text("&amp; &lt; &gt;") == "& < >"

    def test_strips_script(self):
        result = _html_to_text("<script>alert('xss')</script>hello")
        assert "alert" not in result
        assert "hello" in result

    def test_block_elements_become_newlines(self):
        result = _html_to_text("<p>a</p><p>b</p>")
        assert "\n" in result

    def test_collapses_whitespace(self):
        result = _html_to_text("a     b")
        assert result == "a b"

    def test_empty(self):
        assert _html_to_text("") == ""


# --- get_profile ---

class TestGetProfile:
    def test_reads_resume(self, workspace):
        result = get_profile(workspace)
        assert "John Doe" in result

    def test_missing_resume(self, tmp_path):
        config = WorkspaceConfig(workspace_dir=tmp_path)
        with pytest.raises(WorkspaceError, match="No resume.tex"):
            get_profile(config)


# --- list_applications ---

class TestListApplications:
    def test_empty_workspace(self, workspace):
        assert list_applications(workspace) == []

    def test_lists_companies(self, workspace):
        company_dir = workspace.workspace_dir / "acme"
        company_dir.mkdir()
        (company_dir / "notes.md").write_text("notes")
        (company_dir / "resume.pdf").write_text("")  # should be skipped
        result = list_applications(workspace)
        assert len(result) == 1
        assert result[0]["company"] == "acme"
        assert "notes.md" in result[0]["files"]
        assert "resume.pdf" not in result[0]["files"]

    def test_skips_dotdirs(self, workspace):
        (workspace.workspace_dir / ".hidden").mkdir()
        assert list_applications(workspace) == []

    def test_nonexistent_workspace(self, tmp_path):
        config = WorkspaceConfig(workspace_dir=tmp_path / "nope")
        assert list_applications(config) == []


# --- get_application ---

class TestGetApplication:
    def test_returns_text_files(self, workspace):
        company_dir = workspace.workspace_dir / "acme"
        company_dir.mkdir()
        (company_dir / "notes.md").write_text("my notes")
        (company_dir / "resume.tex").write_text("\\tex")
        (company_dir / "binary.pdf").write_text("pdf")  # not in TEXT_EXTENSIONS
        result = get_application(workspace, "Acme")
        assert "notes.md" in result["files"]
        assert "resume.tex" in result["files"]
        assert "binary.pdf" not in result["files"]

    def test_missing_company(self, workspace):
        with pytest.raises(WorkspaceError, match="No application found"):
            get_application(workspace, "nope")


# --- read_application_file ---

class TestReadApplicationFile:
    def test_reads_file(self, workspace):
        company_dir = workspace.workspace_dir / "acme"
        company_dir.mkdir()
        (company_dir / "notes.md").write_text("hello")
        assert read_application_file(workspace, "Acme", "notes.md") == "hello"

    def test_missing_file(self, workspace):
        company_dir = workspace.workspace_dir / "acme"
        company_dir.mkdir()
        with pytest.raises(WorkspaceError, match="File not found"):
            read_application_file(workspace, "Acme", "nope.md")


# --- save_application_file ---

class TestSaveApplicationFile:
    def test_creates_dir_and_file(self, workspace):
        result = save_application_file(workspace, "NewCo", "notes.md", "content")
        assert "Saved" in result
        assert (workspace.workspace_dir / "newco" / "notes.md").read_text() == "content"

    def test_overwrites_existing(self, workspace):
        save_application_file(workspace, "acme", "notes.md", "v1")
        save_application_file(workspace, "acme", "notes.md", "v2")
        assert (workspace.workspace_dir / "acme" / "notes.md").read_text() == "v2"


# --- delete_application ---

class TestDeleteApplication:
    def test_deletes_directory(self, workspace):
        company_dir = workspace.workspace_dir / "acme"
        company_dir.mkdir()
        (company_dir / "notes.md").write_text("x")
        result = delete_application(workspace, "Acme")
        assert "Deleted" in result
        assert not company_dir.exists()

    def test_missing_company(self, workspace):
        with pytest.raises(WorkspaceError, match="No application found"):
            delete_application(workspace, "nope")


# --- save_job_posting ---

class TestSaveJobPosting:
    @pytest.mark.asyncio
    async def test_with_content(self, workspace):
        result = await save_job_posting(workspace, "acme", content="We are hiring!")
        assert "Saved" in result
        saved = (workspace.workspace_dir / "acme" / "job_posting.md").read_text()
        assert saved == "We are hiring!"

    @pytest.mark.asyncio
    async def test_no_url_or_content(self, workspace):
        with pytest.raises(WorkspaceError, match="Must provide"):
            await save_job_posting(workspace, "acme")

    @pytest.mark.asyncio
    async def test_with_url(self, workspace):
        with patch("jobkit_mcp.workspace.fetch_url", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = "fetched job posting"
            result = await save_job_posting(workspace, "acme", url="https://example.com/job")
            mock_fetch.assert_called_once_with("https://example.com/job")
            assert "Saved" in result


# --- compile_resume ---

class TestCompileResume:
    @pytest.mark.asyncio
    async def test_success(self, workspace):
        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        mock_proc.communicate.return_value = (b"output", b"")

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc) as mock_exec:
            result = await compile_resume(workspace)
            assert "Compiled successfully" in result
            mock_exec.assert_called_once()

    @pytest.mark.asyncio
    async def test_failure(self, workspace):
        mock_proc = AsyncMock()
        mock_proc.returncode = 1
        mock_proc.communicate.return_value = (b"error output", b"stderr")

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            with pytest.raises(WorkspaceError, match="lualatex failed"):
                await compile_resume(workspace)

    @pytest.mark.asyncio
    async def test_missing_company(self, workspace):
        with pytest.raises(WorkspaceError, match="No application found"):
            await compile_resume(workspace, company="nope")

    @pytest.mark.asyncio
    async def test_company_no_tex(self, workspace):
        (workspace.workspace_dir / "acme").mkdir()
        with pytest.raises(WorkspaceError, match="No resume.tex"):
            await compile_resume(workspace, company="acme")


# --- fetch_url ---

class TestFetchUrl:
    @pytest.mark.asyncio
    async def test_html_content(self):
        mock_response = MagicMock()
        mock_response.headers = {"content-type": "text/html"}
        mock_response.text = "<p>Hello <b>world</b></p>"
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await fetch_url("https://example.com")
            assert "Hello" in result
            assert "<p>" not in result

    @pytest.mark.asyncio
    async def test_plain_text(self):
        mock_response = MagicMock()
        mock_response.headers = {"content-type": "text/plain"}
        mock_response.text = "plain text"
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await fetch_url("https://example.com")
            assert result == "plain text"


# --- mock_interview_briefing ---

class TestMockInterviewBriefing:
    def test_success(self, workspace):
        company_dir = workspace.workspace_dir / "acme"
        company_dir.mkdir()
        (company_dir / "job_posting.md").write_text("hiring engineers")
        (company_dir / "notes.md").write_text("research")

        result = mock_interview_briefing(workspace, "acme", "behavioral")
        assert result["interview_type"] == "behavioral"
        assert "job_posting.md" in result["materials"]
        assert "John Doe" in result["profile"]

    def test_invalid_type(self, workspace):
        company_dir = workspace.workspace_dir / "acme"
        company_dir.mkdir()
        with pytest.raises(WorkspaceError, match="Invalid interview type"):
            mock_interview_briefing(workspace, "acme", "invalid")

    def test_missing_company(self, workspace):
        with pytest.raises(WorkspaceError, match="No application found"):
            mock_interview_briefing(workspace, "nope")

    def test_no_job_posting(self, workspace):
        company_dir = workspace.workspace_dir / "acme"
        company_dir.mkdir()
        (company_dir / "notes.md").write_text("just notes")
        with pytest.raises(WorkspaceError, match="No job posting found"):
            mock_interview_briefing(workspace, "acme")


# --- WorkspaceConfig.from_env ---

class TestWorkspaceConfigFromEnv:
    def test_reads_env(self, monkeypatch, tmp_path):
        monkeypatch.setenv("JOBKIT_WORKSPACE", str(tmp_path))
        config = WorkspaceConfig.from_env()
        assert config.workspace_dir == tmp_path

    def test_missing_env(self, monkeypatch):
        monkeypatch.delenv("JOBKIT_WORKSPACE", raising=False)
        with pytest.raises(WorkspaceError, match="JOBKIT_WORKSPACE"):
            WorkspaceConfig.from_env()
