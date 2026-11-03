"""The scorers must fail closed: each known exploit or broken answer scores invalid, each baseline valid,
and the stress split must pass every baseline and catch a known fragile final. A candidate's string
hashing must not vary between runs, a module internal is refused however the module is rebound, and a
dunder outside the safe set cannot be defined.

Usage: python3 test_scorers.py [task ...]   One scorer process at a time; exits 1 on any mismatch.
"""
import contextlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile

B = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, B)
import _bench  # noqa: E402
TASKS = ["binpack", "tsp", "cache", "speedup", "schedule", "regex", "knapsack", "coloring", "dedup"]

SPEEDUP_BASE = open(os.path.join(B, "speedup", "candidate_baseline.py")).read()
# Patches re only when PATTERN is read, after the re check: 0.775 when matched in-process.
GETATTR_FORGE = ("import re\n\n\nclass M:\n    def fullmatch(self, s):\n"
                 "        return s if len(s) == 10 and s[4] in '-.' and s[7] == s[4] else None\n\n\n"
                 "def __getattr__(name):\n    re.compile = lambda p: M()\n    return ''\n")

# (task, case name, candidate source, expectation): "invalid", "valid" or ("valid_below", score)
CASES = [
    ("speedup", "clock overwrite (scored 2,142,043x before the fix)", "import time\ntime.process_time = lambda: 0.0\n"
     + SPEEDUP_BASE, ("valid_below", 3.0)),
    ("speedup", "lazy generator (scored 47,942x before the fix)", SPEEDUP_BASE.replace(
        "def usage_report(", "def _real(", 1) + "\n\ndef usage_report(sessions, windows):\n"
     "    return (r for r in _real(sessions, windows))\n", ("valid_below", 3.0)),
    ("binpack", "wrong number of priorities", "def priority(item, bins):\n    return [0]\n", "invalid"),
    ("knapsack", "exception", "def solve(values, weights, capacities):\n    raise RuntimeError('no')\n", "invalid"),
    ("coloring", "every vertex the same colour", "def color(n, edges):\n    return [0] * n\n", "invalid"),
    ("dedup", "no pairs at all", "def near_duplicates(records):\n    return []\n", "invalid"),
    ("schedule", "wrong type", "def schedule(jobs, m):\n    return None\n", "invalid"),
    ("tsp", "not a permutation", "def solve(points):\n    return [0] * len(points)\n", "invalid"),
    ("cache", "banned import", "import gc\n\nclass Cache:\n    def __init__(self, capacity):\n        pass\n\n"
     "    def access(self, key):\n        return False\n", "invalid"),
    ("regex", "file access", "PATTERN = open('/etc/hosts').read()\n", "invalid"),
    ("regex", "re.compile replaced, empty PATTERN (scored 0.775 before the second process)", "import re\n\n\nclass M:\n"
     "    def fullmatch(self, s):\n        return s if len(s) == 10 and s[4] in '-.' and s[7] == s[4] else None\n\n\n"
     "re.compile = lambda p: M()\nPATTERN = ''\n", "invalid"),
    ("regex", "re.compile replaced at PATTERN lookup (refused statically)", GETATTR_FORGE, "invalid"),
    ("tsp", "lazy search past the per-instance limit", open(os.path.join(B, "fixtures/tsp_lazy_search.py")).read(), "invalid"),
    ("schedule", "lazy search past the per-instance limit",
     open(os.path.join(B, "fixtures/schedule_lazy_search.py")).read(), "invalid"),
] + [(t, "baseline", None, "valid") for t in TASKS]

STRESS_TASKS = ["tsp", "schedule", "knapsack", "dedup", "coloring", "binpack", "cache"]
# The run-8 tsp final hangs when a point is its own nearest neighbour; the stress split must catch it.
STRESS_CASES = [(t, "baseline on stress", None, "valid") for t in STRESS_TASKS] + [
    ("tsp", "self-neighbour hang (run 8 final)", open(os.path.join(B, "runs/r8/candidate/tsp/final.py")).read(),
     "invalid")]


