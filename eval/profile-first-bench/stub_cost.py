"""Times what a replay stub itself costs: loading its recording and replaying every call.

usage: python3 stub_cost.py [--rounds 7] [--tiny] TASK [TASK ...]

A share is 1 - T(C stubbed) / T(none), so whatever the stub costs is missing from C's share.
Per task: a fresh work copy at the stated input, one recording run, then, per component whose
stub replays a recording, ROUNDS fresh processes. Each installs the stub on a stand-in for the
program and calls it once per recorded call (a lazy replay is drained, a written text is written
to a buffer), timing the load and the calls together, start-up excluded. ReplayAfter's `before`
is skipped: draining or waiting on the input is the program's work, not the stub's. It prints the
median on the task's clock, and that median as points of the task's `none` time in shares.json:
how far the stub understates the share. Not counted: the extra garbage-collection work a loaded
recording causes while the program runs. Replace, Hook and hand-written stubs are skipped.
Run it on an idle machine; --tiny only checks that it runs.
"""
import argparse
import json
import os
import statistics
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lab"))
import runner  # noqa: E402

CHILD = r"""
import gc, importlib.util, io, sys, time, types
sys.path.insert(0, sys.argv[1])
import stubkit
spec = importlib.util.spec_from_file_location("_bench_stubs", sys.argv[2])
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
s = mod.STUBS[sys.argv[3]]
if not hasattr(s, "name") or not isinstance(s, (stubkit.Replay, stubkit.ReplayAfter, stubkit.ReplayLazy,
                                                  stubkit.ReplayWrite)):
    sys.exit(print("skip"))
ctx = stubkit.Ctx(".replay", False)
calls = 1 if isinstance(s, stubkit.ReplayWrite) else len(ctx.load(s.name))
if isinstance(s, stubkit.ReplayAfter):
    s.before = None
app = types.SimpleNamespace()
*path, attr = s.target.split(".")
owner = app
for p in path:
    setattr(owner, p, types.SimpleNamespace())
    owner = getattr(owner, p)
setattr(owner, attr, None)
gc.collect()
t, w = time.process_time(), time.perf_counter()
if getattr(s, "fake_module", None):
    s.before_import(ctx)
    fn = getattr(sys.modules[s.fake_module], attr)
else:
    s.after_import(app, ctx)
    fn = getattr(owner, attr)
if isinstance(s, stubkit.ReplayWrite):
    fn(None, io.StringIO())
elif isinstance(s, stubkit.ReplayLazy):
    for _ in range(calls):
        for _ in fn():
            pass
else:
    for _ in range(calls):
        fn()
print(time.process_time() - t, time.perf_counter() - w)
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tasks", nargs="+")
    ap.add_argument("--rounds", type=int, default=7)
    ap.add_argument("--tiny", action="store_true")
    a = ap.parse_args()
    runner.lower_priority()
    m = runner.manifest()["tasks"]
    with open(os.path.join(runner.BENCH, "shares.json"), encoding="utf-8") as f:
        measured = json.load(f)["tasks"]
    print(f"load {os.getloadavg()[0]:.2f}", flush=True)
    for tid in a.tasks:
        spec = m[tid]
        clock = spec.get("clock", "cpu")
        label, gen, args = runner.sizes(spec, a.tiny)[0]
        work = os.path.join(runner.BENCH, ".work", "stubcost", f"{tid}-{label}")
        runner.prepare(tid, work, gen)
        runner.run(runner.command(tid, spec, "none", args, record=True), work, "record")
        stubs = os.path.join(runner.LAB, "stubs", f"{tid}.py")
        base = measured.get(tid, {}).get(f"{clock}_secs", {}).get("none")
        for c in spec["components"]:
            cmd = [sys.executable, *runner.HARNESS_FLAGS, "-c", CHILD, runner.LAB, stubs, c]
            secs = []
            for _ in range(a.rounds):
                r = subprocess.run(cmd, cwd=work, capture_output=True, text=True, env=runner.CHILD_ENV)
                if r.returncode:
                    raise SystemExit(f"{tid} {c}: {r.stderr[-1000:]}")
                if r.stdout.strip() == "skip":
                    break
                cpu, wall = map(float, r.stdout.split())
                secs.append(wall if clock == "wall" else cpu)
            if not secs:
                print(f"{tid} {c}: not a stubkit replay (Replace, Hook or hand-written); not timed", flush=True)
                continue
            med = statistics.median(secs)
            pp = f", {100 * med / base:.1f} points of the {base}s run" if base and not a.tiny else ""
            print(f"{tid} {c} [{label}, {clock}]: {med:.4f}s{pp}", flush=True)


if __name__ == "__main__":
    main()
