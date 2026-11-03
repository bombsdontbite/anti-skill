"""Where a laptop queue is: agents done, the ones running, the load gate or STOP, time left.

usage: python3 eval/arms/progress.py <run-dir>
  <run-dir> is an arms run (~/aruns/<run>, with .harness/queue and .harness/queue.log) or a
  loop-bench run (eval/loop-bench/runs/<run>, with queue, queue.log and a night's guard.log).
Reads only; safe while the queue runs.
"""
import datetime
import json
import os
import re
import statistics
import sys

LINE_RE = re.compile(r"^(\d\d):(\d\d):(\d\d) (.*)$")
GATE_RE = re.compile(r"load gate (\d+(?:\.\d+)?)")
JOBS_RE = re.compile(r"\bjobs=(\d+)$")  # loop-bench's start and queue-started lines when JOBS > 1
LOOP_BENCH_GATE = 6  # eval/loop-bench/run_queue.sh waits while int(1-minute load) > 6
# The night guard's lines, most specific first: (words in the line, what it means, queue paused).
GUARD = [("guarded queue done", "the guard is done", False),
         ("limit reset", "the usage limit reset and the queue resumed", False),
         ("waiting for the limit", "waiting for the usage limit to reset", True),
         ("limit seen", "a usage limit was hit and the queue was stopped", True)]


def layout(run_dir):
    """(kind, queue, log) for the run folder, or None when it holds no queue."""
    h = os.path.join(run_dir, ".harness")
    if os.path.isfile(os.path.join(h, "queue")):
        return "arms", os.path.join(h, "queue"), os.path.join(h, "queue.log")
    if os.path.isfile(os.path.join(run_dir, "queue")):
        return "loop-bench", os.path.join(run_dir, "queue"), os.path.join(run_dir, "queue.log")
    return None


def arm_label(arm):
    if arm == "-":
        return "plain"
    if os.path.basename(arm) == "SKILL.md":
        return os.path.basename(os.path.dirname(arm)) or arm
    return os.path.basename(arm)


def read_queue(kind, text):
    """[(id, case, arm)] in queue order; a repeated id is one agent, as the runner skips it."""
    out, seen = [], set()
    for line in text.splitlines():
        f = line.split()
        if not f or f[0].startswith("#") or f[0] in seen:
            continue
        if kind == "arms" and len(f) >= 3:
            out.append((f[0], f[1], f[2]))
        elif kind == "loop-bench":
            out.append((f[0], f[0].rsplit("/", 1)[-1], arm_label(f[1]) if len(f) > 1 else "?"))
        else:
            continue
        seen.add(f[0])
    return out


def finished_in_workspaces(kind, run_dir, ids):
    """Ids the runner would skip: a loop-bench workspace with final.py, an arms agent whose
    agent.json is a run that ended or stopped at the cost cap."""
    out = set()
    for i in ids:
        if kind == "loop-bench":
            if os.path.isfile(os.path.join(run_dir, i, "final.py")):
                out.add(i)
            continue
        try:
            with open(os.path.join(run_dir, i, "agent.json"), encoding="utf-8") as f:
                r = json.load(f)
        except (OSError, ValueError):
            continue
        if isinstance(r, dict) and (r.get("is_error") is False or r.get("subtype") == "error_max_budget_usd"):
            out.add(i)
    return out


def guard_state(lines, last_write):
    """(meaning, time or None, paused) of the guard log's last line, or None for an empty log."""
    last = next((line for line in reversed(lines) if line.strip()), None)
    if last is None:
        return None
    m = LINE_RE.match(last)
    text = m.group(4) if m else last.strip()
    when = timestamps(lines, last_write)[-1][0] if m else None
    for words, meaning, paused in GUARD:
        if words in text:
            return meaning, when, paused
    return f"last line: {text}", when, False


