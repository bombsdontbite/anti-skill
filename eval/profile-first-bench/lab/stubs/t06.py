import logging

from stubkit import Hook, Replay

STUBS = {
    # engine.log is a debug log, not output: with DEBUG disabled, stdout is unchanged.
    "logging": Hook(lambda: logging.disable(logging.DEBUG)),
    "make_key": Replay("make_key"),
    "apply_rules": Replay("apply_rules"),
}
