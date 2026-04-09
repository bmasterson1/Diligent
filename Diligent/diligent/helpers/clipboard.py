"""Platform clipboard copy function.

Wraps platform-native clipboard commands (clip.exe, pbcopy, wl-copy,
xclip) with subprocess. Never raises exceptions; returns bool.
"""

import platform
import subprocess


def copy_to_clipboard(text: str) -> bool:
    """Copy text to system clipboard. Returns True on success, False on failure. Never raises."""
    try:
        system = platform.system()
        if system == "Windows":
            cmd = ["clip.exe"]
        elif system == "Darwin":
            cmd = ["pbcopy"]
        else:
            # Linux: try wl-copy first, fall back to xclip
            try:
                proc = subprocess.run(
                    ["wl-copy"],
                    input=text,
                    text=True,
                    timeout=5,
                    capture_output=True,
                )
                return proc.returncode == 0
            except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
                cmd = ["xclip", "-selection", "clipboard"]

        proc = subprocess.run(
            cmd,
            input=text,
            text=True,
            timeout=5,
            capture_output=True,
        )
        return proc.returncode == 0
    except Exception:
        return False
