"""Nightly sales report: per-customer totals and order history, as JSON on stdout.

usage: python3 app.py orders.csv > report.json
"""
import csv
import json
import sys
from datetime import datetime
from decimal import Decimal

UNITS = {"d": 86400, "h": 3600, "m": 60}


def parse_duration(text):
    """Time to ship, such as '2d4h' or '45m', in seconds."""
    total = num = 0
    i = 0
    while i < len(text):
        ch = text[i]
        if "0" <= ch <= "9":
            num = num * 10 + (ord(ch) - 48)
        elif ch in UNITS:
            total += num * UNITS[ch]
            num = 0
        else:
            raise ValueError(f"bad duration {text!r}")
        i += 1
    return total


def load_orders(path):
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append((r["order_id"], r["customer"], r["sku"], int(r["qty"]), r["unit_price"],
                         r["ts"], parse_duration(r["ship_time"])))
    return rows


def summarise(rows):
    customers = {}
    for order_id, customer, sku, qty, price, ts, ship_secs in rows:
        c = customers.setdefault(customer, {"orders": [], "total": Decimal("0"), "units": 0})
        unit_price = Decimal(price)
        at = datetime.fromisoformat(ts)
        c["orders"].append({"id": order_id, "sku": sku, "qty": qty, "unit_price": unit_price,
                            "line_total": unit_price * qty, "at": at, "ship_secs": ship_secs})
        c["total"] += unit_price * qty
        c["units"] += qty
    for c in customers.values():
        c["orders"].sort(key=lambda o: (o["at"], o["id"]))
        c["first_order"] = c["orders"][0]["at"]
        c["last_order"] = c["orders"][-1]["at"]
        c["mean_ship_secs"] = sum(o["ship_secs"] for o in c["orders"]) // len(c["orders"])
    grand = sum((c["total"] for c in customers.values()), Decimal("0"))
    return {"customers": customers, "grand_total": grand, "order_count": len(rows)}


def _encode(obj):
    if isinstance(obj, Decimal):
        return str(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"cannot encode {type(obj).__name__}")


def write_report(report, out):
    json.dump(report, out, indent=2, sort_keys=True, default=_encode)
    out.write("\n")


def main(argv):
    rows = load_orders(argv[0])
    report = summarise(rows)
    write_report(report, sys.stdout)


if __name__ == "__main__":
    main(sys.argv[1:])
