"""Support triage: which of a customer's own products each ticket mentions.

usage: python3 app.py customers.csv tickets.txt
"""
import csv
import re
import sys
from collections import Counter


def load_customers(path):
    with open(path, newline="", encoding="utf-8") as f:
        return {r["customer"]: r["products"].split(";") for r in csv.DictReader(f)}


def parse_ticket(line):
    m = re.compile(r"^(T-\d{6})\|(C-\d{5})\|(.*)$").match(line)
    if m is None:
        raise ValueError(f"bad ticket line {line[:40]!r}")
    return m.groups()


def mentions(text, product):
    return re.search(rf"(?<!\w){re.escape(product)}(?!\w)", text, re.IGNORECASE) is not None


def main(argv):
    customers = load_customers(argv[0])
    named, unmatched, tickets = Counter(), 0, 0
    with open(argv[1], encoding="utf-8") as f:
        for line in f:
            ticket_id, customer, text = parse_ticket(line.rstrip("\n"))
            tickets += 1
            hits = [p for p in customers.get(customer, ()) if mentions(text, p)]
            named.update(hits)
            unmatched += not hits
    print(f"tickets: {tickets}  naming none of the customer's products: {unmatched}")
    for product, n in sorted(named.items(), key=lambda kv: (-kv[1], kv[0]))[:15]:
        print(f"{n:5d}  {product}")


if __name__ == "__main__":
    main(sys.argv[1:])
