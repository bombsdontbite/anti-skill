"""Cost and leak audit of one arms run, as JSON on stdout: one row per queued agent, and per arm.

usage: python3 audit.py <run-root>

Cost, turns, time and the result's subtype come from each agent's agent.json; `error_max_budget_usd`
is a run stopped at the MAX_USD cap. The leak check reads the agent's transcript
(~/.claude/projects/*/<session_id>.jsonl, subagents included) and lists every tool call that names
the repository, a stick's answer files or the harness, an absolute path outside the agent's own
folder (/dev/null, /dev/stdout and /dev/stderr aside), the home directory, or that runs gh, curl,
wget, a process listing or kill. Isolation is only a folder and a brief, so this is the check that
it held; a flagged run is read by hand before its score is trusted.
"""
import glob
import json
import os
import re
import sys
import subprocess
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def repo_names():
    """Names of this repository a call must not mention: AUDIT_REPO_NAMES (space-separated), else
    the checkout's <parent>/<folder> and the origin remote's owner and owner/name."""
    if "AUDIT_REPO_NAMES" in os.environ:
        return os.environ["AUDIT_REPO_NAMES"].split()
    names = [f"{ROOT.parent.name}/{ROOT.name}"]
    url = subprocess.run(["git", "-C", str(ROOT), "remote", "get-url", "origin"],
                         capture_output=True, text=True).stdout.strip()
    m = re.search(r"[:/]([\w.-]+)/([\w.-]+?)(?:\.git)?/?$", url)
    if m:
        names += [f"{m.group(1)}/{m.group(2)}", m.group(1)]
    return names


PATTERNS = [*(re.escape(n) for n in repo_names()), re.escape(ROOT.name) + r"\.git",
            r"answers\.json", r"measured\.json", r"calibration\.json", r"shares\.json", r"manifest\.json",
            r"loop-bench", r"make-scorer-bench", r"profile-first-bench", r"/gaming/", r"/naive/",
            r"\.harness", r"\.pristine", r"queue\.log", r"LOAD\.json", r"\.\./\.\.",
            r"\$\{?HOME\b", r"(?<![^\s\"'=(:])~(?=[/\s\"']|$)", r"\bpsutil\b", r"\bos\.kill\b",
            r"[\"'](?:gh|curl|wget|ps|pgrep|pkill|kill|killall|lsof)[\"']"]
COMMANDS = re.compile(r"(?:^|[;&|(`]|\$\(|\b(?:nice\s+-n\s*-?\d+|xargs|sudo|exec|env|timeout\s+\S+))\s*"
                      r"(gh|curl|wget|ps|pgrep|pkill|kill|killall|lsof|top|find\s+/)(?=\s|$|[;&|)])",
                      re.M)
ABSOLUTE = re.compile(r"(?<![^\s\"'=(,\[{])/[\w.~-][^\s\"'\\`;|&<>(){}\[\],]*")
HARMLESS = ("/dev/null", "/dev/stdout", "/dev/stderr")


def transcripts(session):
    base = os.path.expanduser("~/.claude/projects")
    return (glob.glob(os.path.join(base, "*", session + ".jsonl"))
            + glob.glob(os.path.join(base, "*", session, "**", "*.jsonl"), recursive=True))


def entries(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                continue
            msg = e.get("message") if isinstance(e, dict) else None
            content = msg.get("content") if isinstance(msg, dict) else None
            for block in content if isinstance(content, list) else []:
                if isinstance(block, dict):
                    yield e.get("timestamp"), block


def strings(x):
    if isinstance(x, str):
        yield x
    elif isinstance(x, dict):
        for v in x.values():
            yield from strings(v)
    elif isinstance(x, list):
        for v in x:
            yield from strings(v)


def epoch(ts):
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
    except (AttributeError, ValueError):
        return None


def bash_calls(session):
    """(start, end, command) per Bash call, in epoch seconds from the transcript's timestamps."""
    calls, ends = {}, {}
    for path in transcripts(session or "-"):
        for ts, b in entries(path):
            if b.get("type") == "tool_use" and b.get("name") == "Bash":
                calls[b.get("id")] = (epoch(ts), str((b.get("input") or {}).get("command", "")))
            elif b.get("type") == "tool_result":
                ends[b.get("tool_use_id")] = epoch(ts)
    return [(s, ends.get(i), cmd) for i, (s, cmd) in calls.items() if s is not None]


def why(name, inp, own):
    out = []
    for s in strings(inp):
        out += [p for p in PATTERNS if re.search(p, s)]
        out += [m.group(0) for m in ABSOLUTE.finditer(s)
                if m.group(0) not in HARMLESS and m.group(0) != own and not m.group(0).startswith(own + "/")]
        if name == "Bash":
            out += [m.group(1) for m in COMMANDS.finditer(s)]
    return list(dict.fromkeys(out))[:6]


def audit(root, q):
    agent_dir = os.path.join(root, q[0])
    row = {"agent": f"{q[2]}/r{q[3]}-{q[1]}", "id": q[0], "arm": q[2]}
    try:
        with open(os.path.join(agent_dir, "agent.json"), encoding="utf-8") as f:
            res = json.load(f)
    except (OSError, json.JSONDecodeError):
        res = None
    row["errors_set_aside"] = len(glob.glob(os.path.join(agent_dir, "agent.error.*.json")))
    if res is None:
        return {**row, "ran": False}
    row.update(ran=True, is_error=res.get("is_error"), subtype=res.get("subtype"),
               usd=res.get("total_cost_usd"), minutes=round((res.get("duration_ms") or 0) / 60000, 1),
               turns=res.get("num_turns"), session=res.get("session_id"))
    found = transcripts(res.get("session_id") or "-")
    row["transcripts"] = len(found)
    hits = []
    for path in found:
        for _, b in entries(path):
            if b.get("type") == "tool_use":
                w = why(b.get("name"), b.get("input"), agent_dir)
                if w:
                    hits.append({"why": w, "input": json.dumps(b.get("input"), ensure_ascii=False)[:300]})
    row["leak_flags"] = hits
    return row


def by_arm(rows):
    out = {}
    for arm in sorted({r["arm"] for r in rows}):
        rs = [r for r in rows if r["arm"] == arm]
        out[arm] = {"agents": len(rs), "ran": sum(r["ran"] for r in rs),
                    "usd": round(sum(r.get("usd") or 0 for r in rs), 2),
                    "cap_hits": sum(r.get("subtype") == "error_max_budget_usd" for r in rs),
                    "errors_set_aside": sum(r["errors_set_aside"] for r in rs),
                    "leak_flagged": sum(bool(r.get("leak_flags")) for r in rs)}
    return out


def main():
    root = os.path.abspath(sys.argv[1])
    with open(os.path.join(root, ".harness", "queue"), encoding="utf-8") as f:
        rows = [audit(root, line.split()) for line in f if line.strip() and not line.startswith("#")]
    json.dump({"by_arm": by_arm(rows), "agents": rows}, sys.stdout, indent=1)


if __name__ == "__main__":
    main()
