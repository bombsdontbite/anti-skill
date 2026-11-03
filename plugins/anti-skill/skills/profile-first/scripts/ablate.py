#!/usr/bin/env python3
"""Time a command against a variant of it, interleaved in fresh processes, and report the drop.

  python3 ablate.py --name NAME --base "CMD" --variant "CMD" --base-cwd DIR --variant-cwd DIR
                    [--check PATH ...] [--repeats 7] [--stdin FILE] [--out profile/ablate]

For an ablation the variant runs a copy with one component stubbed out, and the drop,
1 - T(variant)/T(base), is that component's measured share of wall time. Any command works, on
macOS and Linux. Each arm runs in its own copy: --base-cwd and --variant-cwd may not be the working
directory, inside it or around it, nor overlap each other, since every run repeats its writes.
Both arms run with PYTHONHASHSEED=0 unless it is set, so a replay by call order holds.
Pairs alternate which arm runs first, after one untimed warm-up of each. Every run's stdout and each
--check file (relative to that arm's cwd, and rewritten by each run) must match the base warm-up's,
or timing stops, the verdict is "output differs" and the exit status is 3. The noise floor is the
widest of the two arms' ranges and the pairs' spread; the verdict is "drop" only when the lowest pair's drop clears it,
"rise" when the highest pair's is below minus it. The commands run without a shell: wrap a pipe or
a redirect in sh -c '...'. The result goes to OUT/NAME.json, every character of NAME outside
A-Za-z0-9._- as _; the line "written PATH" names it, and the last line printed is its JSON.
"""
import argparse
import hashlib
import json
import os
import re
import shlex
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

if os.name == "nt":
    sys.exit("ablate: needs macOS or Linux (resource, getloadavg); on Windows run it in WSL")
import resource  # noqa: E402  Unix only

ENV = {"PYTHONHASHSEED": "0", **os.environ}


def digest(f):
    h = hashlib.sha256()
    for chunk in iter(lambda: f.read(1 << 20), b""):
        h.update(chunk)
    return h.hexdigest()


def stat_of(path):
    try:
        st = os.stat(path)
    except OSError:
        return None
    return st.st_ino, st.st_mtime_ns, st.st_ctime_ns, st.st_size


def outputs(paths, before):
    """Each --check file's hash, or "not written" when the run left it absent or untouched (a stale copy)."""
    got = {}
    for c, p in paths.items():
        after = stat_of(p)
        if after is None or after == before[c] or not p.is_file():
            got[c] = "not written"
        else:
            with open(p, "rb") as f:
                got[c] = digest(f)
    return got


def run(cmd, cwd, stdin, timeout, checks=()):
    fin = open(stdin, "rb") if stdin else subprocess.DEVNULL
    try:
        with tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
            paths = {c: Path(cwd or ".") / c for c in checks}
            before = {c: stat_of(p) for c, p in paths.items()}
            r0, t0 = resource.getrusage(resource.RUSAGE_CHILDREN), time.perf_counter()
            try:
                p = subprocess.run(cmd, cwd=cwd, stdin=fin, stdout=out, stderr=err, timeout=timeout, env=ENV)
            except subprocess.TimeoutExpired:
                sys.exit(f"ablate: no result within {timeout:.0f} s: {' '.join(cmd)}")
            wall, r1 = time.perf_counter() - t0, resource.getrusage(resource.RUSAGE_CHILDREN)
            if p.returncode:
                err.seek(0)
                sys.exit(f"ablate: exit {p.returncode} from {' '.join(cmd)} in {cwd or '.'}\n"
                         + err.read().decode(errors="replace")[-2000:])
            out.seek(0)
            got = {"stdout": digest(out), **outputs(paths, before)}
    finally:
        if stdin:
            fin.close()
    return wall, r1.ru_utime - r0.ru_utime + r1.ru_stime - r0.ru_stime, got


