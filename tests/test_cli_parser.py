from argparse import ArgumentParser

from bumpwright.cli import get_parser


def test_get_parser_returns_argument_parser() -> None:
    """Ensure ``get_parser`` creates the CLI parser."""
    parser = get_parser()
    assert isinstance(parser, ArgumentParser)
    assert parser.prog == "bumpwright"
