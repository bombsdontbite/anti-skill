"""Writes events.jsonl, one day of warehouse stock events (fixed seed).

usage: python3 gen_input.py [--events N] [--out events.jsonl]
"""
import argparse
import json
import random

TAGS = ["fragile", "bulky", "promo", "seasonal", "hazmat", "cold", "returnable", "gift"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--events", type=int, default=40000)
    ap.add_argument("--out", default="events.jsonl")
    a = ap.parse_args()
    rng = random.Random(2630)
    skus = [f"SKU-{i:05d}" for i in range(300)]
    locs = [f"{aisle}-{bay:02d}" for aisle in "ABCDEFGH" for bay in range(1, 13)]
    kinds = ["stock.received", "stock.picked", "price.changed", "tag.added"]
    with open(a.out, "w", encoding="utf-8") as f:
        for seq in range(a.events):
            kind = rng.choices(kinds, [5, 4, 1, 1])[0]
            ev = {"seq": seq, "type": kind, "sku": rng.choice(skus)}
            if kind == "stock.received":
                ev.update(qty=rng.randint(5, 60), lot=f"L{seq:07d}", loc=rng.choice(locs))
            elif kind == "stock.picked":
                ev.update(qty=rng.randint(1, 25))
            elif kind == "price.changed":
                ev.update(price_cents=rng.randint(99, 49999))
            else:
                ev.update(tag=rng.choice(TAGS))
            f.write(json.dumps(ev) + "\n")


if __name__ == "__main__":
    main()
