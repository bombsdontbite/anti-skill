"""Reconciles a carrier export: pairs each delivery with its shipment and bills it from the rate grid.

usage: python3 app.py shipments.csv
"""
import csv
import sys

ZONES = 300
BANDS = 200


def build_rate_grid(zones=ZONES, bands=BANDS):
    """Price per zone and half-kilo weight band."""
    grid = []
    for z in range(zones):
        row = []
        base = 2.5 + 0.04 * z
        for b in range(bands):
            row.append(round(base * (1 + b * 0.5) ** 0.85 + (z % 7) * 0.1, 2))
        grid.append(row)
    return grid


def load_rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        r = csv.reader(f)
        next(r)
        return [(kind, ref, carrier, int(zone), float(kg), ts) for kind, ref, carrier, zone, kg, ts in r]


def match_deliveries(rows):
    open_refs, open_rows, matched, orphans = [], [], [], []
    for row in rows:
        if row[0] == "SHIP":
            open_refs.append(row[1])
            open_rows.append(row)
            continue
        try:
            i = open_refs.index(row[1])
        except ValueError:
            orphans.append(row)
            continue
        matched.append((open_rows[i], row))
        del open_refs[i]
        del open_rows[i]
    return matched, open_rows, orphans


def bill(matched, grid):
    per_carrier = {}
    for ship, _delivery in matched:
        band = min(int(ship[4] * 2), BANDS - 1)
        cents = round(grid[ship[3] - 1][band] * 100)
        n, total = per_carrier.get(ship[2], (0, 0))
        per_carrier[ship[2]] = (n + 1, total + cents)
    return per_carrier


def main(argv):
    grid = build_rate_grid()
    rows = load_rows(argv[0])
    matched, still_open, orphans = match_deliveries(rows)
    per_carrier = bill(matched, grid)
    print(f"rows: {len(rows)}  delivered: {len(matched)}  open: {len(still_open)}  orphans: {len(orphans)}")
    for carrier, (n, cents) in sorted(per_carrier.items()):
        print(f"{carrier:8s} {n:7d} parcels  {cents / 100:12.2f}")
    if still_open:
        print("oldest open: " + ", ".join(r[1] for r in still_open[:5]))


if __name__ == "__main__":
    main(sys.argv[1:])
