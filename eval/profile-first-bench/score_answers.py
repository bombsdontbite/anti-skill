"""Scores agents' ANSWER.txt files against the measured shares.

usage: python3 score_answers.py ROOT [ROOT ...] [--shares shares.json] [--designed]
                                [--decoy-threshold 10] [--json scores.json]

Each folder under a ROOT that holds a TASK.md is one run, and its folder name is the task id.
Each ROOT is reported separately (one per arm, say plain-r1 and skill-r1) and then in total.
--designed scores against the designed hot spot instead of shares.json, with no share errors:
for a dry run before the shares are measured.
"""
import argparse
import ast
import json
import os
import re
import statistics
import sys

BENCH = os.path.dirname(os.path.abspath(__file__))
TASKS = os.path.join(BENCH, "tasks")
sys.path.insert(0, os.path.join(BENCH, "lab"))
from runner import task_digest  # noqa: E402
LINE = re.compile(r"^[\s>*`-]*(hotspot|cleared)\s*:\s*(.*)$", re.I)
FILE = re.compile(r"([\w./-]+\.py)\b")
NUMBER = r"(\d+(?:\.\d+)?)"


def parse_share(text):
    """'62%', '~62 %', '60-70%', '<1%' -> percent, or None."""
    t = text.replace(",", ".")
    m = re.search(NUMBER + r"\s*(?:-|–|to)\s*" + NUMBER + r"\s*%", t)
    if m:
        return (float(m.group(1)) + float(m.group(2))) / 2
    m = re.search(r"(<\s*)?" + NUMBER + r"\s*%", t)
    if m:
        return float(m.group(2)) / (2 if m.group(1) else 1)
    return None


def parse_answer(path):
    items = []
    with open(path, encoding="utf-8", errors="replace") as f:
        for raw in f:
            m = LINE.match(raw.rstrip())
            if not m:
                continue
            fields = [x.strip().strip("`") for x in m.group(2).split("|")]
            items.append({"kind": m.group(1).lower(), "where": fields[0],
                          "share": parse_share(fields[1]) if len(fields) > 1 else None})
    return items


def spans(tid, spec):
    """component -> [(file, first line, last line)] in the pristine task folder."""
    out, trees = {}, {}
    for comp, cs in spec["components"].items():
        out[comp] = []
        for w in cs["where"]:
            path = os.path.join(TASKS, tid, w["file"])
            with open(path, encoding="utf-8") as f:
                src = f.read()
            if "func" in w:
                tree = trees.setdefault(path, ast.parse(src))
                nodes = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == w["func"]]
                if not nodes:
                    raise SystemExit(f"{tid}: no function {w['func']} in {w['file']}")
                out[comp] += [(w["file"], n.lineno, n.end_lineno) for n in nodes]
            elif "text" in w:
                hits = [(w["file"], i, i) for i, line in enumerate(src.splitlines(), 1) if w["text"] in line]
                if not hits:
                    raise SystemExit(f"{tid}: no line with {w['text']!r} in {w['file']}")
                out[comp] += hits
            else:
                out[comp].append((w["file"], 1, 10**9))
    return out


def match(where, spec, comp_spans):
    """The component a location names, or None."""
    low = where.lower()
    fm = FILE.search(where)
    file = os.path.basename(fm.group(1)) if fm else None
    rest = where[fm.end():] if fm else where
    funcs = {w["func"]: c for c, cs in spec["components"].items() for w in cs["where"] if "func" in w
             and (file is None or w["file"] == file)}

    def at_line(m):
        line, f = int(m.group(1)), file or spec["entry"]
        hits = [(hi - lo, c) for c, ss in comp_spans.items() for fl, lo, hi in ss if fl == f and lo <= line <= hi]
        return min(hits)[1] if hits else None
    # The location's head (right after "file:") is what the agent named; the text after it is context,
    # so a function named there beats a line number later, and a line number there beats a function later.
    head = re.match(r"[\s:]*(?:(\d+)|([A-Za-z_][\w.]*))", rest)
    if head and head.group(1) and at_line(head):
        return at_line(head)
    if head and head.group(2):
        for ident in head.group(2).split("."):
            if ident in funcs:
                return funcs[ident]
    for ident in re.findall(r"[A-Za-z_]\w*", rest):
        if ident in funcs:
            return funcs[ident]
    lm = re.search(r"\blines?\s+(\d+)", where, re.I)
    if lm and at_line(lm):
        return at_line(lm)
    whole = {w["file"]: c for c, cs in spec["components"].items() for w in cs["where"]
             if set(w) == {"file"}}
    if file in whole and (not rest.strip(" :") or "<module>" in rest or "import" in low):
        return whole[file]
    scores = {c: sum(k in low for k in cs["keywords"]) for c, cs in spec["components"].items()}
    best = max(scores.values())
    winners = [c for c, s in scores.items() if s == best]
    return winners[0] if best and len(winners) == 1 else None


