"""Replays a day of warehouse stock events and reports peak stock and the audit trail.

usage: python3 app.py events.jsonl
"""
import copy
import json
import re
import sys
from collections import deque

EVENT_TYPE = re.compile(r"^(?P<domain>[a-z]+)\.(?P<action>[a-z]+)$")
TRAIL_KEEP = 2000  # the in-memory audit trail keeps the latest snapshots


def load_events(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def classify(event_type):
    m = EVENT_TYPE.match(event_type)
    if m is None:
        raise ValueError(f"bad event type {event_type!r}")
    return m.group("domain"), m.group("action")


def new_item(sku):
    return {"sku": sku, "qty": 0, "price_cents": 0, "tags": [], "locations": {}, "lots": [],
            "version": 0}


def apply(item, domain, action, ev):
    if (domain, action) == ("stock", "received"):
        item["qty"] += ev["qty"]
        item["lots"].append({"lot": ev["lot"], "qty": ev["qty"], "loc": ev["loc"]})
        item["locations"][ev["loc"]] = item["locations"].get(ev["loc"], 0) + ev["qty"]
    elif (domain, action) == ("stock", "picked"):
        want = min(ev["qty"], item["qty"])
        item["qty"] -= want
        while want and item["lots"]:
            lot = item["lots"][0]
            take = min(want, lot["qty"])
            lot["qty"] -= take
            want -= take
            item["locations"][lot["loc"]] -= take
            if not item["locations"][lot["loc"]]:
                del item["locations"][lot["loc"]]
            if not lot["qty"]:
                item["lots"].pop(0)
    elif (domain, action) == ("price", "changed"):
        item["price_cents"] = ev["price_cents"]
    elif (domain, action) == ("tag", "added"):
        if ev["tag"] not in item["tags"]:
            item["tags"].append(ev["tag"])
    item["version"] += 1


def snapshot(item):
    """Frozen copy of an item for the audit trail."""
    return copy.deepcopy(item)


def main(argv):
    events = load_events(argv[0])
    items, trail = {}, deque(maxlen=TRAIL_KEEP)
    peak = {}
    deep_lots = checksum = 0
    for ev in events:
        domain, action = classify(ev["type"])
        item = items.setdefault(ev["sku"], new_item(ev["sku"]))
        apply(item, domain, action, ev)
        snap = snapshot(item)
        trail.append(snap)
        peak[snap["sku"]] = max(peak.get(snap["sku"], 0), snap["qty"])
        deep_lots += len(snap["lots"]) > 3
        checksum = (checksum * 31 + snap["version"] * snap["qty"]
                    + sum(lot["qty"] for lot in snap["lots"]) + len(snap["tags"])) % 1_000_000_007

    held = sum(lot["qty"] for snap in trail for lot in snap["lots"])
    print(f"events: {len(events)}  items: {len(items)}  snapshots with >3 lots: {deep_lots}")
    print(f"audit checksum: {checksum}  trail: last {len(trail)} snapshots, {held} units in their lots")
    for sku, qty in sorted(peak.items(), key=lambda kv: (-kv[1], kv[0]))[:10]:
        final = items[sku]
        print(f"{sku}  peak {qty:5d}  now {final['qty']:5d}  lots {len(final['lots'])}  "
              f"tags {','.join(final['tags'])}")


if __name__ == "__main__":
    main(sys.argv[1:])
