"""Writes articles.txt, help-centre articles separated by "# title" lines (fixed seed).

usage: python3 gen_input.py [--articles N] [--out articles.txt]
"""
import argparse
import random

WORDS = ("order refund parcel delivery invoice account password reset broken missing late "
         "tracking courier warehouse return label replacement colour size voucher discount "
         "payment card blik transfer address change cancel subscription app login code email "
         "the a an and or to of in on for is it your you").split()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--articles", type=int, default=6000)
    ap.add_argument("--out", default="articles.txt")
    a = ap.parse_args()
    rng = random.Random(2714)
    vocab = WORDS + [rng.choice(WORDS[:20]) + str(n) for n in range(4000)]
    with open(a.out, "w", encoding="utf-8") as f:
        for i in range(a.articles):
            f.write(f"# {' '.join(rng.choices(WORDS[:30], k=4)).capitalize()} ({i})\n")
            for _ in range(rng.randint(5, 25)):
                f.write(" ".join(rng.choices(vocab, k=rng.randint(8, 20))) + ".\n")
        f.write("# end\n")


if __name__ == "__main__":
    main()
