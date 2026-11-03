"""Writes addresses.txt (one batch) and geocache.json (answers from earlier batches), fixed seed.

usage: python3 gen_input.py [--addresses N] [--cached N]
"""
import argparse
import json
import random

STREETS = ["Długa", "Floriańska", "Grodzka", "Karmelicka", "Krowoderska", "Lubicz", "Mogilska",
           "Nowohucka", "Wielicka", "Zakopiańska", "Kalwaryjska", "Starowiślna", "Dietla", "Basztowa"]
CITIES = ["Kraków", "Wieliczka", "Skawina", "Niepołomice", "Zabierzów"]


def address(rng):
    return f"ul. {rng.choice(STREETS)} {rng.randint(1, 240)}/{rng.randint(1, 40)}, {rng.choice(CITIES)}"


def key(a):
    parts = a.lower().replace(",", " ").split()
    return " ".join(p.rstrip(".") for p in parts if p not in ("ul", "ul.", "street", "st"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--addresses", type=int, default=10000)
    ap.add_argument("--cached", type=int, default=350000)
    a = ap.parse_args()
    rng = random.Random(2713)
    cache = {}
    while len(cache) < a.cached:
        cache[key(address(rng))] = [round(rng.uniform(49.9, 50.2), 6), round(rng.uniform(19.7, 20.2), 6)]
    with open("geocache.json", "w", encoding="utf-8") as f:
        json.dump(cache, f)
    with open("addresses.txt", "w", encoding="utf-8") as f:
        for _ in range(a.addresses):
            f.write(address(rng) + "\n")


if __name__ == "__main__":
    main()
