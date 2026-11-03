"""Writes articles.md, help-centre articles in the lightweight markup (fixed seed).

usage: python3 gen_input.py [--articles N] [--out articles.md]
"""
import argparse
import random

WORDS = ("order refund parcel delivery invoice account password reset tracking courier return "
         "label voucher payment card transfer address cancel subscription login code email "
         "FAQ BLIK PIN OTP VAT SMS").split()


def phrase(rng, n):
    out = []
    for _ in range(n):
        w = rng.choice(WORDS)
        r = rng.random()
        if r < 0.05:
            w = f"**{w}**"
        elif r < 0.10:
            w = f"_{w}_"
        elif r < 0.13:
            w = f"`{w}`"
        elif r < 0.16:
            w = f"[{w}]({w}-help)"
        elif r < 0.18:
            w = f"{w} & <{rng.choice(WORDS)}>"
        elif r < 0.20:
            w = rng.choice(["--", "...", "(c)", w + "'", f"#{rng.randrange(10000, 99999)}"])
        out.append(w)
    return " ".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--articles", type=int, default=3000)
    ap.add_argument("--out", default="articles.md")
    a = ap.parse_args()
    rng = random.Random(2717)
    with open(a.out, "w", encoding="utf-8") as f:
        for i in range(a.articles):
            f.write(f"# {phrase(rng, 3).replace('*', '').replace('_', '').capitalize()} {i}\n")
            for _ in range(rng.randint(4, 14)):
                kind = rng.choice(["", "", "", "- ", "> ", "## "])
                f.write(kind + phrase(rng, rng.randint(4, 12) if kind == "## " else rng.randint(30, 90)) + "\n")


if __name__ == "__main__":
    main()
