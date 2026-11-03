"""Writes readings.csv, one collection round of smart-meter readings (fixed seed).

usage: python3 gen_input.py [--rows N] [--out readings.csv]
"""
import argparse
import csv
import random


def check_digit(body):
    total = 0
    for i, ch in enumerate(reversed(body)):
        d = int(ch)
        if i % 2 == 0:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return str((10 - total % 10) % 10)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", type=int, default=20000)
    ap.add_argument("--out", default="readings.csv")
    a = ap.parse_args()
    rng = random.Random(2680)
    meters = []
    for _ in range(3000):
        body = f"{rng.randrange(10**8, 10**9)}"
        meters.append(body + check_digit(body))
    with open(a.out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["meter", "ts", "kwh"])
        for i in range(a.rows):
            meter = rng.choice(meters)
            if rng.random() < 0.03:
                meter = meter[:-1] + str((int(meter[-1]) + 1) % 10)
            w.writerow([meter, f"2026-10-{1 + i * 27 // a.rows:02d}T{i % 24:02d}:00:00",
                        round(rng.uniform(0.05, 4.5), 3)])


if __name__ == "__main__":
    main()
