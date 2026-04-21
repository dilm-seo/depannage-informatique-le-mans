"""
Logger console avec horodatage, niveaux colorés et affichage de la hiérarchie
des agents (Superviseur → Chef d'équipe → Travailleur).
"""

import sys
from datetime import datetime

# ─── Codes ANSI ───────────────────────────────────────────────────────────────
_RESET = "\033[0m"
_BOLD  = "\033[1m"
_COLORS = {
    "cyan":    "\033[96m",
    "green":   "\033[92m",
    "yellow":  "\033[93m",
    "red":     "\033[91m",
    "blue":    "\033[94m",
    "magenta": "\033[95m",
    "white":   "\033[97m",
    "gray":    "\033[90m",
    "orange":  "\033[38;5;214m",
    "teal":    "\033[38;5;43m",
}

_USE_COLOR = sys.stdout.isatty()


def _c(text: str, color: str, bold: bool = False) -> str:
    if not _USE_COLOR:
        return text
    prefix = (_BOLD if bold else "") + _COLORS.get(color, "")
    return f"{prefix}{text}{_RESET}"


def _ts() -> str:
    return datetime.now().strftime("%H:%M:%S")


# ─── Niveaux génériques ───────────────────────────────────────────────────────

def info(msg: str) -> None:
    print(f"{_c(_ts(), 'gray')} {_c('INFO ', 'cyan', bold=True)} {msg}")


def success(msg: str) -> None:
    print(f"{_c(_ts(), 'gray')} {_c('✓ OK  ', 'green', bold=True)} {msg}")


def warn(msg: str) -> None:
    print(f"{_c(_ts(), 'gray')} {_c('WARN ', 'yellow', bold=True)} {msg}")


def error(msg: str) -> None:
    print(f"{_c(_ts(), 'gray')} {_c('ERR  ', 'red', bold=True)} {msg}", file=sys.stderr)


# ─── Niveaux hiérarchie agents ────────────────────────────────────────────────

def supervisor(msg: str) -> None:
    """Superviseur principal (Opus 4.7)."""
    print(f"{_c(_ts(), 'gray')} {_c('◆ SUPERVISEUR', 'blue', bold=True)}  {msg}")


def supervisor_delegue(agent: str, directive_preview: str) -> None:
    """Le superviseur envoie une directive à un chef."""
    preview = directive_preview[:70] + "…" if len(directive_preview) > 70 else directive_preview
    print(
        f"{_c(_ts(), 'gray')} {_c('◆ SUPERVISEUR', 'blue', bold=True)}"
        f"  → DÉLÈGUE à {_c(agent, 'orange', bold=True)} : {preview}"
    )


def supervisor_recu(agent: str, confidence: int, recrutes: str) -> None:
    """Le superviseur reçoit un rapport d'un chef."""
    conf_color = "green" if confidence >= 80 else ("yellow" if confidence >= 60 else "red")
    print(
        f"{_c(_ts(), 'gray')} {_c('◆ SUPERVISEUR', 'blue', bold=True)}"
        f"  ← RAPPORT {_c(agent, 'orange', bold=True)}"
        f"  conf={_c(f'{confidence}%', conf_color, bold=True)}"
        f"  agents=[{recrutes}]"
    )


def supervisor_feedback(agent: str, feedback_preview: str) -> None:
    """Le superviseur envoie un feedback de révision."""
    preview = feedback_preview[:60] + "…" if len(feedback_preview) > 60 else feedback_preview
    print(
        f"{_c(_ts(), 'gray')} {_c('◆ SUPERVISEUR', 'blue', bold=True)}"
        f"  ↺ RÉVISION demandée à {_c(agent, 'orange', bold=True)} : {preview}"
    )


def chef(nom: str, msg: str) -> None:
    """Chef d'équipe (Haiku 4.5)."""
    print(f"{_c(_ts(), 'gray')}   {_c(f'▸ CHEF {nom}', 'orange', bold=True)}  {msg}")


def chef_recrute(chef_nom: str, worker_nom: str, specialite: str) -> None:
    """Un chef recrute un agent travailleur."""
    print(
        f"{_c(_ts(), 'gray')}   {_c(f'▸ CHEF {chef_nom}', 'orange', bold=True)}"
        f"  → RECRUTE {_c(worker_nom, 'teal', bold=True)} ({specialite})"
    )


def worker(tag: str, msg: str) -> None:
    """Agent travailleur spécialisé (Haiku 4.5, nœud feuille)."""
    print(f"{_c(_ts(), 'gray')}      {_c(f'· {tag}', 'teal', bold=True)}  {msg}")


# ─── Séparateurs visuels ──────────────────────────────────────────────────────

def divider(title: str = "") -> None:
    width = 64
    if title:
        pad = max(0, (width - len(title) - 2)) // 2
        line = f"{'─' * pad} {title} {'─' * pad}"
    else:
        line = "─" * width
    print(_c(line, "gray"))


def section(title: str) -> None:
    print()
    divider(title)
    print()
