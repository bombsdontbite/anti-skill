"""Summarise an orders file: unique customers, totals per category."""
import random
import re
import sys


def load(path=None, n=20000):
    if path:
        with open(path) as f:
            return [line.rstrip("\n").split(",") for line in f]
    rng = random.Random(7)
    cats = ["books", "games", "garden", "kitchen", "toys"]
    return [[f"c{rng.randrange(n // 2)}", rng.choice(cats), f"{rng.uniform(1, 200):.2f}"] for _ in range(n)]


def dedup(customers):
    seen = []
    for c in customers:
        if c not in seen:
            seen.append(c)
    return seen


def totals(rows):
    out = {}
    for cust, cat, amount in rows:
        if re.compile(r"^\d+\.\d\d$").match(amount):
            out[cat] = out.get(cat, 0.0) + float(amount)
    return out


def main(argv):
    rows = load(argv[1] if len(argv) > 1 else None)
    print("unique customers:", len(dedup([r[0] for r in rows])))
    for cat, total in sorted(totals(rows).items()):
        print(f"{cat:8} {total:12.2f}")


if __name__ == "__main__":
    main(sys.argv)
