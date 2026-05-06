from __future__ import annotations

import os
from pathlib import Path


def project_root(start: str | Path | None = None) -> Path:
    """Return the explicit project root.

    The skill code is global under ~/.codex/skills. The project root is simply
    the user-provided path or the current working directory.
    """
    return Path(start or os.getcwd()).resolve()


def codex_skills_root() -> Path:
    codex_home = os.environ.get("CODEX_HOME")
    if codex_home:
        return Path(codex_home).expanduser().resolve() / "skills"
    return Path.home().resolve() / ".codex" / "skills"


def skill_root(skill_name: str) -> Path:
    candidate = codex_skills_root() / skill_name
    if candidate.exists():
        return candidate
    raise FileNotFoundError(f"Cannot locate global Codex skill '{skill_name}': {candidate}")


def skill_script(skill_name: str, relative_path: str, root: str | Path | None = None) -> Path:
    script = skill_root(skill_name) / relative_path
    if not script.exists():
        raise FileNotFoundError(f"Missing script for {skill_name}: {script}")
    return script


def ensure_project_dirs(root: str | Path | None = None) -> Path:
    base = project_root(root)
    for name in ("problem_files", "crawled_data", "paper_output"):
        (base / name).mkdir(parents=True, exist_ok=True)
    return base
