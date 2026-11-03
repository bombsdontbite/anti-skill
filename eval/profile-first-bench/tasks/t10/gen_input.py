"""Writes listings.jsonl, a day's new marketplace listings (fixed seed).

usage: python3 gen_input.py [--listings N] [--out listings.jsonl]
"""
import argparse
import json
import random

BRANDS = ["Bosch", "Makita", "IKEA", "Samsung", "Lego", "Canon", "Sony", "Philips", "Dyson", "Trek"]
THINGS = ["drill", "sofa", "phone", "bike", "camera", "lamp", "vacuum", "kettle", "desk", "speaker",
          "monitor", "chair", "tent", "guitar", "stroller"]
WORDS = ["new", "used", "mint", "boxed", "cheap", "urgent", "pickup", "warranty", "black", "white",
         "large", "small", "set", "kit", "pro", "classic", "2024", "2025", "original", "spare"]


def title(rng):
    words = [rng.choice(BRANDS), rng.choice(THINGS)] + rng.sample(WORDS, rng.randint(2, 5))
    rng.shuffle(words)
    return " ".join(words)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--listings", type=int, default=1400)
    ap.add_argument("--out", default="listings.jsonl")
    a = ap.parse_args()
    rng = random.Random(2700)
    titles = []
    for i in range(a.listings):
        if titles and rng.random() < 0.15:
            words = rng.choice(titles).split()
            rng.shuffle(words)
            t = " ".join(words + ([rng.choice(WORDS)] if rng.random() < 0.5 else []))
        else:
            t = title(rng)
        titles.append(t)
    with open(a.out, "w", encoding="utf-8") as f:
        for i, t in enumerate(titles):
            f.write(json.dumps({"id": 100000 + i, "title": t, "price": rng.randint(5, 3000)}) + "\n")


if __name__ == "__main__":
    main()
