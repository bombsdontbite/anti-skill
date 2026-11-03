"""Writes mailbox.txt, a support mailbox export: headers, quoted replies and signatures (fixed seed).

usage: python3 gen_input.py [--messages N] [--out mailbox.txt]
"""
import argparse
import random

WORDS = ("order refund parcel delivery invoice account password reset broken missing late "
         "thanks please hello again still waiting tracking number courier warehouse return "
         "label replacement colour size wrong item charged twice voucher discount").split()
DOMAINS = ["gmail.example", "outlook.example", "yeti.example", "support.example", "proton.example",
           "wp.example", "onet.example", "interia.example", "o2.example", "seznam.example",
           "suppor7.example", "yet1.example", "biIling.example", "shop.example", "sh0p.example"]
NAMES = ["anna", "jan", "piotr", "kasia", "marek", "ewa", "tomasz", "ola", "pawel", "zofia"]


def address(rng):
    return f"{rng.choice(NAMES)}.{rng.choice(NAMES)}{rng.randint(1, 99)}@{rng.choice(DOMAINS)}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--messages", type=int, default=20000)
    ap.add_argument("--out", default="mailbox.txt")
    a = ap.parse_args()
    rng = random.Random(2711)
    with open(a.out, "w", encoding="utf-8") as f:
        for i in range(a.messages):
            f.write(f"From: {address(rng)}\nTo: help@support.example\nSubject: #{i} "
                    f"{' '.join(rng.choices(WORDS, k=5))}\n\n")
            for _ in range(rng.randint(3, 12)):
                f.write(" ".join(rng.choices(WORDS, k=rng.randint(6, 16))) + "\n")
            if rng.random() < 0.5:
                f.write(f"> On Monday {address(rng)} wrote:\n")
                for _ in range(rng.randint(2, 8)):
                    f.write("> " + " ".join(rng.choices(WORDS, k=rng.randint(6, 16))) + "\n")
            f.write("--\n" + " ".join(rng.choices(WORDS, k=4)) + "\n\n")


if __name__ == "__main__":
    main()
