"""Writes orders.csv, one night's export of orders (fixed seed).

usage: python3 gen_input.py [--orders N] [--out orders.csv]
"""
import argparse
import csv
import random
from datetime import datetime, timedelta


def ship_time(rng):
    secs = int(rng.lognormvariate(10.5, 0.9))
    d, rest = divmod(secs, 86400)
    h, rest = divmod(rest, 3600)
    m = rest // 60
    parts = [f"{d}d" if d else "", f"{h}h" if h else "", f"{m}m" if m or not (d or h) else ""]
    return "".join(parts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--orders", type=int, default=40000)
    ap.add_argument("--out", default="orders.csv")
    a = ap.parse_args()
    rng = random.Random(2620)
    start = datetime(2026, 10, 1)
    prices = {f"SKU-{i:05d}": f"{rng.uniform(1.5, 240):.2f}" for i in range(4000)}
    skus = list(prices)
    with open(a.out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["order_id", "customer", "sku", "qty", "unit_price", "ts", "ship_time"])
        for i in range(a.orders):
            sku = rng.choice(skus)
            ts = start + timedelta(seconds=rng.randrange(30 * 86400))
            w.writerow([f"O-{i:07d}", f"C-{rng.randrange(1500):05d}", sku, rng.randint(1, 5),
                        prices[sku], ts.isoformat(), ship_time(rng)])


if __name__ == "__main__":
    main()