def pristine(run_dir, tid):
    changed = []
    for root, _dirs, files in os.walk(os.path.join(TASKS, tid)):
        for name in files:
            if name.endswith(".py"):
                src = os.path.join(root, name)
                rel = os.path.relpath(src, os.path.join(TASKS, tid))
                dst = os.path.join(run_dir, rel)
                with open(src, "rb") as a:
                    want = a.read()
                got = None
                if os.path.exists(dst):
                    with open(dst, "rb") as b:
                        got = b.read()
                if got != want:
                    changed.append(rel)
    return changed


def score_run(run_dir, tid, spec, truth, threshold):
    res = {"run": run_dir, "task": tid, "modified": pristine(run_dir, tid)}
    path = os.path.join(run_dir, "ANSWER.txt")
    if not os.path.exists(path):
        return {**res, "status": "missing"}
    items = parse_answer(path)
    hot = [i for i in items if i["kind"] == "hotspot"]
    if not hot:
        return {**res, "status": "invalid"}
    comp_spans = spans(tid, spec)
    for i in items:
        i["component"] = match(i["where"], spec, comp_spans)
    roles = {c: cs["role"] for c, cs in spec["components"].items()}
    shares = truth["shares"]
    first = hot[0]["component"]
    # Hot spot lines are a breakdown of the run, so a component's stated share is the sum of its lines.
    # A line that names nothing an earlier line of its component did not (a part listed after its whole,
    # or a repeat) is not a new part and is left out of the sum.
    stated, named_by = {}, {}
    for i in hot:
        c = i["component"]
        if not c or i["share"] is None:
            continue
        words = set(re.findall(r"[a-z_]\w*|\d+", i["where"].lower()))
        i["repeat"] = any(words <= w for w in named_by.get(c, []))
        named_by.setdefault(c, []).append(words)
        if not i["repeat"]:
            stated[c] = stated.get(c, 0) + i["share"]
    errors = [abs(v - 100 * shares[c]) for c, v in stated.items()] if shares else []
    top1_err = None
    if first == truth["top"] and shares and first in stated:
        top1_err = abs(stated[first] - 100 * shares[first])
    ranked = sorted(stated.values(), reverse=True)
    sum_top = max(stated, key=stated.get) if ranked and (len(ranked) == 1 or ranked[0] > ranked[1]) else None
    decoys = [c for c, r in roles.items() if r == "decoy"]
    named = [c for c in decoys if stated.get(c, 0) >= threshold
             or any(i["component"] == c and i["share"] is None for i in hot)]
    res.update(status="ok", top1=first == truth["top"], top1_by_sum=sum_top == truth["top"],
               stated_shares=stated,
               topk=truth["top"] in {i["component"] for i in hot},
               top1_share_error=top1_err, share_errors=errors,
               decoy_named=bool(named) if decoys else None,
               decoy_cleared=any(i["kind"] == "cleared" and i["component"] in decoys for i in items)
               if decoys else None,
               unmatched=[i["where"] for i in items if i["component"] is None],
               items=items)
    if truth.get("toy_top"):
        res["named_toy_top"] = first == truth["toy_top"]
    return res


def truths(manifest, shares_path, designed):
    out = {}
    data = None
    if not designed:
        if not os.path.exists(shares_path):
            raise SystemExit(f"{shares_path} not found: run measure_shares.py first, or pass --designed")
        with open(shares_path, encoding="utf-8") as f:
            data = json.load(f)["tasks"]
    for tid, spec in manifest["tasks"].items():
        if designed:
            hot = [c for c, cs in spec["components"].items() if cs["role"] == "hot"][0]
            out[tid] = {"top": hot, "shares": None}
            continue
        t = data.get(tid)
        if t is None or "error" in t:
            continue
        if t.get("task_digest") not in (None, task_digest(tid)):
            raise SystemExit(f"{tid}: shares were measured on different task files; measure again")
        if "clock" not in t:
            raise SystemExit(f"{tid}: shares were measured by wall time alone, before CPU-time shares; measure again")
        out[tid] = {"top": t["top"], "shares": {c: v["share"]["median"] for c, v in t["components"].items()},
                    "toy_top": t.get("toy", {}).get("top")}
    return out


