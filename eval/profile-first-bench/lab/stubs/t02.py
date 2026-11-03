from stubkit import Replay, ReplayWrite

STUBS = {
    "write_report": ReplayWrite("write_report"),
    "parse_duration": Replay("parse_duration"),
    "load_orders": Replay("load_orders"),
}
