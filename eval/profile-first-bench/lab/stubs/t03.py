from stubkit import Replace, Replay


def fast_snapshot(item):
    return {"sku": item["sku"], "qty": item["qty"], "price_cents": item["price_cents"],
            "tags": item["tags"][:], "locations": item["locations"].copy(),
            "lots": [lot.copy() for lot in item["lots"]], "version": item["version"]}


def fast_classify(event_type):
    domain, _, action = event_type.partition(".")
    return domain, action


STUBS = {
    "snapshot": Replace("snapshot", fast_snapshot),
    "classify": Replace("classify", fast_classify),
    "load_events": Replay("load_events"),
}
