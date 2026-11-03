"""Leak check for loop-bench agents: did any agent touch files outside its workspace and its arm?

usage: audit_reads.py [--runs 12-24] [--out file.json]
Reads the agents' own session transcripts (~/.claude/projects/<cwd as dashes>/*.jsonl) and flags
every tool call that names a path outside the workspace and the arm folder, reads a scorer, names
the held-out seed variable, or uses the web. Prints one line per flag and a count per run.
"""
import argparse
import glob
import json
import os
import re

HOME = os.path.expanduser("~")
B = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser()
ap.add_argument("--runs", default="12-24")
ap.add_argument("--out")
a = ap.parse_args()
lo, hi = (int(x) for x in a.runs.split("-"))
SUSPECT = re.compile(r"LOOP_BENCH_TEST_SEED|heldout|--split test|score\.py|_bench\.py|/loop-bench/(?:cache|dedup|speedup|tsp|schedule|knapsack|coloring|binpack|regex)/")
PATH = re.compile(r"(?<![\w.])(/(?:Users|private|tmp|var|etc|opt)[^\s'\"`;|&<>()]*)")
ALLOWED_PREFIX = ("/tmp", "/private/tmp", "/private/var/folders", "/var/folders", "/dev/null", "/opt/homebrew", "/usr", "/bin")


def arms_of(run_dir):
    q = os.path.join(run_dir, "queue")
    out = set()
    if os.path.exists(q):
        for line in open(q):
            parts = line.split()
            if len(parts) > 1 and parts[1] != "-":
                for p in parts[1].split("+"):
                    out.add(os.path.dirname(p))
    return out


flags, seen = [], {}
for proj in sorted(glob.glob(f"{HOME}/.claude/projects/*-anti-skill-eval-loop-bench-runs-r*")):
    m = re.search(r"-runs-(r(\d+)[a-z]?)-(.+?)-(\w+)$", proj)
    if not m or not lo <= int(m.group(2)) <= hi:
        continue
    run = m.group(1)
    for tr in glob.glob(f"{proj}/*.jsonl"):
        ws = None
        calls = []
        for line in open(tr):
            try:
                e = json.loads(line)
            except ValueError:
                continue
            ws = ws or e.get("cwd")
            for blk in (e.get("message") or {}).get("content") or []:
                if isinstance(blk, dict) and blk.get("type") == "tool_use":
                    calls.append((blk["name"], blk.get("input") or {}))
        if not ws:
            continue
        allowed = {ws} | arms_of(os.path.join(B, "runs", run))
        seen[run] = seen.get(run, 0) + 1
        for name, inp in calls:
            text = "\n".join(str(v) for v in inp.values())  # raw strings, so newlines end paths
            why = []
            if name in ("WebSearch", "WebFetch"):
                why.append("web")
            if SUSPECT.search(text):
                why.append("scorer or held-out")
            # Agents cd into their own subfolders, so only three or more levels up can reach a scorer.
            rel = [os.path.normpath(os.path.join(ws, t)) for t in re.findall(r"(?<![\w/])((?:\.\./){3,}[^\s'\"`;|&<>()]*)", text)]
            for p in PATH.findall(text) + rel:
                p = p.rstrip(".,:")
                if not any(p == x or p.startswith(x + "/") for x in allowed) and not p.startswith(ALLOWED_PREFIX):
                    why.append(f"outside: {p}")
            if why:
                flags.append({"run": run, "workspace": ws, "tool": name, "why": sorted(set(why)), "input": text[:300].replace("\n", " ⏎ ")})
for f in flags:
    print(f"{f['workspace'].split('/runs/')[-1]:28} {f['tool']:8} {'; '.join(f['why'])[:120]}  | {f['input'][:140]}")
print(f"\n{len(flags)} flags in {sum(seen.values())} agent sessions over {len(seen)} run folders")
if a.out:
    json.dump(flags, open(a.out, "w"), indent=1)
