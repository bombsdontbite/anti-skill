"""Score a regex against a hidden string family. Usage: score.py <candidate.py> [--split train|test]

score = accuracy (re.fullmatch) on the split's examples - 0.001 * len(PATTERN).
`score.py --write-train` regenerates train_examples.json from the train seed.
The candidate's process only hands over PATTERN; a second process that never imports the candidate
compiles and matches it, so rebinding re.compile cannot stand in for a regex.
"""
import json
import os
import random
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import _bench  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
TRAIN_SEED = "regex-train-8"
TEST_SEED = "regex-test-35"
SIZES = {"train": 200, "test": 1000}
MAX_PATTERN = 2000
TIMEOUT = 10.0
MDAYS = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


def is_member(s):
    if len(s) != 10 or s[4] not in "-." or s[7] != s[4]:
        return False
    y, mo, d = s[:4], s[5:7], s[8:]
    if not (y + mo + d).isascii() or not (y + mo + d).isdigit():
        return False
    y, mo, d = int(y), int(mo), int(d)
    return 1900 <= y <= 2099 and 1 <= mo <= 12 and 1 <= d <= MDAYS[mo - 1]


def positive(rng):
    mo = rng.randint(1, 12)
    sep = rng.choice("-.")
    return f"{rng.randint(1900, 2099):04d}{sep}{mo:02d}{sep}{rng.randint(1, MDAYS[mo - 1]):02d}"


def negative(rng):
    y, mo = rng.randint(1900, 2099), rng.randint(1, 12)
    d, sep = rng.randint(1, MDAYS[mo - 1]), rng.choice("-.")
    kind = rng.randrange(11)
    if kind == 0:
        mo = rng.choice([0, 13, 14, 15, 19, 20, 21])
    elif kind == 1:
        d = rng.choice([0, 32, 33, 39, 40, 41])
    elif kind == 2:
        mo = rng.choice([2, 4, 6, 9, 11])
        d = MDAYS[mo - 1] + rng.randint(1, 31 - MDAYS[mo - 1]) if mo != 2 else rng.choice([30, 31])
    elif kind == 3:
        y = rng.choice([rng.randint(1000, 1899), rng.randint(2100, 2999), rng.randint(0, 999)])
    if kind == 4:
        a, b = rng.sample("-./ _:", 2)
        return f"{y:04d}{a}{mo:02d}{b}{d:02d}"
    if kind == 5:
        a = rng.choice("/ _:,")
        return f"{y:04d}{a}{mo:02d}{a}{d:02d}"
    if kind == 6:
        return f"{y}{sep}{mo}{sep}{d}" if mo < 10 or d < 10 else f"{y}{sep}{mo}{sep}{d:03d}"
    base = f"{y:04d}{sep}{mo:02d}{sep}{d:02d}"
    if kind == 7:
        i = rng.randrange(len(base) + 1)
        return base[:i] + rng.choice("0123456789") + base[i:]
    if kind == 8:
        i = rng.randrange(len(base))
        return base[:i] + base[i + 1:]
    if kind == 9:
        return rng.choice([" ", "", "x"]) + base + rng.choice([" ", "\n", "Z", "0"])
    if kind == 10:
        i = rng.choice([0, 1, 2, 3, 5, 6, 8, 9])
        return base[:i] + rng.choice("OoIl٣") + base[i + 1:]
    return base


def examples(seed, n):
    rng = random.Random(seed)
    pos, neg = set(), set()
    while len(pos) < n:
        pos.add(positive(rng))
    while len(neg) < n:
        s = negative(rng)
        if not is_member(s):
            neg.add(s)
    return {"positive": sorted(pos), "negative": sorted(neg)}


READER = r'''
import re as _re
_RE = dict(vars(_re))

def _run(cand, p):
    now = vars(_re)
    if set(now) != set(_RE) or any(now[k] is not v for k, v in _RE.items()):
        return {"error": "the candidate changed the re module"}
    pat = cand.PATTERN
    if type(pat) is not str:
        return {"error": "PATTERN must be a str"}
    if len(pat) > p["max_len"]:
        return {"error": f"PATTERN longer than {p['max_len']} characters"}
    return {"pattern": pat}
'''

# Runs beside an empty module, never the candidate: the pattern is data here.
MATCHER = r'''
import re as _re

def _run(cand, p):
    rx = _re.compile(p["pattern"])
    return {"match": [rx.fullmatch(s) is not None for s in p["strings"]]}
'''


def _phase(res, phase, left=TIMEOUT):
    """Name the phase that ran out of the one budget: a starved honest run is not a catastrophic one."""
    if str(res.get("error", "")).startswith("time limit exceeded"):
        return dict(res, error=f"time limit exceeded while {phase}, which had {left:g}s of the "
                               f"{TIMEOUT:g}s budget for reading PATTERN and matching")
    return res


def main():
    if "--write-train" in sys.argv:
        with open(os.path.join(HERE, "train_examples.json"), "w", encoding="utf-8") as f:
            json.dump(examples(TRAIN_SEED, SIZES["train"]), f, indent=1, ensure_ascii=False)
            f.write("\n")
        return
    cand, split = _bench.parse_args(sys.argv)
    seed = TRAIN_SEED if split == "train" else _bench.test_seed(TEST_SEED)
    ex = examples(seed, SIZES[split])
    strings = ex["positive"] + ex["negative"]
    truth = [True] * len(ex["positive"]) + [False] * len(ex["negative"])
    t0 = time.monotonic()
    res = _bench.run_child(cand, READER, {"max_len": MAX_PATTERN}, TIMEOUT)
    if "error" in res:
        return _bench.fail(_phase(res, "reading PATTERN"))
    pat = res.get("pattern")
    if type(pat) is not str or len(pat) > MAX_PATTERN:
        return _bench.fail({"error": f"no PATTERN of at most {MAX_PATTERN} characters"})
    # One budget for both processes, as the single process had.
    left = round(TIMEOUT - (time.monotonic() - t0), 2)
    if left <= 0:
        return _bench.fail(_phase({"error": "time limit exceeded"}, "reading PATTERN"))
    res = _bench.run_child(None, MATCHER, {"pattern": pat, "strings": strings}, left, source="")
    if "error" in res:
        return _bench.fail(_phase(res, "matching", left))
    got = res.get("match")
    if not isinstance(got, list) or len(got) != len(truth) or not all(type(g) is bool for g in got):
        return _bench.fail({"error": "missing match results"})
    pos_ok = sum(g and t for g, t in zip(got, truth))
    neg_ok = sum((not g) and (not t) for g, t in zip(got, truth))
    acc = (pos_ok + neg_ok) / len(truth)
    plen = len(pat)
    detail = {"split": split, "accuracy": round(acc, 6), "pattern_length": plen,
              "positives_matched": f"{pos_ok}/{len(ex['positive'])}",
              "negatives_rejected": f"{neg_ok}/{len(ex['negative'])}"}
    _bench.emit(True, acc - 0.001 * plen, detail)


if __name__ == "__main__":
    main()
