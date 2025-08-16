"""Tests for the migrations analyser plugin."""

import os
import subprocess
from pathlib import Path

try:  # pragma: no cover - handled when pytest not installed
    import pytest
except ModuleNotFoundError:  # pragma: no cover
    pytest = None  # type: ignore

from bumpwright.analysers import load_enabled
from bumpwright.compare import Impact
from bumpwright.config import Config, Migrations


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


def _commit_migrations(repo: Path, files: dict[str, str]) -> str:
    """Commit multiple migration files at once.

    Args:
        repo: Repository root path.
        files: Mapping of file names to their contents.

    Returns:
        The commit hash after committing the migrations.
    """

    mig_dir = repo / "migrations"
    mig_dir.mkdir(exist_ok=True)
    for name, content in files.items():
        (mig_dir / name).write_text(content)
    _run(["git", "add", str(mig_dir)], repo)
    _run(["git", "commit", "-m", "batch"], repo)
    return _run(["git", "rev-parse", "HEAD"], repo)


def _baseline(repo: Path) -> str:
    """Return the current HEAD commit hash."""

    return _run(["git", "rev-parse", "HEAD"], repo)


def _analyze(repo: Path, base: str, head: str) -> list[Impact]:
    """Run the migrations analyser and return impacts.

    Args:
        repo: Repository root path.
        base: Base git reference.
        head: Head git reference.

    Returns:
        List of detected impacts.
    """

    cfg = Config(migrations=Migrations(paths=["migrations"]))
    cfg.analysers.enabled.add("migrations")
    analyser = load_enabled(cfg)[0]
    old_cwd = os.getcwd()
    os.chdir(repo)
    try:
        return analyser.compare(analyser.collect(base), analyser.collect(head))
    finally:
        os.chdir(old_cwd)


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
    impacts = _analyze(repo, base, head)
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
    impacts = _analyze(repo, base, head)
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
    impacts = _analyze(repo, base, head)
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
    impacts = _analyze(repo, base, head)
    assert any(i.severity == "minor" for i in impacts)


def test_drop_table_major(repo: Path) -> None:
    """Dropping a table should be major."""

    base = _baseline(repo)
    head = _commit_migration(
        repo,
        "0005_drop_table.py",
        """
from alembic import op

def upgrade():
    op.drop_table('t')
""",
    )
    impacts = _analyze(repo, base, head)
    assert any(i.severity == "major" for i in impacts)


def test_rename_column_major(repo: Path) -> None:
    """Renaming a column should be major."""

    base = _baseline(repo)
    head = _commit_migration(
        repo,
        "0006_rename_col.py",
        """
from alembic import op

def upgrade():
    op.rename_column('t', 'c', 'd')
""",
    )
    impacts = _analyze(repo, base, head)
    assert any(i.severity == "major" for i in impacts)


def test_alter_column_nullable_minor(repo: Path) -> None:
    """Making a column nullable should be minor."""

    base = _baseline(repo)
    head = _commit_migration(
        repo,
        "0007_alter_col_nullable.py",
        """
from alembic import op

def upgrade():
    op.alter_column('t', 'c', nullable=True)
""",
    )
    impacts = _analyze(repo, base, head)
    assert any(i.severity == "minor" for i in impacts)


def test_alter_column_non_nullable_major(repo: Path) -> None:
    """Making a column non-nullable should be major."""

    base = _baseline(repo)
    head = _commit_migration(
        repo,
        "0008_alter_col_nn.py",
        """
from alembic import op

def upgrade():
    op.alter_column('t', 'c', nullable=False)
""",
    )
    impacts = _analyze(repo, base, head)
    assert any(i.severity == "major" for i in impacts)


def test_drop_index_minor(repo: Path) -> None:
    """Dropping an index should be minor."""

    base = _baseline(repo)
    head = _commit_migration(
        repo,
        "0009_drop_index.py",
        """
from alembic import op

def upgrade():
    op.drop_index('ix_t_c', 't')
""",
    )
    impacts = _analyze(repo, base, head)
    assert any(i.severity == "minor" for i in impacts)


def test_multiple_migrations_single_commit(repo: Path) -> None:
    """Processing multiple migration files in one commit works."""

    base = _baseline(repo)
    head = _commit_migrations(
        repo,
        {
            "0005_add_col.py": """
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column('t', sa.Column('e', sa.Integer(), nullable=True))
""",
            "0006_drop_col.py": """
from alembic import op

def upgrade():
    op.drop_column('t', 'e')
""",
        },
    )
    impacts = _analyze(repo, base, head)
    severities = {i.severity for i in impacts}
    assert {"minor", "major"}.issubset(severities)
