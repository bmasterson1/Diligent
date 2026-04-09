"""Tests for diligent install command."""

from unittest.mock import patch

from click.testing import CliRunner

from diligent.cli import cli


@patch("shutil.which", return_value="/usr/local/bin/diligent")
def test_install_to_custom_path(mock_which, tmp_path):
    """Install writes 6 skill files to the specified directory."""
    runner = CliRunner()
    result = runner.invoke(cli, ["install", "--path", str(tmp_path)])

    assert result.exit_code == 0
    files = list(tmp_path.glob("dd_*.md"))
    assert len(files) == 6, f"Expected 6 files, got {len(files)}: {files}"
    assert "Installed 6 skill files" in result.output


@patch("shutil.which", return_value="/usr/local/bin/diligent")
def test_installed_files_have_resolved_path(mock_which, tmp_path):
    """Installed files contain actual CLI path, not the template token."""
    runner = CliRunner()
    runner.invoke(cli, ["install", "--path", str(tmp_path)])

    for f in tmp_path.glob("dd_*.md"):
        content = f.read_text(encoding="utf-8")
        assert "{{DILIGENT_PATH}}" not in content, (
            f"{f.name} still has template token"
        )
        assert "/usr/local/bin/diligent" in content, (
            f"{f.name} missing resolved path"
        )


@patch("shutil.which", return_value=None)
def test_install_fallback_when_binary_not_found(mock_which, tmp_path):
    """When shutil.which returns None, use 'diligent' and warn."""
    runner = CliRunner()
    result = runner.invoke(cli, ["install", "--path", str(tmp_path)])

    assert result.exit_code == 0
    assert "Could not find diligent binary" in result.output

    for f in tmp_path.glob("dd_*.md"):
        content = f.read_text(encoding="utf-8")
        assert "{{DILIGENT_PATH}}" not in content
        # Should contain bare 'diligent' as the path
        assert "diligent" in content


@patch("shutil.which", return_value="/usr/local/bin/diligent")
def test_uninstall_removes_files(mock_which, tmp_path):
    """Uninstall removes dd_*.md files from target directory."""
    runner = CliRunner()
    # First install
    runner.invoke(cli, ["install", "--path", str(tmp_path)])
    assert len(list(tmp_path.glob("dd_*.md"))) == 6

    # Then uninstall
    result = runner.invoke(
        cli, ["install", "--uninstall", "--path", str(tmp_path)]
    )
    assert result.exit_code == 0
    assert "Removed 6 skill files" in result.output
    assert len(list(tmp_path.glob("dd_*.md"))) == 0


@patch("shutil.which", return_value="/usr/local/bin/diligent")
def test_uninstall_empty_directory(mock_which, tmp_path):
    """Uninstall on directory with no skill files succeeds with message."""
    runner = CliRunner()
    result = runner.invoke(
        cli, ["install", "--uninstall", "--path", str(tmp_path)]
    )
    assert result.exit_code == 0
    assert "No skill files found" in result.output


def test_install_no_target_flag():
    """Install without --claude-code, --antigravity, or --path errors."""
    runner = CliRunner()
    result = runner.invoke(cli, ["install"])
    assert result.exit_code != 0
    assert "Specify --claude-code, --antigravity, or --path" in result.output


def test_install_nonexistent_directory():
    """Install to non-existent directory fails with clear error."""
    runner = CliRunner()
    result = runner.invoke(
        cli, ["install", "--path", "/nonexistent/directory/that/does/not/exist"]
    )
    assert result.exit_code != 0
    assert "does not exist" in result.output


@patch("shutil.which", return_value="/usr/local/bin/diligent")
def test_install_file_count_exactly_six(mock_which, tmp_path):
    """Exactly 6 skill files are written, no more, no less."""
    runner = CliRunner()
    runner.invoke(cli, ["install", "--path", str(tmp_path)])

    files = sorted(f.name for f in tmp_path.glob("dd_*.md"))
    expected = [
        "dd_artifacts.md",
        "dd_questions.md",
        "dd_sources.md",
        "dd_status.md",
        "dd_truth.md",
        "dd_workstreams.md",
    ]
    assert files == expected


@patch("shutil.which", return_value="/usr/local/bin/diligent")
def test_install_json_mode(mock_which, tmp_path):
    """Install with --json outputs structured JSON."""
    import json

    runner = CliRunner()
    result = runner.invoke(
        cli, ["install", "--path", str(tmp_path), "--json"]
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["count"] == 6
    assert data["target_dir"] == str(tmp_path)


@patch("shutil.which", return_value="/usr/local/bin/diligent")
def test_uninstall_json_mode(mock_which, tmp_path):
    """Uninstall with --json outputs structured JSON."""
    import json

    runner = CliRunner()
    # Install first
    runner.invoke(cli, ["install", "--path", str(tmp_path)])
    # Uninstall with json
    result = runner.invoke(
        cli, ["install", "--uninstall", "--path", str(tmp_path), "--json"]
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["removed"] == 6
