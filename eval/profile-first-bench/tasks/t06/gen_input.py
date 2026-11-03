"""Writes transactions.csv, one day of card transactions (fixed seed).

usage: python3 gen_input.py [--txns N] [--out transactions.csv]
"""
import argparse
import csv
import random

COUNTRIES = ["PL"] * 30 + ["DE"] * 8 + ["CZ", "FR", "GB", "US", "NG", "RU", "VE", "UA", "LT", "SK"]
CURRENCIES = ["PLN"] * 12 + ["EUR"] * 6 + ["USD", "GBP", "CZK"]
MCCS = ["5411", "5812", "5541", "4111", "5999", "4829", "6051", "7995", "5967", "5732", "5311"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--txns", type=int, default=30000)
    ap.add_argument("--out", default="transactions.csv")
    a = ap.parse_args()
    rng = random.Random(2660)
    with open(a.out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "account", "amount", "currency", "country", "mcc", "hour"])
        for i in range(a.txns):
            amount = round(rng.lognormvariate(3.6, 1.3), 2) if rng.random() > 0.03 else rng.randint(1, 60) * 100
            w.writerow([f"T{i:08d}", f"A{rng.randrange(4000):05d}", amount, rng.choice(CURRENCIES),
                        rng.choice(COUNTRIES), rng.choice(MCCS), rng.randrange(24)])


if __name__ == "__main__":
    main()
