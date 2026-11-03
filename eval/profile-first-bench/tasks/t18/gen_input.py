"""Writes timesheets.csv, a month of clock-in records from the handheld scanners (fixed seed).

usage: python3 gen_input.py [--people N] [--out timesheets.csv]
The scanners log a new record at every break, so a person has many short shifts a day.
"""
import argparse
import csv
import random

TEAMS = ["pick", "pack", "dispatch", "returns", "inbound", "yard"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--people", type=int, default=400)
    ap.add_argument("--out", default="timesheets.csv")
    a = ap.parse_args()
    rng = random.Random(2718)
    with open(a.out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["person", "team", "day", "start", "end"])
        for p in range(a.people):
            team = rng.choice(TEAMS)
            for day in range(1, 31):
                t = rng.randrange(300, 600)
                for _ in range(rng.randint(30, 70)):
                    length = rng.randint(5, 25)
                    w.writerow([f"E{p:05d}", team, f"2026-10-{day:02d}", t, t + length])
                    t += length + rng.randint(-3, 6)


if __name__ == "__main__":
    main()
