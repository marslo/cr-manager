# -*- coding: utf-8 -*-

"""
Helpers for bash-completion installation.

Public API (imported by crm.py):
  get_completion_text()   → str
  install_completion()    → None  (exits on unrecoverable error)
"""

import importlib.resources as pkg_resources
import os
import platform
import subprocess
import sys
from pathlib import Path

_COMPLETION_FILENAME = "cr-manager"
_PACKAGE_DATA        = "cli.completions"
_BUNDLED_FILE        = "cr-manager.bash"


# ---------------------------------------------------------------------------
# public API
# ---------------------------------------------------------------------------

def get_completion_text() -> str:
    """Return the bundled bash completion script as a string."""
    ref = pkg_resources.files(_PACKAGE_DATA).joinpath(_BUNDLED_FILE)
    return ref.read_text(encoding="utf-8")


def install_completion() -> None:
    """
    Install the bash completion script to the OS-appropriate directory.

    Candidate directories are tried in priority order (user-level first so
    that no root privilege is needed by default).  On macOS, Homebrew's
    bash-completion directory is preferred when Homebrew is available.

    Prints progress to stdout and exits with code 1 on failure.
    """
    text = get_completion_text()

    print( "Detecting bash-completion directory ..." )
    for candidate, label in _candidate_dirs():
        writable = ( candidate.exists() and os.access(candidate, os.W_OK) ) or not candidate.exists()
        if not writable:
            continue
        print( f"  trying {label}: {candidate}" )
        if _try_install( candidate, text ):
            _print_hint( candidate / _COMPLETION_FILENAME )
            return

    print(
        "\nERROR: could not find a writable bash-completion directory.\n"
        "Try one of:\n"
        "  cr-manager --completion | sudo tee /etc/bash_completion.d/cr-manager",
        file=sys.stderr,
    )
    sys.exit(1)


# ---------------------------------------------------------------------------
# internal helpers
# ---------------------------------------------------------------------------

def _brew_prefix() -> Path | None:
    try:
        result = subprocess.run(
            ["brew", "--prefix"],
            capture_output=True, text=True, timeout=5, check=False,
        )
        if result.returncode == 0:
            return Path( result.stdout.strip() )
    except ( FileNotFoundError, subprocess.TimeoutExpired ):
        pass
    return None


def _candidate_dirs() -> list[tuple[Path, str]]:
    """
    Ordered list of (directory, label) candidates.

    macOS  : Homebrew → XDG user → ~/.bash_completion.d → system
    Linux  : XDG user → ~/.bash_completion.d → system
    """
    xdg = Path( os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share") )

    candidates: list[tuple[Path, str]] = []

    if platform.system() == "Darwin":
        brew = _brew_prefix()
        if brew:
            candidates.append(( brew / "etc" / "bash_completion.d", "Homebrew" ))

    candidates += [
        ( xdg / "bash-completion" / "completions", "XDG user" ),
        ( Path.home() / ".bash_completion.d",      "user ~/.bash_completion.d" ),
        ( Path("/usr/share/bash-completion/completions"), "system /usr/share" ),
        ( Path("/etc/bash_completion.d"),                 "system /etc" ),
    ]
    return candidates


def _try_install(directory: Path, text: str) -> bool:
    try:
        directory.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        return False
    dest = directory / _COMPLETION_FILENAME
    try:
        dest.write_text(text, encoding="utf-8")
    except PermissionError:
        return False
    print(f"  installed → {dest}")
    return True


def _print_hint(dest: Path) -> None:
    print(
        f"\nDone!  To activate immediately run:\n"
        f"  source {dest}\n"
        f"Or add the following line to your ~/.bashrc / ~/.bash_profile:\n"
        f"  source {dest}\n"
        f"\nNote: pip uninstall does not remove this file.\n"
        f"To uninstall the completion manually:\n"
        f"  rm {dest}"
    )

# vim:tabstop=4:softtabstop=4:shiftwidth=4:expandtab:filetype=python:
