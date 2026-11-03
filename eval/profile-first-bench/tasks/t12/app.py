"""Replays a day of checkout events, prints basket metrics and the latest audit entries.

usage: python3 app.py events.tsv
"""
import sys

TIERS = [(25, 10), (10, 6), (5, 3), (1, 0)]  # (minimum quantity, % off), best first
OFF = [next(o for q, o in TIERS if n >= q) if n else 0 for n in range(26)]


class AuditTrail:
    """Every priced basket seen today, kept for the end-of-day audit."""

    def __init__(self):
        self.entries = []

    def add(self, session, priced):
        self.entries.append((session, priced))

    def __len__(self):
        return len(self.entries)

    def latest(self, n):
        return self.entries[-n:]


def load_events(path):
    """session, op, sku, qty, cents per line; remove lines leave the last two empty."""
    with open(path, encoding="utf-8") as f:
        return [line.rstrip("\n").split("\t") for line in f]


def apply(baskets, ev):
    session, op, sku, qty, cents = ev
    basket = baskets.setdefault(session, {})
    if op == "add":
        basket[sku] = (int(qty), int(cents))
    elif op == "remove":
        basket.pop(sku, None)
    return basket


def price_basket(basket):
    """Each line at the best volume tier its quantity reaches."""
    priced = []
    for sku, (qty, cents) in basket.items():
        off = OFF[min(qty, 25)]
        priced.append({"sku": sku, "qty": qty, "net": qty * cents * (100 - off) // 100})
    return priced


def tier_names():
    names = {}
    for a in range(1, 26):
        for b in range(1, 26):
            names[a, b] = f"{a}x{b}"
    return names


def main(argv):
    events = load_events(argv[0])
    names = tier_names()
    trail, baskets, peak = AuditTrail(), {}, 0
    for ev in events:
        priced = price_basket(apply(baskets, ev))
        total = 0
        for line in priced:
            total += line["net"]
        peak = max(peak, total)
        trail.add(ev[0], priced)
    print(f"sessions: {len(baskets)}  basket states: {len(trail)}  peak basket: {peak}  tiers: {len(names)}")
    for session, priced in trail.latest(3):
        print(f"  {session} lines={len(priced)} net={sum(line['net'] for line in priced)}")


if __name__ == "__main__":
    main(sys.argv[1:])