def main():
    ap = argparse.ArgumentParser(usage=__doc__)
    ap.add_argument("--name", required=True,
                    help="the row the variant removes, as the table prints it, e.g. app.py:normalise")
    shell = "a command line, split like a shell's but run without one; wrap a pipe in sh -c '...'"
    ap.add_argument("--base", required=True, help=shell)
    ap.add_argument("--variant", required=True, help=shell)
    ap.add_argument("--base-cwd", required=True, help="a copy of the project, outside it")
    ap.add_argument("--variant-cwd", required=True, help="another copy, outside the project and apart from --base-cwd")
    ap.add_argument("--check", action="append", default=[], metavar="PATH",
                    help="a file the command writes, compared between the arms; repeatable")
    ap.add_argument("--repeats", type=int, default=7, help="interleaved pairs, at least 5 (21 for runs under 0.5 s)")
    ap.add_argument("--stdin")
    ap.add_argument("--timeout", type=float, default=900)
    ap.add_argument("--out", default="profile/ablate")
    a = ap.parse_args()
    if a.repeats < 5:
        sys.exit("ablate: --repeats must be at least 5")
    here = Path.cwd().resolve()
    base_dir, variant_dir = Path(a.base_cwd).resolve(), Path(a.variant_cwd).resolve()
    for flag, arm, raw, d in (("--base-cwd", "base", a.base_cwd, base_dir),
                              ("--variant-cwd", "variant", a.variant_cwd, variant_dir)):
        if here.is_relative_to(d) or d.is_relative_to(here):
            sys.exit(f"ablate: {flag} {raw} is the project or overlaps it; run the {arm} in a copy outside it, "
                     "since it runs 1 + --repeats times and its writes would land in the project")
    if base_dir.is_relative_to(variant_dir) or variant_dir.is_relative_to(base_dir):
        sys.exit(f"ablate: --base-cwd {a.base_cwd} and --variant-cwd {a.variant_cwd} are one folder or overlap; "
                 "run each arm in its own copy, since each repeats its writes and they would land in the other's")
    arms = {"base": (shlex.split(a.base), a.base_cwd), "variant": (shlex.split(a.variant), a.variant_cwd)}
    load = [os.getloadavg()[0]]
    warm = {k: run(*arms[k], a.stdin, a.timeout, a.check) for k in arms}
    missing = [c for c in a.check if warm["base"][2][c] == "not written"]
    if missing:
        sys.exit(f"ablate: the base did not write {', '.join(missing)} (a --check path is relative to the arm's cwd)")
    differs = [k for k in warm["base"][2] if warm["base"][2][k] != warm["variant"][2][k]]
    line = {"name": a.name, "base": a.base, "variant": a.variant, "variant_cwd": a.variant_cwd,
            "checks": a.check, "same_output": not differs, "differs": differs,
            "differs_at": "warm-up" if differs else None, "repeats": a.repeats}
    if not differs:
        if warm["base"][0] < 0.5 and a.repeats < 21:
            print(f"WARNING  base ran {warm['base'][0]:.3f} s: pass --repeats 21 for runs under 0.5 s")
        t = timed(a, arms, warm["base"][2], line)
        differs = line["differs"]
    if differs:
        line.update(same_output=False, base_s=None, variant_s=None, drop=None, interval=None, cpu_drop=None,
                    noise_floor=None, verdict="output differs", load=load)
        print(f"ablate   {a.name}: output DIFFERS from the base ({', '.join(differs)}) at {line['differs_at']}; "
              "no drop is claimed")
        return write(a, line)
    load.append(os.getloadavg()[0])

    bw, vw = [w for w, _ in t["base"]], [w for w, _ in t["variant"]]
    bc, vc = [c for _, c in t["base"]], [c for _, c in t["variant"]]
    ratios = [v / b for b, v in zip(bw, vw)]
    drop = 1 - statistics.median(vw) / statistics.median(bw)
    lo, hi = 1 - max(ratios), 1 - min(ratios)
    noise = max((max(x) - min(x)) / statistics.median(x) for x in (bw, vw))
    noise = max(noise, hi - lo)  # an A/A run must not clear it
    cpu_drop = 1 - statistics.median(vc) / max(statistics.median(bc), 1e-9)
    verdict = "drop" if lo > noise else "rise" if hi < -noise else "within noise"
    line.update(base_s=statistics.median(bw), variant_s=statistics.median(vw), drop=drop, interval=[lo, hi],
                cpu_drop=cpu_drop, noise_floor=noise, verdict=verdict, load=load)

    print(f"ablate   {a.name}: base {line['base_s']:.3f} s, variant {line['variant_s']:.3f} s, "
          f"{a.repeats} interleaved pairs")
    print(f"drop     {drop:.1%} of wall (pair range {lo:.1%} to {hi:.1%}), CPU drop {cpu_drop:.1%}, "
          f"noise floor {noise:.1%}")
    print(f"output   identical (stdout{''.join(', ' + c for c in a.check)})")
    print(f"load     {load[0]:.2f} -> {load[1]:.2f} on {os.cpu_count()} CPUs")
    write(a, line)


def timed(a, arms, want, line):
    """The interleaved pairs; stops at the first run whose output differs from the base warm-up's."""
    t = {"base": [], "variant": []}
    for i in range(a.repeats):
        for k in ("base", "variant") if i % 2 == 0 else ("variant", "base"):
            wall, cpu, got = run(*arms[k], a.stdin, a.timeout, a.check)
            bad = [c for c in want if got[c] != want[c]]
            if bad:
                line.update(differs=bad, differs_at=f"{k}, repeat {i + 1}")
                return t
            t[k].append((wall, cpu))
    return t


def write(a, line):
    print(f"verdict  {line['verdict']}")
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{re.sub(r'[^A-Za-z0-9._-]', '_', a.name)}.json"
    path.write_text(json.dumps(line) + "\n")
    print(f"written  {path}")
    print(json.dumps(line))
    if line["verdict"] == "output differs":
        sys.exit(3)


if __name__ == "__main__":
    main()
