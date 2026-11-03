"""Settles a day of card payments per merchant, dropping the acquirer's duplicate resends.

usage: python3 app.py payments.csv
"""
import csv
import datetime
import sys

CUTOFF = datetime.datetime(2026, 10, 30, 22, 0)  # later payments go to the next batch
HOLIDAYS = {(1, 1), (1, 6), (5, 1), (5, 3), (8, 15), (11, 1), (11, 11), (12, 25), (12, 26)}


def load_rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        r = csv.reader(f)
        next(r)
        return [(merchant, txn, int(cents), currency, datetime.datetime.fromisoformat(ts))
                for merchant, txn, cents, currency, ts in r]


def drop_resends(rows):
    """The acquirer resends a payment it did not see acknowledged; keep the first of each."""
    seen = {}
    kept = []
    for row in rows:
        ids = seen.setdefault(row[0], [])
        if row[1] in ids:
            continue
        ids.append(row[1])
        kept.append(row)
    return kept


def settlement_day(today):
    """The next business day, skipping weekends and public holidays."""
    day = today + datetime.timedelta(days=1)
    while day.weekday() >= 5 or (day.month, day.day) in HOLIDAYS:
        day += datetime.timedelta(days=1)
    return day


def settle(rows):
    totals, late = {}, 0
    for merchant, _txn, cents, currency, ts in rows:
        if ts >= CUTOFF:
            late += 1
            continue
        key = (merchant, currency)
        totals[key] = totals.get(key, 0) + cents
    return totals, late


def main(argv):
    rows = load_rows(argv[0])
    kept = drop_resends(rows)
    totals, late = settle(kept)
    day = settlement_day(datetime.date(2026, 10, 30))
    print(f"payments: {len(rows)}  resends dropped: {len(rows) - len(kept)}  "
          f"merchants: {len({m for m, _ in totals})}  after cut-off: {late}  settles on {day.isoformat()}")
    for (merchant, currency), cents in sorted(totals.items(), key=lambda kv: (-kv[1], kv[0]))[:6]:
        print(f"  {merchant:10s} {currency} {cents / 100:14.2f}")


if __name__ == "__main__":
    main(sys.argv[1:])
