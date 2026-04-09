"""Tests for atomic_write utility with OneDrive retry and validation."""

import os
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


class TestAtomicWriteBasic:
    """Basic atomic write operations."""

    def test_creates_file_with_correct_content(self, tmp_path):
        from diligent.helpers.io import atomic_write

        target = tmp_path / "test.txt"
        atomic_write(target, "hello world")
        assert target.read_text(encoding="utf-8") == "hello world"

    def test_overwrites_existing_file(self, tmp_path):
        from diligent.helpers.io import atomic_write

        target = tmp_path / "test.txt"
        target.write_text("old content", encoding="utf-8")
        atomic_write(target, "new content")
        assert target.read_text(encoding="utf-8") == "new content"

    def test_creates_parent_directories(self, tmp_path):
        from diligent.helpers.io import atomic_write

        target = tmp_path / "sub" / "deep" / "test.txt"
        atomic_write(target, "nested content")
        assert target.read_text(encoding="utf-8") == "nested content"

    def test_no_temp_files_after_success(self, tmp_path):
        from diligent.helpers.io import atomic_write

        target = tmp_path / "test.txt"
        atomic_write(target, "content")
        tmp_files = list(tmp_path.glob("*.tmp"))
        assert tmp_files == [], f"Temp files left behind: {tmp_files}"


class TestAtomicWriteRetry:
    """PermissionError retry with exponential backoff."""

    def test_retries_on_permission_error(self, tmp_path):
        from diligent.helpers.io import atomic_write, MAX_RETRIES

        target = tmp_path / "test.txt"
        call_count = 0
        original_replace = os.replace

        def mock_replace(src, dst):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise PermissionError("WinError 32")
            return original_replace(src, dst)

        with patch("diligent.helpers.io.os.replace", side_effect=mock_replace), \
             patch("diligent.helpers.io.time.sleep") as mock_sleep:
            atomic_write(target, "retried content")

        assert target.read_text(encoding="utf-8") == "retried content"
        assert call_count == 3
        # Should have slept twice (before retry 2 and 3)
        assert mock_sleep.call_count == 2

    def test_raises_after_max_retries(self, tmp_path):
        from diligent.helpers.io import atomic_write, MAX_RETRIES

        target = tmp_path / "test.txt"

        def always_fail(src, dst):
            raise PermissionError("WinError 32")

        with patch("diligent.helpers.io.os.replace", side_effect=always_fail), \
             patch("diligent.helpers.io.time.sleep"):
            with pytest.raises(PermissionError):
                atomic_write(target, "will fail")

    def test_exponential_backoff_delays(self, tmp_path):
        from diligent.helpers.io import atomic_write, BASE_DELAY

        target = tmp_path / "test.txt"
        call_count = 0
        original_replace = os.replace

        def mock_replace(src, dst):
            nonlocal call_count
            call_count += 1
            if call_count < 4:
                raise PermissionError("WinError 32")
            return original_replace(src, dst)

        with patch("diligent.helpers.io.os.replace", side_effect=mock_replace), \
             patch("diligent.helpers.io.time.sleep") as mock_sleep:
            atomic_write(target, "content")

        # Verify exponential backoff: 0.1, 0.2, 0.4
        delays = [call.args[0] for call in mock_sleep.call_args_list]
        assert delays[0] == pytest.approx(BASE_DELAY * 1)  # 0.1
        assert delays[1] == pytest.approx(BASE_DELAY * 2)  # 0.2
        assert delays[2] == pytest.approx(BASE_DELAY * 4)  # 0.4

    def test_no_temp_files_after_max_retries(self, tmp_path):
        from diligent.helpers.io import atomic_write

        target = tmp_path / "test.txt"

        def always_fail(src, dst):
            raise PermissionError("WinError 32")

        with patch("diligent.helpers.io.os.replace", side_effect=always_fail), \
             patch("diligent.helpers.io.time.sleep"):
            with pytest.raises(PermissionError):
                atomic_write(target, "will fail")

        tmp_files = list(tmp_path.glob("*.tmp"))
        assert tmp_files == [], f"Temp files left behind: {tmp_files}"


class TestAtomicWriteCleanup:
    """Temp file cleanup on failure."""

    def test_cleans_up_on_write_failure(self, tmp_path):
        from diligent.helpers.io import atomic_write

        target = tmp_path / "test.txt"

        # Make the directory read-only to cause write failure... but that's
        # tricky cross-platform. Instead mock fdopen to raise.
        with patch("diligent.helpers.io.os.fdopen", side_effect=IOError("disk full")):
            with pytest.raises(IOError):
                atomic_write(target, "content")

        tmp_files = list(tmp_path.glob("*.tmp"))
        assert tmp_files == [], f"Temp files left behind: {tmp_files}"

    def test_cleans_up_on_unexpected_error(self, tmp_path):
        from diligent.helpers.io import atomic_write

        target = tmp_path / "test.txt"

        def raise_runtime(src, dst):
            raise RuntimeError("unexpected")

        with patch("diligent.helpers.io.os.replace", side_effect=raise_runtime):
            with pytest.raises(RuntimeError):
                atomic_write(target, "content")

        tmp_files = list(tmp_path.glob("*.tmp"))
        assert tmp_files == [], f"Temp files left behind: {tmp_files}"


class TestAtomicWriteValidation:
    """Validation function gate."""

    def test_no_validation_writes_normally(self, tmp_path):
        from diligent.helpers.io import atomic_write

        target = tmp_path / "test.txt"
        atomic_write(target, "content", validate_fn=None)
        assert target.read_text(encoding="utf-8") == "content"

    def test_validation_true_writes_normally(self, tmp_path):
        from diligent.helpers.io import atomic_write

        target = tmp_path / "test.txt"
        atomic_write(target, "content", validate_fn=lambda c: True)
        assert target.read_text(encoding="utf-8") == "content"

    def test_validation_false_raises_value_error(self, tmp_path):
        from diligent.helpers.io import atomic_write

        target = tmp_path / "test.txt"
        target.write_text("prior content", encoding="utf-8")

        with pytest.raises(ValueError, match="Validation failed"):
            atomic_write(target, "bad content", validate_fn=lambda c: False)

    def test_validation_false_preserves_prior_content(self, tmp_path):
        from diligent.helpers.io import atomic_write

        target = tmp_path / "test.txt"
        target.write_text("prior content", encoding="utf-8")

        with pytest.raises(ValueError):
            atomic_write(target, "bad content", validate_fn=lambda c: False)

        assert target.read_text(encoding="utf-8") == "prior content"

    def test_validation_false_no_file_created_if_none_existed(self, tmp_path):
        from diligent.helpers.io import atomic_write

        target = tmp_path / "test.txt"
        assert not target.exists()

        with pytest.raises(ValueError):
            atomic_write(target, "bad content", validate_fn=lambda c: False)

        assert not target.exists()

    def test_no_temp_files_after_validation_failure(self, tmp_path):
        from diligent.helpers.io import atomic_write

        target = tmp_path / "test.txt"

        with pytest.raises(ValueError):
            atomic_write(target, "bad", validate_fn=lambda c: False)

        tmp_files = list(tmp_path.glob("*.tmp"))
        assert tmp_files == [], f"Temp files left behind: {tmp_files}"
