from argparse import ArgumentParser

from bumpwright.cli import get_parser


def test_get_parser_returns_argument_parser() -> None:
    """Ensure ``get_parser`` creates the CLI parser."""
    parser = get_parser()
    assert isinstance(parser, ArgumentParser)
    assert parser.prog == "bumpwright"


def test_parser_includes_ref_and_analyzer_options() -> None:
    """Verify reference and analyzer toggling options remain available."""

    parser = get_parser()
    args = parser.parse_args(
        [
            "bump",
            "--base",
            "A",
            "--head",
            "B",
            "--enable-analyzer",
            "cli",
            "--disable-analyzer",
            "db",
        ]
    )
    assert args.base == "A"
    assert args.head == "B"
    assert args.enable_analyzer == ["cli"]
    assert args.disable_analyzer == ["db"]
