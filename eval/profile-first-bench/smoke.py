"""Checks that every task runs and that every stub prints what the real program prints.

usage: python3 smoke.py [t01 t02 ...]
Tiny inputs, one run per variant, at nice 19. The run times it prints are not a measurement.
It also checks that the agent-visible folders name no stub, switch or answer.
"""
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lab"))
import runner  # noqa: E402

LEAK = re.compile(r"stub|decoy|ablat|shares\.json|manifest|harness|\blab/", re.I)


def leaks():
    found = []
    for root, _dirs, files in os.walk(runner.TASKS):
        for name in files:
            if name.endswith((".py", ".md", ".txt", ".csv")) and name != "vocab.txt":
                path = os.path.join(root, name)
                with open(path, encoding="utf-8", errors="replace") as f:
                    for n, line in enumerate(f, 1):
                        if LEAK.search(line):
                            found.append(f"{os.path.relpath(path, runner.BENCH)}:{n}: {line.strip()}")
    return found


def main():
    runner.lower_priority()
    m = runner.manifest()["tasks"]
    ids = sys.argv[1:] or sorted(m)
    failed = 0
    for tid in ids:
        spec = m[tid]
        (_label, gen, args), = runner.sizes(spec, tiny=True)
        work = os.path.join(runner.BENCH, ".work", "smoke", tid)
        runner.prepare(tid, work, gen)
        runner.run(runner.command(tid, spec, "none", args, record=True), work, "record")
        base = runner.run(runner.command(tid, spec, "none", args), work, "none")
        line = [f"{tid} none {base['wall']:.2f}s"]
        for variant in ["plain", *spec["components"]]:
            r = runner.run(runner.command(tid, spec, variant, args), work, variant)
            ok = r["sha"] == base["sha"]
            failed += not ok
            line.append(f"{variant} {r['wall']:.2f}s{'' if ok else ' OUTPUT DIFFERS'}")
        print("  ".join(line), flush=True)
    found = leaks()
    for f in found:
        print("possible leak:", f)
    if failed or found:
        raise SystemExit(f"{failed} variant(s) differ, {len(found)} possible leak(s)")
    print("ok: every stub matches its program's output")


if __name__ == "__main__":
    main()
