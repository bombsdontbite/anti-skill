"""Writes queries.txt, a day of shop search queries (fixed seed).

usage: python3 gen_input.py [--queries N] [--out queries.txt]
"""
import argparse
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
LETTERS = "abcdefghijklmnopqrstuvwxyz"


def typo(rng, word):
    i = rng.randrange(len(word))
    kind = rng.randrange(3)
    if kind == 0:
        return word[:i] + word[i + 1:]
    if kind == 1:
        return word[:i] + rng.choice(LETTERS) + word[i + 1:]
    return word[:i] + rng.choice(LETTERS) + word[i:]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--queries", type=int, default=6000)
    ap.add_argument("--out", default="queries.txt")
    a = ap.parse_args()
    rng = random.Random(2610)
    with open(os.path.join(HERE, "vocab.txt"), encoding="utf-8") as f:
        vocab = [w.strip() for w in f if w.strip()]
    weights = [1 / (r + 1) ** 0.8 for r in range(len(vocab))]
    with open(a.out, "w", encoding="utf-8") as f:
        for _ in range(a.queries):
            words = rng.choices(vocab, weights, k=rng.randint(1, 3))
            words = [typo(rng, w) if rng.random() < 0.25 else w for w in words]
            if rng.random() < 0.2:
                words[0] = words[0].capitalize()
            f.write(" ".join(words) + "\n")


if __name__ == "__main__":
    main()
