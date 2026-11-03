"""Writes a carrier export: shipments and deliveries in time order (fixed seed).

usage: python3 gen_input.py [--rows N] [--out shipments.csv]
The default size is the one fixtures/sample.csv was made with.
"""
import argparse
import csv
import random

CARRIERS = ["DHL", "DPD", "GLS", "InPost", "UPS"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", type=int, default=200)
    ap.add_argument("--out", default="shipments.csv")
    a = ap.parse_args()
    rng = random.Random(2650)
    span = 30 * 86400
    events = []
    refs = rng.sample(range(10_000_000), a.rows // 2)
    for ref in refs:
        t = rng.randrange(span)
        ship = ("SHIP", f"SH-{ref:07d}", rng.choice(CARRIERS), rng.randint(1, 300),
                round(rng.uniform(0.1, 140), 2))
        events.append((t, ship))
        r = rng.random()
        if r < 0.94:  # delivered, a while later
            events.append((t + int(rng.uniform(0.3, 1.0) * (span - t)) + 1, ("DLVR",) + ship[1:]))
        elif r < 0.96:  # a delivery whose shipment is in an older export
            events.append((t, ("DLVR", f"SH-{rng.randrange(10_000_000, 20_000_000):08d}") + ship[2:]))
    events.sort(key=lambda e: (e[0], e[1][0], e[1][1]))
    with open(a.out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["kind", "ref", "carrier", "zone", "kg", "ts"])
        for t, (kind, ref, carrier, zone, kg) in events:
            w.writerow([kind, ref, carrier, zone, kg, t])


if __name__ == "__main__":
    main()
