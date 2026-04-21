"""Logger console avec horodatage et niveaux colorés (sans dépendances externes)."""

import sys
from datetime import datetime

# Codes ANSI
_RESET = "\033[0m"
_BOLD = "\033[1m"
_COLORS = {
    "cyan": "\033[96m",
    "green": "\033[92m",
    "yellow": "\033[93m",
    "red": "\033[91m",
    "blue": "\033[94m",
    "magenta": "\033[95m",
    "white": "\033[97m",
    "gray": "\033[90m",
}

_USE_COLOR = sys.stdout.isatty()


def _colorize(text: str, color: str, bold: bool = False) -> str:
    if not _USE_COLOR:
        return text
    prefix = (_BOLD if bold else "") + _COLORS.get(color, "")
    return f"{prefix}{text}{_RESET}"


def _timestamp() -> str:
    return datetime.now().strftime("%H:%M:%S")


def info(msg: str) -> None:
    ts = _colorize(_timestamp(), "gray")
    tag = _colorize("INFO ", "cyan", bold=True)
    print(f"{ts} {tag} {msg}")


def success(msg: str) -> None:
    ts = _colorize(_timestamp(), "gray")
    tag = _colorize("✓ OK  ", "green", bold=True)
    print(f"{ts} {tag} {msg}")


def warn(msg: str) -> None:
    ts = _colorize(_timestamp(), "gray")
    tag = _colorize("WARN ", "yellow", bold=True)
    print(f"{ts} {tag} {msg}")


def error(msg: str) -> None:
    ts = _colorize(_timestamp(), "gray")
    tag = _colorize("ERR  ", "red", bold=True)
    print(f"{ts} {tag} {msg}", file=sys.stderr)


def agent(name: str, msg: str) -> None:
    ts = _colorize(_timestamp(), "gray")
    tag = _colorize(f"[{name}]", "magenta", bold=True)
    print(f"{ts} {tag} {msg}")


def supervisor(msg: str) -> None:
    ts = _colorize(_timestamp(), "gray")
    tag = _colorize("[SUPERVISEUR]", "blue", bold=True)
    print(f"{ts} {tag} {msg}")


def divider(title: str = "") -> None:
    line = "─" * 60
    if title:
        pad = (58 - len(title)) // 2
        display = f"{'─' * pad} {title} {'─' * pad}"
    else:
        display = line
    print(_colorize(display, "gray"))


def section(title: str) -> None:
    print()
    divider(title)
    print()