def aggregate(rows):
    n = len(rows)
    ok = [r for r in rows if r["status"] == "ok"]
    decoy = [r for r in ok if r["decoy_named"] is not None]
    t1e = [r["top1_share_error"] for r in ok if r["top1_share_error"] is not None]
    errs = [e for r in ok for e in r["share_errors"]]

    def rate(xs, key):
        return round(sum(bool(r[key]) for r in xs) / len(xs), 3) if xs else None
    return {"runs": n, "missing": sum(r["status"] == "missing" for r in rows),
            "invalid": sum(r["status"] == "invalid" for r in rows),
            "top1_hit": round(sum(r.get("top1", False) for r in rows) / n, 3) if n else None,
            "top1_by_sum_hit": round(sum(r.get("top1_by_sum", False) for r in rows) / n, 3) if n else None,
            "topk_hit": round(sum(r.get("topk", False) for r in rows) / n, 3) if n else None,
            "top1_share_error_pp": round(statistics.mean(t1e), 1) if t1e else None,
            "mean_share_error_pp": round(statistics.mean(errs), 1) if errs else None,
            "decoy_named": rate(decoy, "decoy_named"), "decoy_cleared": rate(decoy, "decoy_cleared"),
            "unmatched_items": sum(len(r["unmatched"]) for r in ok),
            "modified_runs": sum(bool(r["modified"]) for r in rows)}


def fmt(x):
    return "-" if x is None else str(x)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("roots", nargs="+")
    ap.add_argument("--shares", default=os.path.join(BENCH, "shares.json"))
    ap.add_argument("--manifest", default=os.path.join(BENCH, "lab", "manifest.json"))
    ap.add_argument("--designed", action="store_true")
    ap.add_argument("--decoy-threshold", type=float, default=10.0,
                    help="a decoy listed as a hot spot counts when its stated share is at least this %%")
    ap.add_argument("--json")
    a = ap.parse_args()
    with open(a.manifest, encoding="utf-8") as f:
        manifest = json.load(f)
    truth = truths(manifest, a.shares, a.designed)
    report, every = {}, []
    for root in a.roots:
        rows = []
        for d, _dirs, files in sorted(os.walk(root)):
            if "TASK.md" not in files:
                continue
            tid = os.path.basename(d)
            if tid not in manifest["tasks"]:
                raise SystemExit(f"{d}: unknown task id {tid!r}")
            if tid not in truth:
                raise SystemExit(f"{d}: no measured share for {tid} in {a.shares}")
            rows.append(score_run(d, tid, manifest["tasks"][tid], truth[tid], a.decoy_threshold))
        if not rows:
            raise SystemExit(f"{root}: no runs (no folder with a TASK.md)")
        every += rows
        report[root] = {"total": aggregate(rows),
                        "by_task": {t: aggregate([r for r in rows if r["task"] == t])
                                    for t in sorted({r["task"] for r in rows})}}
    report["ALL"] = {"total": aggregate(every)}
    cols = ["runs", "top1_hit", "top1_by_sum_hit", "topk_hit", "top1_share_error_pp", "mean_share_error_pp",
            "decoy_named", "decoy_cleared", "unmatched_items", "missing", "invalid"]
    print("\t".join(["root", "task"] + cols))
    for root, r in report.items():
        for t, agg in r.get("by_task", {}).items():
            print("\t".join([root, t] + [fmt(agg[c]) for c in cols]))
        print("\t".join([root, "TOTAL"] + [fmt(r["total"][c]) for c in cols]))
    for tid in sorted({r["task"] for r in every if "named_toy_top" in r}):
        toy = [r for r in every if r["task"] == tid and "named_toy_top" in r]
        print(f"{tid} runs whose first hot spot is the toy-size top: {sum(r['named_toy_top'] for r in toy)}/{len(toy)}")
    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump({"report": report, "runs": every}, f, indent=2)


if __name__ == "__main__":
    main()
