"""Tests for the migrations analyzer."""

import subprocess
from pathlib import Path

try:  # pragma: no cover - handled when pytest not installed
    import pytest
except ModuleNotFoundError:  # pragma: no cover
    pytest = None  # type: ignore

from bumpwright.analyzers.migrations import analyze_migrations
from bumpwright.config import Migrations


def _run(cmd: list[str], cwd: Path) -> str:
    res = subprocess.run(cmd, cwd=cwd, check=True, stdout=subprocess.PIPE, text=True)
    return res.stdout.strip()


@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    _run(["git", "init"], tmp_path)
    _run(["git", "config", "user.email", "a@b.c"], tmp_path)
    _run(["git", "config", "user.name", "tester"], tmp_path)
    (tmp_path / "README.md").write_text("init")
    _run(["git", "add", "README.md"], tmp_path)
    _run(["git", "commit", "-m", "init"], tmp_path)
    return tmp_path


def _commit_migration(repo: Path, name: str, content: str) -> str:
    mig_dir = repo / "migrations"
    mig_dir.mkdir(exist_ok=True)
    (mig_dir / name).write_text(content)
    _run(["git", "add", str(mig_dir)], repo)
    _run(["git", "commit", "-m", name], repo)
    return _run(["git", "rev-parse", "HEAD"], repo)


def _baseline(repo: Path) -> str:
    return _run(["git", "rev-parse", "HEAD"], repo)


def test_add_nullable_column_minor(repo: Path) -> None:
    """Adding a nullable column should be minor."""

    base = _baseline(repo)
    head = _commit_migration(
        repo,
        "0001_add_col.py",
        """
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column('t', sa.Column('c', sa.Integer(), nullable=True))
""",
    )
    impacts = analyze_migrations(base, head, Migrations(paths=["migrations"]), cwd=repo)
    assert any(i.severity == "minor" for i in impacts)


def test_drop_column_major(repo: Path) -> None:
    """Dropping a column should be major."""

    base = _baseline(repo)
    head = _commit_migration(
        repo,
        "0002_drop_col.py",
        """
from alembic import op

def upgrade():
    op.drop_column('t', 'c')
""",
    )
    impacts = analyze_migrations(base, head, Migrations(paths=["migrations"]), cwd=repo)
    assert any(i.severity == "major" for i in impacts)


def test_add_non_nullable_no_default_major(repo: Path) -> None:
    """Adding a non-nullable column without default is major."""

    base = _baseline(repo)
    head = _commit_migration(
        repo,
        "0003_add_nn.py",
        """
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column('t', sa.Column('d', sa.Integer(), nullable=False))
""",
    )
    impacts = analyze_migrations(base, head, Migrations(paths=["migrations"]), cwd=repo)
    assert any(i.severity == "major" for i in impacts)


def test_create_index_minor(repo: Path) -> None:
    """Creating an index is considered a minor change."""

    base = _baseline(repo)
    head = _commit_migration(
        repo,
        "0004_add_index.py",
        """
from alembic import op

def upgrade():
    op.create_index('ix_t_c', 't', ['c'])
""",
    )
    impacts = analyze_migrations(base, head, Migrations(paths=["migrations"]), cwd=repo)
    assert any(i.severity == "minor" for i in impacts)
