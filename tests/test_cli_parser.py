from argparse import ArgumentParser

from bumpwright.cli import get_parser


def test_get_parser_returns_argument_parser() -> None:
    """Ensure ``get_parser`` creates the CLI parser."""
    parser = get_parser()
    assert isinstance(parser, ArgumentParser)
    assert parser.prog == "bumpwright"


def test_parser_includes_ref_and_analyser_options() -> None:
    """Verify reference and analyser toggling options remain available."""

    parser = get_parser()
    args = parser.parse_args(
        [
            "bump",
            "--base",
            "A",
            "--head",
            "B",
            "--enable-analyser",
            "cli",
            "--disable-analyser",
            "db",
        ]
    )
    assert args.base == "A"
    assert args.head == "B"
    assert args.enable_analyser == ["cli"]
    assert args.disable_analyser == ["db"]
