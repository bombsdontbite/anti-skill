"""Writes payments.csv, a day of card payments with the acquirer's resends (fixed seed).

usage: python3 gen_input.py [--rows N] [--merchants M] [--out payments.csv]
The defaults are the test file's: 60,000 rows spread over 15,000 merchants.
"""
import argparse
import csv
import datetime
import random


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", type=int, default=60000)
    ap.add_argument("--merchants", type=int, default=15000)
    ap.add_argument("--out", default="payments.csv")
    a = ap.parse_args()
    rng = random.Random(2716)
    merchants = [f"M{i:06d}" for i in range(a.merchants)]
    rows, sent = [], []
    while len(rows) < a.rows:
        if sent and rng.random() < 0.03:
            row = rng.choice(sent)  # a resend of an earlier payment
        else:
            row = (rng.choice(merchants), f"T{rng.randrange(10**12):012d}", rng.randint(100, 250000),
                   rng.choice(["PLN", "PLN", "PLN", "EUR"]))
            sent.append(row)
        ts = datetime.datetime(2026, 10, 30) + datetime.timedelta(seconds=len(rows) * 86400 // a.rows)
        rows.append(row + (ts.isoformat(timespec="seconds"),))
    with open(a.out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["merchant", "txn", "cents", "currency", "ts"])
        w.writerows(rows)


if __name__ == "__main__":
    main()
