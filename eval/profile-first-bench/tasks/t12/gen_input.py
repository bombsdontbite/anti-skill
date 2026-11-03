"""Writes events.tsv, a day of checkout events, tab-separated: lines added to and removed from baskets (fixed seed).

usage: python3 gen_input.py [--sessions N] [--out events.tsv]
"""
import argparse
import random


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sessions", type=int, default=3000)
    ap.add_argument("--out", default="events.tsv")
    a = ap.parse_args()
    rng = random.Random(2712)
    skus = [f"SKU-{i:05d}" for i in range(3000)]
    with open(a.out, "w", encoding="utf-8") as f:
        for i in range(a.sessions):
            held = []
            for _ in range(rng.randint(10, 60)):
                if held and rng.random() < 0.15:
                    ev = [f"S{i:06d}", "remove", held.pop(rng.randrange(len(held))), "", ""]
                else:
                    sku = rng.choice(skus)
                    held.append(sku)
                    ev = [f"S{i:06d}", "add", sku, str(rng.randint(1, 30)), str(rng.randint(99, 49999))]
                f.write("\t".join(ev) + "\n")


if __name__ == "__main__":
    main()
