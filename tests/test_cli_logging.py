import logging
from typing import List

from bumpwright.cli import main


def _clear_handlers() -> tuple[List[logging.Handler], int]:
    """Remove existing root handlers and return their backup and level."""
    root = logging.getLogger()
    handlers = root.handlers[:]
    level = root.level
    for handler in handlers:
        root.removeHandler(handler)
    return handlers, level


def _restore_handlers(handlers: List[logging.Handler], level: int) -> None:
    """Restore root logger handlers and level."""
    root = logging.getLogger()
    for handler in list(root.handlers):
        root.removeHandler(handler)
    for handler in handlers:
        root.addHandler(handler)
    root.setLevel(level)


def test_main_configures_logging_once() -> None:
    """Ensure the CLI configures logging a single time."""
    handlers, level = _clear_handlers()
    try:
        assert logging.getLogger().handlers == []
        main([])
        root = logging.getLogger()
        assert len(root.handlers) == 1
        first_handler = root.handlers[0]
        main([])
        root = logging.getLogger()
        assert len(root.handlers) == 1
        assert root.handlers[0] is first_handler
    finally:
        _restore_handlers(handlers, level)


def test_main_respects_user_logging_config() -> None:
    """Verify user-defined logging configuration is retained."""
    handlers, level = _clear_handlers()
    try:
        logging.basicConfig(level=logging.DEBUG)
        root = logging.getLogger()
        assert root.level == logging.DEBUG
        first_handler = root.handlers[0]
        main([])
        root = logging.getLogger()
        assert root.level == logging.DEBUG
        assert root.handlers[0] is first_handler
    finally:
        _restore_handlers(handlers, level)
