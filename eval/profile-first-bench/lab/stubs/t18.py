from collections import deque

from stubkit import ReplayAfter, ReplayLazy

STUBS = {
    "find_overlaps": ReplayAfter("find_overlaps", before=lambda rows: deque(rows, maxlen=0)),
    "open_sheet": ReplayLazy("open_sheet", project=tuple, rebuild=tuple),
    "rota_grid": ReplayAfter("rota_grid"),
}
