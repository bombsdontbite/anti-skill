"""Fraud rules engine: scores a day of card transactions and prints the decisions.

usage: python3 app.py transactions.csv
"""
import csv
import logging
import os
import sys
from collections import Counter

log = logging.getLogger("engine")

HIGH_RISK = {"NG", "RU", "KP", "VE"}
RISKY_MCC = {"4829", "6051", "7995", "5967"}


def setup_logging():
    logging.basicConfig(filename="engine.log", filemode="w",
                        level=os.environ.get("ENGINE_LOG_LEVEL", "DEBUG"),
                        format="%(asctime)s %(levelname)s %(name)s %(message)s")


def load_transactions(path):
    with open(path, newline="", encoding="utf-8") as f:
        return [{"id": r["id"], "account": r["account"], "amount": float(r["amount"]),
                 "currency": r["currency"], "country": r["country"], "mcc": r["mcc"],
                 "hour": int(r["hour"])} for r in csv.DictReader(f)]


RULES = [
    ("large", lambda t, h: t["amount"] > 2500),
    ("night", lambda t, h: t["hour"] < 5),
    ("country", lambda t, h: t["country"] in HIGH_RISK),
    ("mcc", lambda t, h: t["mcc"] in RISKY_MCC),
    ("velocity", lambda t, h: len(h) >= 4 and sum(h[-4:]) > 3000),
    ("spike", lambda t, h: bool(h) and t["amount"] > 8 * (sum(h) / len(h))),
    ("round", lambda t, h: t["amount"] >= 100 and t["amount"] % 100 == 0),
    ("fx", lambda t, h: t["currency"] not in ("EUR", "PLN")),
]


def apply_rules(txn, history):
    return [name for name, rule in RULES if rule(txn, history)]


def make_key(txn):
    return f"{txn['account']}:{txn['currency']}:{txn['amount']:.2f}:{txn['mcc']}"


def process(txns):
    history, decisions, rule_hits, keys, duplicates = {}, Counter(), Counter(), set(), 0
    for txn in txns:
        key = make_key(txn)
        log.debug("txn %s start key=%s txn=%r", txn["id"], key, txn)
        if key in keys:
            duplicates += 1
        keys.add(key)
        past = history.setdefault(txn["account"], [])
        hits = apply_rules(txn, past)
        log.debug("txn %s rules=%r", txn["id"], hits)
        score = len(hits) + 2 * ("velocity" in hits) + 2 * ("country" in hits)
        decision = "block" if score >= 4 else "review" if score >= 2 else "allow"
        state = {"account": txn["account"], "score": score, "decision": decision,
                 "history_len": len(past), "recent": past[-4:], "hits": hits}
        log.debug("txn %s decision=%s state=%r", txn["id"], decision, state)
        past.append(txn["amount"])
        decisions[decision] += 1
        rule_hits.update(hits)
    return decisions, rule_hits, duplicates


def main(argv):
    setup_logging()
    txns = load_transactions(argv[0])
    decisions, rule_hits, duplicates = process(txns)
    print(f"transactions: {len(txns)}  possible duplicates: {duplicates}")
    for d in ("allow", "review", "block"):
        print(f"{d:7s} {decisions[d]:7d}")
    for name, n in sorted(rule_hits.items(), key=lambda kv: (-kv[1], kv[0])):
        print(f"  rule {name:9s} {n:7d}")


if __name__ == "__main__":
    main(sys.argv[1:])