def score(task, src, split="train"):
    if src is None:
        path, tmp = os.path.join(B, task, "candidate_baseline.py"), None
    else:
        tmp = tempfile.NamedTemporaryFile("w", suffix=".py", delete=False)
        tmp.write(src)
        tmp.close()
        path = tmp.name
    try:
        out = subprocess.run([sys.executable, "score.py", path, "--split", split], cwd=os.path.join(B, task),
                             capture_output=True, text=True, timeout=900).stdout
        return json.loads(out.strip().splitlines()[-1])
    finally:
        if tmp:
            os.unlink(tmp.name)


HASH_CAND = "def h(s):\n    return hash(s)\n"
HASH_RUNNER = "def _run(cand, payload):\n    return {'h': cand.h(payload['s'])}\n"


def child_hashes(flags):
    saved, _bench.CHILD_FLAGS = _bench.CHILD_FLAGS, flags
    try:
        return [_bench.run_child(None, HASH_RUNNER, {"s": "abc"}, 30, source=HASH_CAND).get("h")
                for _ in range(2)]
    finally:
        _bench.CHILD_FLAGS = saved


def hash_seed_mismatches():
    """Two runs of a candidate hash "abc" alike. Under the old `-I -S`, which ignores
    PYTHONHASHSEED, they differ: that arm shows the check can fail."""
    bad = 0
    for flags, want_same in [(_bench.CHILD_FLAGS, True), (["-I", "-S"], False)]:
        h = child_hashes(flags)
        ok = None not in h and (h[0] == h[1]) == want_same
        bad += not ok
        print(f"{'ok      ' if ok else 'MISMATCH'} hash('abc') twice under {' '.join(flags)}: {h}", flush=True)
    return bad


# A module internal read through any rebinding of the module (an outside audit's `m = random; m._os`
# passed when the check matched only the module's own name). Each must be refused statically.
REBOUND = [
    ("an alias", "import random\nm = random\nx = m._os\n"),
    ("import as", "import random as r\nx = r._os\n"),
    ("a function argument", "import random\ndef f(m):\n    return m._os\nf(random)\n"),
    ("a lambda default", "import random\nf = lambda m=random: m._os\n"),
    ("a list item", "import random\nx = [random][0]._os\n"),
    ("a walrus", "import random\nif (m := random):\n    x = m._os\n"),
    ("a class pattern", "import random\nmatch random:\n    case object(_os=o):\n        pass\n"),
]
# A dunder bound by a def, a class or another string-named binding runs implicitly after the checks.
DUNDER_DEFS = [
    ("a module __getattr__", "def __getattr__(name):\n    return ''\n"),
    ("__del__", "class C:\n    def __del__(self):\n        pass\n"),
    ("__init_subclass__", "class C:\n    def __init_subclass__(cls):\n        pass\n"),
    ("__set_name__", "class D:\n    def __set_name__(self, owner, name):\n        pass\n"),
    ("__class_getitem__", "class C:\n    def __class_getitem__(cls, item):\n        pass\n"),
    ("__getattribute__", "class C:\n    def __getattribute__(self, name):\n        pass\n"),
    ("an async def", "async def __getattr__(name):\n    pass\n"),
    ("a class", "class __getattr__:\n    pass\n"),
    ("import as", "from functools import partial as __getattr__\n"),
    ("except as", "try:\n    pass\nexcept ValueError as __getattr__:\n    pass\n"),
    ("a match capture", "match 1:\n    case __getattr__:\n        pass\n"),
    ("a parameter", "def f(__getattr__):\n    pass\n"),
    ("global", "def f():\n    global __getattr__\n"),
]
# Underscore names an honest final uses, which must still pass.
HONEST = [
    ("a private attribute of its own", "class C:\n    def __init__(self):\n        self._evict = []\n"),
    ("the dunders it may define", "class C:\n    def __init__(self, k):\n        self.k = k\n\n"
     "    def __lt__(self, o):\n        return self.k < o.k\n\n    def __eq__(self, o):\n        return self.k == o.k\n\n"
     "    def __hash__(self):\n        return hash(self.k)\n"),
    ("namedtuple's _replace", "import collections\nP = collections.namedtuple('P', 'a b')\n"
     "q = P(1, 2)._replace(a=3)._asdict()\n"),
]


