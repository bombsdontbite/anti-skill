"""Writes posts.jsonl, a month of feed posts with their raw hashtags (fixed seed).

usage: python3 gen_input.py [--posts N] [--out posts.jsonl]
"""
import argparse
import json
import random

SYL = ["ka", "lo", "mi", "ne", "ru", "sa", "to", "vi", "ze", "po", "da", "fu", "gi", "ho", "ju"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--posts", type=int, default=14000)
    ap.add_argument("--out", default="posts.jsonl")
    a = ap.parse_args()
    rng = random.Random(2640)
    vocab = sorted({"".join(rng.choice(SYL) for _ in range(rng.randint(2, 4))) for _ in range(6000)})
    rng.shuffle(vocab)
    vocab = vocab[:4500]
    weights = [1 / (r + 1) ** 0.5 for r in range(len(vocab))]
    with open(a.out, "w", encoding="utf-8") as f:
        for i in range(a.posts):
            raw = []
            for tag in rng.choices(vocab, weights, k=rng.randint(2, 6)):
                style = rng.randrange(4)
                raw.append(["#" + tag, tag.capitalize(), " " + tag, "#" + tag.upper()][style])
            f.write(json.dumps({"id": i, "author": f"u{rng.randrange(3000)}", "tags": raw}) + "\n")


if __name__ == "__main__":
    main()
