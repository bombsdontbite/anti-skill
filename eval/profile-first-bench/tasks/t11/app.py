"""Counts the sender domains in a support mailbox export and flags lookalike domains.

usage: python3 app.py mailbox.txt
"""
import sys
from collections import Counter
import re

ADDRESS = re.compile(r"([\w.+-]+)@([\w-]+(?:\.[\w-]+)+)")
CONFUSABLE = {"0": "o", "1": "l", "3": "e", "5": "s", "7": "t", "rn": "m", "vv": "w"}
TRUSTED = ["yeti.example", "support.example", "billing.example", "shop.example"]


def read_mailbox(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def addresses(text):
    return ADDRESS.finditer(text)


def domain_counts(matches):
    counts = Counter()
    for m in matches:
        counts[m.group(2).lower()] += 1
    return counts


def lookalikes(domains):
    """Domains that read as a trusted one once every confusable is folded, in every order."""
    flagged = []
    for d in domains:
        for t in TRUSTED:
            for a, b in CONFUSABLE.items():
                for c, e in CONFUSABLE.items():
                    if d != t and d.replace(a, b).replace(c, e) == t:
                        flagged.append(d)
    return sorted(set(flagged))


def main(argv):
    text = read_mailbox(argv[0])
    counts = domain_counts(addresses(text))
    flagged = lookalikes(list(counts))
    print(f"addresses: {sum(counts.values())}  domains: {len(counts)}  lookalikes: {len(flagged)}")
    for domain, n in counts.most_common(8):
        print(f"  {domain:28s} {n:7d}")
    for domain in flagged:
        print(f"  lookalike: {domain}")


if __name__ == "__main__":
    main(sys.argv[1:])