def static_mismatches():
    """Every name through which an allowed module reaches a module we did not allow, or a private of
    its own, is refused through an alias; the rebinding forms above are refused; honest code passes."""
    bad = 0
    for name, src in REBOUND:
        ok = bool(_bench.static_check(src))
        bad += not ok
        print(f"{'ok      ' if ok else 'MISMATCH'} static: module internal through {name} is refused", flush=True)
    for name, src in DUNDER_DEFS:
        ok = any("defining" in p for p in _bench.static_check(src))
        bad += not ok
        print(f"{'ok      ' if ok else 'MISMATCH'} static: a dunder bound by {name} is refused", flush=True)
    for name, src in HONEST:
        ok = not _bench.static_check(src)
        bad += not ok
        print(f"{'ok      ' if ok else 'MISMATCH'} static: {name} passes", flush=True)
    missed = sorted(a for a in _bench.REACH_ATTRS if not _bench.static_check(f"import math\nm = math\nx = m.{a}\n"))
    bad += bool(missed)
    print(f"{'ok      ' if not missed else 'MISMATCH'} static: {len(_bench.REACH_ATTRS)} reach names refused on an "
          f"alias{', missed ' + ', '.join(missed[:5]) if missed else ''}", flush=True)
    return bad


def score_unchecked(scorer, src):
    """Run a regex scorer in this process with the static check opened, so only its process split stands
    between the candidate and the matching. The patch lives in this test's memory; no candidate reaches it."""
    spec = importlib.util.spec_from_file_location("regex_score_unchecked", scorer)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as tmp:
        tmp.write(src)
    saved, argv, out = mod._bench.static_check, sys.argv, io.StringIO()
    mod._bench.static_check, sys.argv = (lambda s: []), ["score.py", tmp.name, "--split", "train"]
    try:
        with contextlib.redirect_stdout(out):
            mod.main()
    finally:
        mod._bench.static_check, sys.argv = saved, argv
        os.unlink(tmp.name)
    return json.loads(out.getvalue().strip().splitlines()[-1])


def matching_apart_mismatches(scorer=os.path.join(B, "regex", "score.py")):
    """With the static check open, the __getattr__ forge runs and must still score as the empty pattern it
    hands over: it fails if matching moves back beside the candidate (0.775 there)."""
    r = score_unchecked(scorer, GETATTR_FORGE)
    ok = bool(r.get("valid")) and r.get("score") is not None and r["score"] < 0.6
    print(f"{'ok      ' if ok else 'MISMATCH'} train  regex     __getattr__ forge, static check open: "
          f"valid={r.get('valid')} score={r.get('score')}", flush=True)
    return not ok


def main():
    only = set(sys.argv[1:]) or set(TASKS)
    bad = hash_seed_mismatches() + static_mismatches()
    if "regex" in only:
        bad += matching_apart_mismatches()
    for split, (task, name, src, want) in [("train", c) for c in CASES] + [("stress", c) for c in STRESS_CASES]:
        if task not in only:
            continue
        r = score(task, src, split)
        valid, s = bool(r.get("valid")), r.get("score")
        if want == "invalid":
            ok = not valid
        elif want == "valid":
            ok = valid
        else:
            ok = valid and s is not None and s < want[1]
        bad += not ok
        print(f"{'ok      ' if ok else 'MISMATCH'} {split:6} {task:9} {name}: valid={valid} score={s}", flush=True)
    print(f"{bad} mismatches")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
