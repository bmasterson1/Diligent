"""Atomic file write utility with OneDrive retry.

Writes to a temp file in the same directory, fsyncs, then uses
os.replace for an atomic rename. Retries on PermissionError with
exponential backoff to handle OneDrive sync locks (WinError 32).

No network imports. No external dependencies. Stdlib only.
"""

import os
import tempfile
import time
from pathlib import Path
from typing import Callable, Optional

MAX_RETRIES = 5
BASE_DELAY = 0.1  # 100ms


def atomic_write(
    target: Path, content: str, validate_fn: Optional[Callable] = None
) -> None:
    """Write content to target atomically with OneDrive retry.

    Args:
        target: Final file path.
        content: String content to write.
        validate_fn: Optional callable(content) -> bool. If provided,
            content is validated before writing. On failure, prior
            state is preserved and ValueError is raised.

    Raises:
        ValueError: If validate_fn returns False.
        PermissionError: If os.replace fails after MAX_RETRIES attempts.
    """
    if validate_fn is not None and not validate_fn(content):
        raise ValueError(f"Validation failed for {target}; prior state preserved.")

    parent = target.parent
    parent.mkdir(parents=True, exist_ok=True)

    # Write to temp file in same directory (same filesystem for os.replace)
    fd, tmp_path = tempfile.mkstemp(dir=str(parent), suffix=".tmp")
    fd_closed = False
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            fd_closed = True  # fdopen takes ownership of fd
            f.write(content)
            f.flush()
            os.fsync(f.fileno())

        # Retry os.replace for OneDrive file locks
        for attempt in range(MAX_RETRIES):
            try:
                os.replace(tmp_path, str(target))
                return
            except PermissionError:
                if attempt == MAX_RETRIES - 1:
                    raise
                delay = BASE_DELAY * (2 ** attempt)
                time.sleep(delay)
    except BaseException:
        # Close the raw fd if fdopen never took ownership
        if not fd_closed:
            try:
                os.close(fd)
            except OSError:
                pass
        # Clean up temp file on any failure
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise
