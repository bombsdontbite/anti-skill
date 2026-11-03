"""Writes the data files the task folders ship with: t01/vocab.txt and t05/fixtures/sample.csv.

usage: python3 build_assets.py   (fixed seeds; rerunning gives the same bytes)
"""
import os
import random
import subprocess
import sys

TASKS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tasks")
ONSETS = ["b", "br", "c", "ch", "cl", "d", "dr", "f", "fl", "g", "gr", "h", "j", "k", "l", "m",
          "n", "p", "pl", "r", "s", "sh", "st", "t", "tr", "v", "w", "z"]
VOWELS = ["a", "e", "i", "o", "u", "ai", "ea", "io", "ou"]
CODAS = ["", "", "n", "r", "s", "t", "l", "m", "x", "nd", "st"]


def vocab(n=6000, seed=26):
    rng = random.Random(seed)
    words, seen = [], set()
    while len(words) < n:
        w = "".join(rng.choice(ONSETS) + rng.choice(VOWELS) + rng.choice(CODAS)
                    for _ in range(rng.randint(2, 3)))
        if 6 <= len(w) <= 9 and w not in seen:
            seen.add(w)
            words.append(w)
    return words


def main():
    with open(os.path.join(TASKS, "t01", "vocab.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(vocab()) + "\n")
    t05 = os.path.join(TASKS, "t05")
    os.makedirs(os.path.join(t05, "fixtures"), exist_ok=True)
    subprocess.run([sys.executable, "gen_input.py", "--rows", "200", "--out",
                    os.path.join("fixtures", "sample.csv")], cwd=t05, check=True)


if __name__ == "__main__":
    main()
