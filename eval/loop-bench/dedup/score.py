"""Score a faster near_duplicates. Usage: score.py <candidate.py> [--split train|test]

score = median reference CPU time / median candidate CPU time over RUNS alternating fresh
processes (import time counts); invalid if any set of pairs differs from the reference's.
"""
import bisect
import os
import random
import statistics
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import _bench  # noqa: E402

TRAIN_SEED = "dedup-train-8"
TEST_SEED = "dedup-test-39"
RUNS = 3
TIMED = (("titles", 3000), ("short", 3000))
RUN_TIMEOUT = 40.0
SLOWDOWN_CAP = 3.0  # a candidate this many times slower than the reference is cut off

REFERENCE = '''
def near_duplicates(records):
    sets = [set(r.split()) for r in records]
    pairs = []
    for i in range(len(sets)):
        a = sets[i]
        for j in range(i + 1, len(sets)):
            b = sets[j]
            inter = len(a & b)
            union = len(a) + len(b) - inter
            if union and 5 * inter >= 4 * union:
                pairs.append((i, j))
    return pairs
'''
_ns = {}
exec(REFERENCE, _ns)
reference = _ns["near_duplicates"]

SYLLABLES = ["ka", "to", "ri", "an", "el", "mo", "su", "ne", "li", "ar", "in", "or", "be",
             "da", "fi", "go", "ul", "ze", "pa", "th"]


class Vocabulary:
    def __init__(self, rng, size, skew):
        words = set()
        while len(words) < size:
            words.add("".join(rng.choice(SYLLABLES) for _ in range(rng.randint(1, 4))))
        self.words = sorted(words)
        rng.shuffle(self.words)
        acc, self.cum = 0.0, []
        for r in range(size):
            acc += 1 / (r + 1) ** skew
            self.cum.append(acc)
        self.rng = rng

    def word(self):
        return self.words[bisect.bisect(self.cum, self.rng.random() * self.cum[-1])]


def variant(rng, voc, toks):
    t = list(toks)
    for _ in range(rng.choice((0, 1, 1, 2, 3))):
        op = rng.random()
        if op < 0.35 and len(t) > 1:
            t.pop(rng.randrange(len(t)))
        elif op < 0.65:
            t.insert(rng.randint(0, len(t)), voc.word())
        elif op < 0.9:
            t[rng.randrange(len(t))] = voc.word()
        else:
            k = rng.randrange(len(t))
            t[k] = t[k].capitalize()
    if rng.random() < 0.3:
        rng.shuffle(t)
    return t


def records(rng, kind, n):
    if kind == "titles":
        voc, lo, hi, number = Vocabulary(rng, 3000, 0.9), 3, 12, 0.3
    elif kind == "short":
        voc, lo, hi, number = Vocabulary(rng, 400, 0.5), 2, 6, 0.1
    else:  # "dense": a tiny vocabulary, so many pairs sit right at the threshold
        voc, lo, hi, number = Vocabulary(rng, rng.randint(6, 30), 0.3), 1, 9, 0.0
    out = []
    while len(out) < n:
        toks = [voc.word() for _ in range(rng.randint(lo, hi))]
        if rng.random() < number:
            toks.append(str(rng.randint(1, 500)))
        out.append(toks)
        if rng.random() < 0.3:
            out.extend(variant(rng, voc, toks) for _ in range(rng.randint(1, 3)))
    out = out[:n]
    rng.shuffle(out)
    seps = (" ", " ", " ", " ", "  ", "\t")
    return [rng.choice(seps).join(t) if rng.random() < 0.1 else " ".join(t) for t in out]


def edge_cases(rng):
    cases = [
        [], ["solo"], ["", "   ", "\n", "a"], ["", ""],
        ["a b", "b a", "a  b", "a\tb\n", " a b ", "a b", "a b a"],
        ["a b c d e", "a b c d", "a b c d f", "a b c", "A b c d e"],
        ["p q r s t u v w x", "p q r s t u v w y", "p q r s t u v w"],
        ["x x x", "x", "X", "x y"],
    ]
    for _ in range(60):
        cases.append(records(rng, "dense", rng.randint(0, 40)))
    cases.append(records(rng, "dense", 400))
    cases.append(records(rng, "short", 500))
    return cases


