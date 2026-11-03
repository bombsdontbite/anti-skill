"""Writes customers.csv and tickets.txt, a week of support tickets (fixed seed).

usage: python3 gen_input.py [--customers N] [--tickets N]
"""
import argparse
import csv
import random

LINES = ["Orbit", "Nova", "Pulse", "Atlas", "Ember", "Vertex", "Lumen", "Quartz", "Drift", "Halo",
         "Cinder", "Fjord", "Kestrel", "Mosaic", "Onyx", "Prism", "Rune", "Sable", "Tundra", "Zephyr"]
MODELS = ["Mini", "Max", "Pro", "Air", "Go", "Plus", "Lite", "One", "Duo", "S"]
FILLER = ("the device stopped charging after the update and the app shows an error when I try "
          "to pair it again I already reset it twice please advise on a replacement or refund "
          "my order arrived late and the box was damaged").split()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--customers", type=int, default=2500)
    ap.add_argument("--tickets", type=int, default=24000)
    a = ap.parse_args()
    rng = random.Random(2670)
    catalogue = [f"{l} {m} {n}" for l in LINES for m in MODELS for n in (10, 20, 40, 60, 80, 100, 120, 200)]
    owned = {}
    with open("customers.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["customer", "products"])
        for i in range(a.customers):
            products = rng.sample(catalogue, rng.randint(2, 4))
            owned[f"C-{i:05d}"] = products
            w.writerow([f"C-{i:05d}", ";".join(products)])
    ids = list(owned)
    with open("tickets.txt", "w", encoding="utf-8") as f:
        for t in range(a.tickets):
            customer = rng.choice(ids)
            words = rng.choices(FILLER, k=rng.randint(25, 60))
            r = rng.random()
            if r < 0.6:
                name = rng.choice(owned[customer])
                words.insert(rng.randrange(len(words)), name.lower() if rng.random() < 0.3 else name)
            elif r < 0.75:
                words.insert(rng.randrange(len(words)), rng.choice(owned[customer]) + "0")
            f.write(f"T-{t:06d}|{customer}|{' '.join(words)}\n")


if __name__ == "__main__":
    main()
