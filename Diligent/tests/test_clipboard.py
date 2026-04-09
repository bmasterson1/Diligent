"""Tests for clipboard helper.

Unit tests with mocked subprocess to verify platform dispatch,
success/failure return values, and exception safety.
"""

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from diligent.helpers.clipboard import copy_to_clipboard


class TestCopyToClipboardSuccess:
    """Tests for successful clipboard copy paths."""

    @patch("diligent.helpers.clipboard.platform")
    @patch("diligent.helpers.clipboard.subprocess")
    def test_returns_true_on_returncode_zero(self, mock_subprocess, mock_platform):
        """copy_to_clipboard returns True when subprocess exits 0."""
        mock_platform.system.return_value = "Windows"
        proc = MagicMock()
        proc.returncode = 0
        mock_subprocess.run.return_value = proc
        mock_subprocess.TimeoutExpired = subprocess.TimeoutExpired

        assert copy_to_clipboard("hello") is True

    @patch("diligent.helpers.clipboard.platform")
    @patch("diligent.helpers.clipboard.subprocess")
    def test_windows_uses_clip_exe(self, mock_subprocess, mock_platform):
        """Windows dispatches to clip.exe."""
        mock_platform.system.return_value = "Windows"
        proc = MagicMock()
        proc.returncode = 0
        mock_subprocess.run.return_value = proc
        mock_subprocess.TimeoutExpired = subprocess.TimeoutExpired

        copy_to_clipboard("test text")
        args = mock_subprocess.run.call_args
        assert args[0][0][0] == "clip.exe"

    @patch("diligent.helpers.clipboard.platform")
    @patch("diligent.helpers.clipboard.subprocess")
    def test_macos_uses_pbcopy(self, mock_subprocess, mock_platform):
        """macOS dispatches to pbcopy."""
        mock_platform.system.return_value = "Darwin"
        proc = MagicMock()
        proc.returncode = 0
        mock_subprocess.run.return_value = proc
        mock_subprocess.TimeoutExpired = subprocess.TimeoutExpired

        copy_to_clipboard("test text")
        args = mock_subprocess.run.call_args
        assert args[0][0][0] == "pbcopy"


class TestCopyToClipboardFailure:
    """Tests for failure paths that should return False."""

    @patch("diligent.helpers.clipboard.platform")
    @patch("diligent.helpers.clipboard.subprocess")
    def test_returns_false_on_nonzero_returncode(self, mock_subprocess, mock_platform):
        """copy_to_clipboard returns False when subprocess exits non-zero."""
        mock_platform.system.return_value = "Windows"
        proc = MagicMock()
        proc.returncode = 1
        mock_subprocess.run.return_value = proc
        mock_subprocess.TimeoutExpired = subprocess.TimeoutExpired

        assert copy_to_clipboard("hello") is False

    @patch("diligent.helpers.clipboard.platform")
    @patch("diligent.helpers.clipboard.subprocess")
    def test_returns_false_on_file_not_found(self, mock_subprocess, mock_platform):
        """copy_to_clipboard returns False when clipboard command not found."""
        mock_platform.system.return_value = "Windows"
        mock_subprocess.run.side_effect = FileNotFoundError("clip.exe not found")
        mock_subprocess.TimeoutExpired = subprocess.TimeoutExpired

        assert copy_to_clipboard("hello") is False

    @patch("diligent.helpers.clipboard.platform")
    @patch("diligent.helpers.clipboard.subprocess")
    def test_returns_false_on_timeout(self, mock_subprocess, mock_platform):
        """copy_to_clipboard returns False on subprocess timeout."""
        mock_platform.system.return_value = "Windows"
        mock_subprocess.run.side_effect = subprocess.TimeoutExpired("clip.exe", 5)
        mock_subprocess.TimeoutExpired = subprocess.TimeoutExpired

        assert copy_to_clipboard("hello") is False

    @patch("diligent.helpers.clipboard.platform")
    @patch("diligent.helpers.clipboard.subprocess")
    def test_returns_false_on_os_error(self, mock_subprocess, mock_platform):
        """copy_to_clipboard returns False on OSError."""
        mock_platform.system.return_value = "Windows"
        mock_subprocess.run.side_effect = OSError("permission denied")
        mock_subprocess.TimeoutExpired = subprocess.TimeoutExpired

        assert copy_to_clipboard("hello") is False

    @patch("diligent.helpers.clipboard.platform")
    @patch("diligent.helpers.clipboard.subprocess")
    def test_never_raises_exceptions(self, mock_subprocess, mock_platform):
        """copy_to_clipboard catches all exceptions and returns bool."""
        mock_platform.system.return_value = "Windows"
        mock_subprocess.run.side_effect = RuntimeError("unexpected")
        mock_subprocess.TimeoutExpired = subprocess.TimeoutExpired

        # Should not raise, should return False
        result = copy_to_clipboard("hello")
        assert result is False