def stress_cases(rng):
    """Inputs the statement allows and the random kinds rarely make."""
    voc = Vocabulary(rng, 50, 0.5)
    long_rec = [voc.word() for _ in range(150)]
    return [
        ["a b c"] * 300,  # many identical records
        [" ".join(long_rec), " ".join(long_rec[:-1]), " ".join(long_rec[:120]), " ".join(reversed(long_rec))],
        [" ".join(voc.word() for _ in range(rng.randint(40, 120))) for _ in range(60)],
        ["été café", "ete cafe", "ÉTÉ café", "été  café", "café été"],
        ["1 2 3 4 5", "1 2 3 4 5 6", "12 3 4 5", "1 2 3 4"],
        ["x " * 50, "x", "x y " * 25, "y x"],
        [" ".join(voc.word() for _ in range(rng.randint(1, 3))) for _ in range(400)],
    ]


RUNNER = r'''
_cpu = time.process_time
_cpu_start = _cpu()

def _pairs(rep):
    out = []
    for row in rep:
        i, j = row
        if type(i) is not int or type(j) is not int:
            raise ValueError("every pair must be two ints")
        out.append([i, j])
    return out

def _run(cand, p):
    res = {"edge": [], "timed": [], "cpu": _cpu() - _cpu_start}
    _arm(p["timeout"])
    try:
        for recs in p["edge"]:
            res["edge"].append(_pairs(cand.near_duplicates(list(recs))))
        for recs in p["timed"]:
            recs = list(recs)
            t0 = _cpu()
            out = _pairs(cand.near_duplicates(recs))
            res["cpu"] += _cpu() - t0
            res["timed"].append(out)
    finally:
        _disarm()
    return res
'''


def canonical(pairs):
    return sorted(tuple(p) for p in pairs)


def main():
    cand, split = _bench.parse_args(sys.argv)
    seed = {"train": TRAIN_SEED, "stress": "dedup-stress-1"}.get(split) or _bench.test_seed(TEST_SEED)
    timed = [records(random.Random(f"{seed}/timed/{i}"), kind, n)
             for i, (kind, n) in enumerate(TIMED)]
    edge = edge_cases(random.Random(f"{seed}/edge"))
    if split == "stress":
        edge += stress_cases(random.Random("dedup-stress-1"))
        timed = timed[:1]
    expected_edge = [canonical(reference(c)) for c in edge]
    payload = {"timed": timed, "edge": [], "timeout": RUN_TIMEOUT}
    ref_times, cand_times, expected = [], [], None
    for run in range(RUNS):
        ref = _bench.run_child(None, RUNNER, payload, RUN_TIMEOUT + 5, source=REFERENCE)
        if "error" in ref:
            return _bench.fail({"error": f"reference failed: {ref['error']}"})
        expected = expected or [canonical(t) for t in ref["timed"]]
        ref_times.append(ref["cpu"])
        cap = max(1.5, SLOWDOWN_CAP * ref["cpu"] + 1.0)
        res = _bench.run_child(cand, RUNNER, dict(payload, timeout=cap,
                                                  edge=edge if run == 0 else []), cap + 5)
        if "error" in res:
            return _bench.fail(res)
        if run == 0:
            if len(res.get("edge", [])) != len(edge):
                return _bench.fail({"error": "missing correctness tests"})
            for i, (got, want) in enumerate(zip(res["edge"], expected_edge)):
                if canonical(got) != want:
                    return _bench.fail({"error": f"wrong pairs on correctness test {i}"})
        timed_out = res.get("timed", [])
        if len(timed_out) != len(timed) or [canonical(t) for t in timed_out] != expected:
            return _bench.fail({"error": f"wrong pairs on a timed input (run {run})"})
        cand_times.append(res["cpu"])
    ref_t, cand_t = statistics.median(ref_times), max(statistics.median(cand_times), 1e-6)
    detail = {"split": split, "reference_cpu_s": round(ref_t, 4), "candidate_cpu_s": round(cand_t, 6),
              "runs": RUNS, "pairs": [len(e) for e in expected]}
    _bench.emit(True, ref_t / cand_t, detail)


if __name__ == "__main__":
    main()