def timestamps(lines, last_write):
    """Dated (datetime, text) for the log's HH:MM:SS lines. The last line is dated by the log's
    last write, and each earlier one goes back a day whenever its clock time runs past the next."""
    parsed = [(m, m.group(4)) for m in map(LINE_RE.match, lines) if m]
    out, day, nxt = [], last_write.date(), None
    for m, text in reversed(parsed):
        t = datetime.time(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        when = datetime.datetime.combine(day, t)
        limit = nxt if nxt is not None else last_write + datetime.timedelta(minutes=1)
        if when > limit:
            day -= datetime.timedelta(days=1)
            when = datetime.datetime.combine(day, t)
        out.append((when, text))
        nxt = when
    return out[::-1]


def parse(kind, queue_text, log_lines, last_write, finished=frozenset()):
    """The queue's state from its log, with `finished` (from the workspaces) counted as done."""
    queue = read_queue(kind, queue_text)
    ids = {q[0] for q in queue}
    # running: {id: start time} in start order; jobs: how many run at once (loop-bench's jobs=N).
    s = {"kind": kind, "queue": queue, "done": set(), "durations": {}, "running": {}, "jobs": 1,
         "state": "not started", "at": None, "gate": None, "no_final": set(),
         "has_log": any(line.strip() for line in log_lines)}
    starts = {}
    for when, text in timestamps(log_lines, last_write):
        w = text.split()
        if not w:
            continue
        if text.startswith("queue started"):
            if (g := GATE_RE.search(text)):
                s["gate"] = float(g.group(1))
            j = JOBS_RE.search(text)
            s["jobs"] = int(j.group(1)) if j else 1
            s["running"], s["state"] = {}, "between agents"
        elif w[0] == "start" and len(w) > 1:
            starts[w[1]] = when
            j = JOBS_RE.search(text)
            s["jobs"] = int(j.group(1)) if j else 1
            # One at a time, a new start means the last one ended, even unlogged (a killed runner).
            if s["jobs"] == 1:
                s["running"] = {}
            s["running"].pop(w[1], None)
            s["running"][w[1]], s["state"] = when, "running"
        elif w[0] == "skip" and "(claimed" in text:
            continue  # another worker holds it, or a killed runner left its claim: not done
        elif w[0] in ("done", "skip") and len(w) > 1:
            if "final=no" in w:
                s["no_final"].add(w[1])
            elif w[1] in ids:
                s["done"].add(w[1])
            if w[0] == "done" and w[1] in starts:
                s["durations"][w[1]] = (when - starts[w[1]]).total_seconds() / 60
            s["running"].pop(w[1], None)
            if s["jobs"] == 1:
                s["running"], s["state"] = {}, "between agents"
            elif not s["state"].startswith("stopped"):
                # With JOBS > 1 an agent started before STOP still logs its done after it.
                s["state"] = "running" if s["running"] else "between agents"
        elif w[0] == "error" and len(w) > 1:
            s["done"].discard(w[1].rstrip(":"))
            s["running"], s["state"] = {}, "stopped after an error"
        elif text.startswith("STOP file found") or text.startswith("queue stopped"):
            # After an error the queue touches STOP itself, then logs "queue stopped".
            if s["state"] != "stopped after an error":
                s["state"] = "stopped by STOP"
            if kind == "arms" or s["jobs"] == 1 or text.startswith("queue stopped"):
                s["running"] = {}
        elif text.startswith("queue finished"):
            # loop-bench's runner logs this after a STOP too, once every agent has ended.
            s["running"] = {}
            if not s["state"].startswith("stopped"):
                s["state"] = "finished"
        elif "claude -p failed" in text:
            s["running"], s["state"] = {}, "not started: the sign-in probe failed"
        else:
            continue
        s["at"] = when
    # A running agent's final.py may be a draft until the log says done.
    s["done"] = (s["done"] | (set(finished) & ids)) - set(s["running"])
    s["no_final"] -= s["done"] | set(s["running"])
    if s["has_log"] and ids and s["done"] >= ids:
        s["state"] = "finished"
    return s


def fmt_min(m):
    return f"{m:.0f} min" if m < 90 else f"{m / 60:.1f} h"


def report(run_dir, s, now, load, stop_file, guard=None):
    q, done = s["queue"], len(s["done"])
    total = len(q)
    lines = [f"{os.path.basename(os.path.normpath(run_dir))} ({s['kind']} queue)",
             f"done {done}/{total} ({100 * done / total:.0f}%)" if total else "the queue is empty"]
    if s["no_final"]:
        names = sorted(s["no_final"])
        more = f" and {len(names) - 5} more" if len(names) > 5 else ""
        lines.append(f"ended without final.py: {', '.join(names[:5])}{more}")
    elapsed = []
    if s["running"]:
        for r, since in s["running"].items():
            case, arm = next(((c, a) for i, c, a in q if i == r), ("?", "?"))
            elapsed.append((now - since).total_seconds() / 60)
            lines.append(f"running: {r} {case} {arm}, {elapsed[-1]:.0f} min since start (by the log)")
        if s["state"].startswith("stopped"):
            lines.append(f"state: {s['state']} at {s['at']:%H:%M:%S}; no new start, the agents above run to their end")
    elif not s["has_log"]:
        lines.append("state: finished (no queue.log; counted from the workspaces)" if total and done == total
                     else "state: not started (no queue.log)")
    else:
        at = ""
        if s["at"]:
            ago = (now - s["at"]).total_seconds() / 60
            at = f" at {s['at']:%H:%M:%S}" + (f" ({fmt_min(ago)} ago)" if ago >= 1 else "")
        lines.append(f"state: {s['state']}{at}")
    paused = False
    if guard:
        meaning, when, paused = guard
        lines.append(f"guard: {meaning}" + (f" at {when:%H:%M:%S}" if when else ""))
    gate = s["gate"] if s["gate"] is not None else (LOOP_BENCH_GATE if s["kind"] == "loop-bench" else None)
    if s["state"] == "between agents" and gate is not None and load is not None and not (stop_file or paused):
        over = int(load) > gate if s["kind"] == "loop-bench" else load > gate
        lines.append(f"load {load:.2f} against the gate {gate:g}: "
                     + ("waiting on the load gate" if over else "under the gate, the next agent is starting"))
    if stop_file:
        lines.append("STOP file present: the queue stops before its next agent")
    d = list(s["durations"].values())
    if d:
        med = statistics.median(d)
        lines.append(f"median {med:.1f} min per finished agent ({len(d)} timed)")
        left = total - done - len(s["running"])
        if (s["state"] in ("running", "between agents") or paused) and left >= 0 and done < total:
            est = (left * med + sum(max(med - e, 0) for e in elapsed)) / s["jobs"]
            after = ", after the limit resets" if paused else ""
            jobs = f", {s['jobs']} at a time" if s["jobs"] > 1 else ""
            lines.append(f"left ≈ {fmt_min(est)} (estimate: {total - done} agent(s) at the median{jobs}{after})")
    elif done < total:
        lines.append("no agent timed in the log yet: no estimate")
    return "\n".join(lines)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    run_dir = os.path.abspath(os.path.expanduser(argv[0]))
    lay = layout(run_dir)
    if not lay:
        print(f"progress.py: no queue in {run_dir} (.harness/queue or queue)", file=sys.stderr)
        return 2
    kind, queue_path, log_path = lay
    with open(queue_path, encoding="utf-8", errors="replace") as f:
        queue_text = f.read()
    log_lines, last_write = read_log(log_path)
    finished = finished_in_workspaces(kind, run_dir, [q[0] for q in read_queue(kind, queue_text)])
    s = parse(kind, queue_text, log_lines, last_write, finished)
    if s["gate"] is None and kind == "arms":
        try:
            with open(os.path.join(run_dir, ".harness", "LOAD_MAX"), encoding="utf-8") as f:
                s["gate"] = float(f.read().strip())
        except (OSError, ValueError):
            pass
    guard = None
    if kind == "loop-bench":
        guard = guard_state(*read_log(os.path.join(run_dir, "guard.log")))
    try:
        load = os.getloadavg()[0]
    except OSError:
        load = None
    print(report(run_dir, s, datetime.datetime.now(), load, os.path.exists(os.path.join(run_dir, "STOP")), guard))
    return 0


def read_log(path):
    """(lines, time of the last write); no lines when the file does not exist."""
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            lines = f.read().splitlines()
        return lines, datetime.datetime.fromtimestamp(os.stat(path).st_mtime)
    except FileNotFoundError:
        return [], datetime.datetime.now()


if __name__ == "__main__":
    sys.exit(main())
