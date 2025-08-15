from __future__ import annotations
import subprocess
from pathlib import Path
from typing import Iterable, List, Optional, Set

def _run(cmd: List[str], cwd: str | None = None) -> str:
    res = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
    if res.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{res.stderr}")
    return res.stdout

def changed_paths(base: str, head: str, cwd: str | None = None) -> Set[str]:
    out = _run(["git", "diff", "--name-only", f"{base}..{head}"], cwd)
    return {line.strip() for line in out.splitlines() if line.strip()}

def list_py_files_at_ref(ref: str, roots: Iterable[str], cwd: str | None = None) -> Set[str]:
    # List tracked files, then filter by root and .py extension.
    out = _run(["git", "ls-tree", "-r", "--name-only", ref], cwd)
    paths = []
    roots_norm = [str(Path(r)) for r in roots]
    for line in out.splitlines():
        if not line.endswith(".py"):
            continue
        p = Path(line)
        if any(str(p).startswith(r.rstrip("/") + "/") or str(p) == r for r in roots_norm):
            paths.append(str(p))
    return set(paths)

def read_file_at_ref(ref: str, path: str, cwd: str | None = None) -> Optional[str]:
    try:
        return _run(["git", "show", f"{ref}:{path}"], cwd)
    except RuntimeError:
        return None
