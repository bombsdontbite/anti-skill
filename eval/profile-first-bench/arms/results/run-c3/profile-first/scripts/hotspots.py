#!/usr/bin/env python3
"""Profile a Python entry point in fresh processes and print where its time goes.

Prints wall and CPU medians, I/O wait (wall - CPU), import time from -X importtime, and two
tables: Python frames by a time-weighted stdlib sampler, self time charged to the nearest frame
under the working directory, beside cProfile's share; and cProfile's self time, which also covers
C calls. Everything goes to OUT/hotspots.json. A first argument after -- named python* is the
interpreter. --compare OLD.json prints old against new shares. With --focus NAME it is the stop
gate: exit 0 only on the same command, interpreter, working directory, input (the file and folder
arguments, --input, stdin), environment and --check names, with stdout and every --check file
unchanged, NAME's share below the old beyond sampling noise (a name gone from the new profile
counts as 0), the wall median below the old by more than either side's run range (NAME may be
"imports"), and each profiled run about as long as the plain runs. Python 3.9+, stdlib only, never
needs root; macOS and Linux.
"""
import argparse
import atexit
import collections
import cProfile
import functools
import hashlib
import json
import math
import os
import pkgutil  # noqa: F401  runpy imports it lazily; load it before the profiler starts
import pstats
import runpy
import shlex
import shutil
import signal
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

if os.name == "nt":
    sys.exit("hotspots: needs macOS or Linux (SIGALRM, setitimer, resource); on Windows run it in WSL")
import resource  # noqa: E402  Unix only

USAGE = "%(prog)s [options] -- [python] script.py ARGS...   (or: -- [python] -m package.module ARGS...)"

HERE = str(Path(__file__).resolve())
WRAPPERS = {HERE, runpy.__file__, "<frozen runpy>"}
SLOWED = 1.3  # tracing slowed the run this much: enough tiny calls to inflate cProfile's shares


def child(mode, out, target):
    """Runs in a fresh interpreter: the target under cProfile or the sampler."""
    if target[0] == "-m":
        sys.argv, sys.path[0] = [target[1], *target[2:]], os.getcwd()
        run = lambda: runpy.run_module(target[1], run_name="__main__", alter_sys=True)  # noqa: E731
    else:
        sys.argv, sys.path[0] = list(target), str(Path(target[0]).resolve().parent)
        run = lambda: runpy.run_path(target[0], run_name="__main__")  # noqa: E731
    code = 0

    def guarded():
        nonlocal code
        try:
            run()
        except SystemExit as e:
            code = e.code if isinstance(e.code, int) else int(e.code is not None)

    if mode == "sample":
        # a timer signal, not a sleeping thread: that thread's ticks depend on timer slack and the GIL
        interval = float(os.environ.get("HOTSPOTS_INTERVAL", "0.002"))
        # a tick that wakes the main thread restarts its wait for the GIL; a shorter switch interval
        # lets that wait run out between ticks, or a busy worker thread starves main
        sys.setswitchinterval(min(sys.getswitchinterval(), interval / 2))
        count, done = 0, False
        wall, cpu = collections.Counter(), collections.Counter()

        def sample(_sig, f):
            # runs between bytecodes, so a C or blocking call delays it; the stack it then sees is the
            # one that waited, and elapsed-time weighting charges it the whole delay
            nonlocal count, last, last_cpu
            if done:
                return
            now, now_cpu, st = time.perf_counter(), time.process_time(), []
            while f is not None:
                c = f.f_code
                st.append((c.co_filename, c.co_firstlineno, getattr(c, "co_qualname", c.co_name)))
                f = f.f_back
            wall[tuple(st)] += now - last
            cpu[tuple(st)] += now_cpu - last_cpu
            last, last_cpu, count = now, now_cpu, count + 1

        signal.signal(signal.SIGALRM, sample)
        # SA_RESTART restarts a read; a sleep, poll or select in C code still returns early (main() warns)
        signal.siginterrupt(signal.SIGALRM, False)
        t0 = last = time.perf_counter()
        last_cpu = time.process_time()
        signal.setitimer(signal.ITIMER_REAL, interval, interval)
        try:
            guarded()
        finally:
            timer = signal.setitimer(signal.ITIMER_REAL, 0)
            done, elapsed = True, time.perf_counter() - t0
            disturbed = [why for why, bad in [
                ("the target replaced the SIGALRM handler", signal.getsignal(signal.SIGALRM) is not sample),
                ("the target reset the ITIMER_REAL timer (signal.alarm or setitimer)", abs(timer[1] - interval) > 1e-5),
                ("the target blocks SIGALRM", signal.SIGALRM in signal.pthread_sigmask(signal.SIG_BLOCK, []))] if bad]
            Path(out).write_text(json.dumps({"interval": interval, "count": count, "elapsed": elapsed,
                                             "disturbed": "; ".join(disturbed),
                                             "stacks": [[k, w, cpu[k]] for k, w in wall.items()]}))
    else:
        prof = cProfile.Profile(time.perf_counter)
        prof.enable()
        try:
            guarded()
        finally:
            prof.disable()
            prof.dump_stats(out)
    sys.stdout.flush()
    sys.exit(code)


def run_once(cmd, stdin, timeout, checks=()):
    fin = open(stdin, "rb") if stdin else subprocess.DEVNULL
    try:
        with tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
            before = {c: stat_of(c) for c in checks}
            r0, t0 = resource.getrusage(resource.RUSAGE_CHILDREN), time.perf_counter()
            try:
                p = subprocess.run(cmd, stdin=fin, stdout=out, stderr=err, timeout=timeout)
            except subprocess.TimeoutExpired:
                sys.exit(f"hotspots: no result within {timeout:.0f} s: {' '.join(cmd)}")
            wall, r1 = time.perf_counter() - t0, resource.getrusage(resource.RUSAGE_CHILDREN)
            out.seek(0)
            digest = digest_of(out)
            err.seek(0)
            errtext = err.read().decode(errors="replace")
    finally:
        if stdin:
            fin.close()
    if p.returncode:
        sys.exit(f"hotspots: exit {p.returncode} from {' '.join(cmd)}\n{errtext[-2000:]}")
    cpu = r1.ru_utime - r0.ru_utime + r1.ru_stime - r0.ru_stime
    return wall, cpu, digest, errtext, {c: written(c, before[c]) for c in checks}


def digest_of(f):
    h = hashlib.sha256()  # hashlib.file_digest is 3.11+; macOS ships 3.9
    for chunk in iter(lambda: f.read(1 << 20), b""):
        h.update(chunk)
    return h.hexdigest()[:16]


def sha(path):
    with open(path, "rb") as f:
        return digest_of(f)


def input_sha(path, cap):
    """sha(path) while the content fits in cap bytes; past it, or unreadable, a file counts by size and mtime."""
    p, left, partial, h = Path(path), cap, False, hashlib.sha256()
    if p.is_file() and p.stat().st_size <= cap:
        try:
            return sha(p), False
        except OSError:
            pass
    for f in sorted(q for q in p.rglob("*") if q.is_file()) if p.is_dir() else [p]:
        st, rel = f.stat(), os.fsencode(f.relative_to(p) if p.is_dir() else f.name)  # a name may not be UTF-8
        digest = None
        if st.st_size <= left:
            try:
                digest = sha(f)
                left -= st.st_size
            except OSError:
                pass
        partial = partial or digest is None
        h.update(rel + f"\0{digest or f'{st.st_size}:{st.st_mtime_ns}'}\0".encode())
    return h.hexdigest()[:16], partial


def stat_of(path):
    try:
        st = os.stat(path)
    except OSError:
        return None
    return st.st_ino, st.st_mtime_ns, st.st_ctime_ns, st.st_size


def written(path, before):
    """The file's hash, or "not written" when the run left it absent or untouched (stale from an earlier run)."""
    after = stat_of(path)
    return "not written" if after is None or after == before or not Path(path).is_file() else sha(path)


def env_record(names):
    """Hashes, not values, of PYTHON* variables and the --env names: what the target reads."""
    keys = sorted({k for k in os.environ if k.startswith("PYTHON")} | set(names))
    return {k: hashlib.sha256(os.environ[k].encode()).hexdigest()[:16] if k in os.environ else None for k in keys}


def parse_importtime(err):
    """Top-level cumulative import times, in seconds, by module (nested imports sit inside them)."""
    top = {}
    for line in err.splitlines():
        parts = line.removeprefix("import time:").split("|")
        if not line.startswith("import time:") or len(parts) != 3 or not parts[1].strip().isdigit():
            continue
        name = parts[2][1:]
        if not name.startswith(" "):
            top[name.strip()] = top.get(name.strip(), 0) + int(parts[1]) / 1e6
    return top


def short(fn):
    if fn.startswith("<") or fn == "~":
        return fn
    p = Path(fn)
    try:
        return str(p.resolve().relative_to(Path.cwd().resolve()))
    except ValueError:
        parts = p.parts
        if "site-packages" in parts:
            return "/".join(parts[parts.index("site-packages") + 1:])
        return "/".join(parts[-2:])


def label(fn, name):
    return name if fn == "~" else f"{short(fn)}:{name}"


@functools.cache
def mine(fn):
    """True for a file under the working directory and outside any site-packages."""
    p = None if fn.startswith("<") else Path(fn).resolve()
    return p is not None and p.is_relative_to(Path.cwd().resolve()) and "site-packages" not in p.parts


def inflated(cp, sampled, count, slowdown):
    """Tracing charges every call, so only a run it slowed down can make many tiny calls look hot."""
    return cp is not None and count >= 100 and slowdown >= SLOWED and cp - sampled > 0.10 and cp > 1.5 * sampled


def cprofile_key(loc):
    """cProfile names a function by co_name; the sampler keeps co_qualname where it exists (3.11+)."""
    return loc[0], loc[1], loc[2].rpartition(".")[2]


def analyse(out, slowdown):
    stats = pstats.Stats(str(out / "cprofile_wall.prof"))
    tw, W = stats.total_tt or 1e-9, {k: (v[1], v[2], v[3]) for k, v in stats.stats.items()}
    d = json.loads((out / "samples.json").read_text())
    n, total = d["count"], sum(w for _, w, _ in d["stacks"]) or 1e-9
    # a delayed tick saw a stack that could not change while it waited, so each interval it covers
    # counts; not once the target took the timer over
    eff = n if d["disturbed"] else max(n, total / d["interval"])
    incl, incl_cpu, own, imp = collections.Counter(), collections.Counter(), collections.Counter(), 0.0
    for st, w, c in d["stacks"]:
        # file and first line alone merge a def on line 1 with its <module>; the name tells them apart
        frames = [tuple(f) for f in st if f[0] not in WRAPPERS]
        if frames:
            own[next((f for f in frames if mine(f[0])), frames[0])] += w
        imp += w * any(f[0].startswith("<frozen importlib") for f in frames)
        for loc in set(frames):
            incl[loc] += w
            incl_cpu[loc] += c
    qual = {cprofile_key(loc): loc[2] for loc in incl}
    base = {k: label(k[0], qual.get(k, k[2])) for k in set(qual) | set(W)}
    repeats = collections.Counter(base.values())

    def name(k):  # 3.9 calls every listcomp in a file <listcomp>: a shared label gets its line
        return base[k] + f"@{k[1]}" * (repeats[base[k]] > 1 and k[0] != "~")

    rows = []
    for loc, w in incl.items():
        p, cw = w / total, W.get(cprofile_key(loc))
        cp = cw and cw[2] / tw
        rows.append({"name": name(cprofile_key(loc)), "at": f"{short(loc[0])}:{loc[1]}", "profile_share": p,
                     "se": math.sqrt(p * (1 - p) / max(eff, 1)), "self": own[loc] / total, "cp_cum": cp,
                     "calls": cw and cw[0],
                     "flags": ["cProfile inflates"] * inflated(cp, p, eff, slowdown)
                     + ["waits"] * (w - incl_cpu[loc] > max(0.5 * w, 0.05 * total))})
    rows.sort(key=lambda r: (-r["self"], -r["profile_share"]))
    share = {r["name"]: r["profile_share"] for r in rows}
    by_self = []
    for k, (calls, tt, ct) in sorted(W.items(), key=lambda kv: -kv[1][1]):
        if tt / tw < 0.001:
            break
        if k[0] in WRAPPERS:
            continue
        r = {"name": name(k), "calls": calls, "self_wall": tt / tw, "cum_wall": ct / tw,
             "flags": ["cProfile inflates"] * (slowdown >= SLOWED and calls >= 10_000 and tt / calls < 1e-5)}
        if k[0] == "~":  # a C call: the sampler has no frame for it
            share.setdefault(r["name"], r["self_wall"])
        by_self.append(r)
    seen = sorted({name(k) for k in W})
    return {"samples": n, "samples_effective": eff, "sampled_s": total, "interval": d["interval"],
            "sampler_elapsed_s": d["elapsed"], "sampler_disturbed": d["disturbed"], "import_share_sampled": imp / total,
            "frames": rows, "by_self": by_self, "profile_share": share, "seen": seen, "cprofile_total_s": tw}


def pct(x):
    return "    —" if x is None else f"{100 * x:5.1f}%"


def stem(name):
    head, _, line = name.rpartition("@")
    return head if line.isdigit() else name


def lookup(doc, name, line=None):
    if name not in doc["profile_share"] and line:  # a namesake added or removed moves the @line suffix
        name = next((r["name"] for r in doc["frames"]
                     if stem(r["name"]) == stem(name) and r["at"].rpartition(":")[2] == line), name)
    if name in doc["profile_share"]:
        return doc["profile_share"][name], next((r["se"] for r in doc["frames"] if r["name"] == name), 0.0)
    file, _, func = name.rpartition(":")
    if name in doc["seen"] or f"{file}:{func.rpartition('.')[2]}" in doc["seen"]:
        return 0.0, 0.0  # still called, but below every table
    return None


def paths(d):
    """./out.csv and out.csv are one file."""
    return {os.path.normpath(k): v for k, v in d.items()}


def differing(old, new):
    keys = sorted(set(old) | set(new))
    return [k for k in keys if old.get(k) != new.get(k)]


def compare(old, new, path, focus):
    oi, ni = old["input"], new["input"]
    partial = sorted({os.path.normpath(k) for k in oi.get("partial", []) + ni.get("partial", [])})
    of, nf = paths(old.get("outputs", {})), paths(new.get("outputs", {}))
    diff = ([k for k in ("command", "python", "cwd") if old.get(k) != new.get(k)]
            + ["stdin"] * (oi["stdin_sha"] != ni["stdin_sha"])
            + ["--hash-mb"] * ("hash_mb" in oi and "hash_mb" in ni and oi["hash_mb"] != ni["hash_mb"])
            + [f"input {k}" for k in differing(paths(oi["files"]), paths(ni["files"]))]
            + [f"env {k}" for k in differing(old.get("env", {}), new.get("env", {}))]
            + [f"--check {k} (only in the {'old' if k in of else 'new'} run)" for k in sorted(set(of) ^ set(nf))])
    outs = [("stdout", old["stdout_sha"], new["stdout_sha"])] + [(k, of[k], nf[k]) for k in sorted(set(of) & set(nf))]
    varies = [k for k, o, n in outs if len(o or []) > 1 or len(n or []) > 1]
    changed = [k for k, o, n in outs if o != n]
    print(f"\ncompare with {path}: wall {old['wall_s']:.3f} s -> {new['wall_s']:.3f} s"
          + (f"   (different: {', '.join(diff)})" if diff else "") + (f"   (output changed: {', '.join(changed)})" if changed else ""))
    names = [r["name"] for r in old["frames"][:5] + new["frames"][:5]] + [focus] * bool(focus)
    at, shown = {r["name"]: r["at"].rpartition(":")[2] for r in old["frames"] + new["frames"]}, set()
    for name in dict.fromkeys(names):
        if (stem(name), at.get(name)) in shown:
            continue
        shown.add((stem(name), at.get(name)))
        b, a = lookup(old, name, at.get(name)), lookup(new, name, at.get(name))
        print(f"  {pct(b and b[0])} -> {pct(a and a[0])}  {name}")
    if not focus:
        return None
    line = next((r["at"].rpartition(":")[2] for r in old["frames"] if r["name"] == focus), None)
    b, a = lookup(old, focus), lookup(new, focus, line)
    if b is not None and a is None:
        a = (0.0, 0.0)  # the change removed it: nothing left to sample
    # a renamed body drops the share, not the wall; either side's range is noise, as in ablate.py
    spread = max(max(r) - min(r) for r in (old["wall_runs_s"], new["wall_runs_s"]))
    gate = {"name": focus, "share_before": b and b[0], "share_after": a and a[0],
            "seconds_before": b and b[0] * old["wall_s"], "seconds_after": a and a[0] * new["wall_s"],
            "noise": b and a and max(0.02, 2 * math.hypot(b[1], a[1])),
            "wall_before_s": old["wall_s"], "wall_after_s": new["wall_s"], "wall_range_s": spread,
            "same_input": not diff, "input_partial": partial, "same_output": not changed and not varies,
            "reason": "", "passed": False}
    if diff:
        why = "unclear: different " + ", ".join(diff)
    elif varies:
        why = "unclear: output varies between runs (" + ", ".join(varies) + "), so a change to it cannot be seen"
    elif changed:
        why = "output changed: " + ", ".join(changed)
    elif b is None:
        why = "unclear: name not in the old profile"
    elif old.get("unlike_plain") or new.get("unlike_plain"):
        why = ("unclear: a profiled run was unlike the plain runs, so its shares are not this run's; "
               "time old against new with ablate.py")
    else:
        sec_b, sec_a, noise = gate["seconds_before"], gate["seconds_after"], gate["noise"]
        failed = (["share not beyond noise"] * (a[0] >= b[0] - noise)
                  + ["wall within range"] * (new["wall_s"] >= old["wall_s"] - spread))
        gate["passed"] = not failed
        why = (", ".join(failed) + ": ") * bool(failed) + (
            f"share {pct(b[0])} -> {pct(a[0])} (noise {pct(noise)}), ~{sec_b:.3f} s -> ~{sec_a:.3f} s; "
            f"wall {old['wall_s']:.3f} s -> {new['wall_s']:.3f} s (range {spread:.3f} s)")
    if partial:  # a file past --hash-mb that changed but kept its size and mtime goes unseen
        why += f"; input check partial for {', '.join(partial)}: files past --hash-mb compared by size and mtime"
    gate["reason"] = why
    print(f"GATE {'pass' if gate['passed'] else 'fail'}: {focus}: {why}")
    return gate


def main():
    argv = sys.argv[1:]
    if argv[:1] == ["--_child"]:
        return child(argv[1], argv[2], argv[4:])
    ap = argparse.ArgumentParser(usage=USAGE, description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repeat", type=int, default=3, help="fresh unprofiled runs for wall and CPU (7 for runs under 0.5 s)")
    ap.add_argument("--top", type=int, default=12)
    ap.add_argument("--out", default="profile")
    ap.add_argument("--stdin", help="file fed to the target's stdin on every run")
    ap.add_argument("--hash-mb", type=float, default=256,
                    help="content hashed per input path; past it a file counts by size and mtime (default 256)")
    ap.add_argument("--input", action="append", default=[], metavar="PATH",
                    help="an input file or folder the arguments do not name (those are hashed already); repeatable")
    ap.add_argument("--env", action="append", default=[], metavar="NAME",
                    help="an environment variable the target reads (PYTHON* are always recorded); repeatable")
    ap.add_argument("--check", action="append", default=[], metavar="PATH",
                    help="a file the target writes; its hash after each run is part of the output; repeatable")
    ap.add_argument("--input-desc", default="", help="what the input is and how big, for the report")
    ap.add_argument("--python", default=sys.executable)
    ap.add_argument("--timeout", type=float, default=900, help="seconds per run (about 5x the first run if it may hang)")
    ap.add_argument("--compare", help="an earlier hotspots.json")
    ap.add_argument("--focus", help="with --compare: the named hot spot the stop gate checks")
    if "--" not in argv:
        ap.parse_args(argv)  # prints --help with the options
        ap.error("after -- give a Python script or -m module, then its arguments")
    i = argv.index("--")
    a, target = ap.parse_args(argv[:i]), argv[i + 1:]
    if target and Path(target[0]).name.startswith("python") and not target[0].endswith(".py"):
        a.python, target = target[0], target[1:]
    if not target or (target[0] == "-m" and len(target) < 2) or (target[0] != "-m" and not Path(target[0]).is_file()):
        sys.exit("hotspots: after -- give a Python script or -m module, then its arguments")
    if a.focus and not a.compare:
        sys.exit("hotspots: --focus needs --compare OLD.json")
    out, py, load = Path(a.out), a.python, [os.getloadavg()[0]]
    raw_names = ("cprofile_wall.prof", "samples.json", "importtime.txt")
    if (out / "__init__.py").exists() or (
            any((out / f).exists() for f in raw_names) and not (out / "hotspots.json").is_file()):
        sys.exit(f"hotspots: {out}/ is not profile-first's (a package, or its file names taken); pass --out another folder")
    out.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="hotspots-"))  # the raw files reach OUT only with hotspots.json
    atexit.register(shutil.rmtree, tmp, True)
    for p in a.input:
        if not Path(p).exists():
            sys.exit(f"hotspots: --input {p} does not exist")
    # hashed before any run, so a file the target writes is not taken for input
    written = {Path(c).resolve() for c in a.check} | {out.resolve()}

    def is_input(t):  # a folder that holds what the target or this script writes changes on every run
        p = Path(t).resolve()
        return p.exists() and p not in written and (
            p.is_file() or t in a.input or not any(w.is_relative_to(p) for w in written))

    hashed = {os.path.normpath(t): input_sha(t, a.hash_mb * (1 << 20))
              for t in dict.fromkeys(target[1:] + a.input) if is_input(t)}
    files, partial = {k: v[0] for k, v in hashed.items()}, sorted(k for k, v in hashed.items() if v[1])

    startup = statistics.median(run_once([py, "-c", "pass"], None, 60)[0] for _ in range(3))
    runs = [run_once([py, *target], a.stdin, a.timeout, a.check) for _ in range(max(1, a.repeat))]
    wall, cpu = statistics.median(r[0] for r in runs), statistics.median(r[1] for r in runs)
    missing = sorted({c for r in runs for c, h in r[4].items() if h == "not written"})
    if missing and not a.compare:
        sys.exit(f"hotspots: the target did not write {', '.join(missing)}; --check names a file it writes")
    bare = parse_importtime(run_once([py, "-X", "importtime", "-c", "pass"], None, 60)[3])
    err = run_once([py, "-X", "importtime", *target], a.stdin, a.timeout)[3]
    (tmp / "importtime.txt").write_text(err)
    mods = {m: s for m, s in parse_importtime(err).items() if m not in bare}
    imports = sum(mods.values())
    took, raw = {}, {"wall": tmp / "cprofile_wall.prof", "sample": tmp / "samples.json"}
    for mode, f in raw.items():
        took[mode] = run_once([py, HERE, "--_child", mode, str(f), "--", *target], a.stdin, a.timeout)[0]
        if not f.is_file():
            sys.exit(f"hotspots: the target exited before the profiler could write {f} (os._exit skips it)")
    traced = took["wall"]
    load.append(os.getloadavg()[0])
    # a tick cuts a C-level wait short (see child()), and the shares then describe a shorter run
    unlike = [m for m, t, hi in (("sampler", took["sample"], 1.5), ("cProfile", traced, math.inf))
              if not 0.7 * wall - 0.05 < t < hi * wall + 0.05]

    doc = {"command": target, "python": py, "command_line": shlex.join([py, *target]), "cwd": os.getcwd(),
           "repeat": len(runs),
           "input": {"desc": a.input_desc, "files": files, "partial": partial, "hash_mb": a.hash_mb, "stdin": a.stdin,
                     "stdin_sha": sha(a.stdin) if a.stdin else None},
           "env": env_record(a.env), "outputs": {c: sorted({r[4][c] for r in runs}) for c in a.check},
           "wall_runs_s": [r[0] for r in runs], "cpu_runs_s": [r[1] for r in runs], "wall_s": wall, "cpu_s": cpu,
           "wait_s": max(0.0, wall - cpu), "startup_s": startup, "import_s": imports,
           "imports_top": sorted(mods.items(), key=lambda kv: -kv[1])[:5], "traced_wall_s": traced,
           "sampled_wall_s": took["sample"], "unlike_plain": unlike,
           "stdout_sha": sorted({r[2] for r in runs}), "load": load, **analyse(tmp, traced / wall)}
    doc["profile_share"]["imports"] = imports / wall

    print(f"command  {' '.join(target)}   ({len(runs)} fresh runs of {py})")
    print(f"input    {a.input_desc or '(not described)'}; files {files or '-'}; stdin {doc['input']['stdin_sha']}")
    print(f"wall     {wall:.3f} s median [{min(doc['wall_runs_s']):.3f}-{max(doc['wall_runs_s']):.3f}]   CPU {cpu:.3f} s")
    print(f"wait     {doc['wait_s']:.3f} s = wall - CPU ({doc['wait_s'] / wall:.0%} of wall): I/O, sleep, locks, children"
          if cpu <= wall else "wait     CPU exceeds wall: work runs in parallel, wait cannot be estimated")
    top_mods = ", ".join(f"{m} {s:.3f}" for m, s in doc["imports_top"]) or "-"
    print(f"imports  {imports:.3f} s beyond a bare interpreter's {startup:.3f} s ({imports / wall:.0%} of wall, "
          f"-X importtime); top: {top_mods}; sampler: {doc['import_share_sampled']:.0%} of sampled time")
    print(f"tracing  cProfile run {traced:.2f} s against {wall:.2f} s ({traced / wall:.1f}x); "
          f"sampler {doc['samples']} samples at {1000 * doc['interval']:.0f} ms over {doc['sampled_s']:.2f} s "
          f"({doc['samples_effective']:.0f} intervals; a C or blocking call holds a sample until it returns)")
    varies = [k for k, v in [("stdout", doc["stdout_sha"]), *doc["outputs"].items()] if len(v) > 1]
    for warn, cond in [("short run: startup and imports dominate; profile a production-sized input, "
                        "or pass --repeat 7", wall < 0.5),
                       ("few samples: shares are rough; use a longer input", doc["samples_effective"] < 200),
                       (f"input check partial for {', '.join(partial)}: past --hash-mb {a.hash_mb:g} or unreadable, "
                        "files are compared by size and mtime", bool(partial)),
                       (f"sampler stopped early: {doc['sampler_disturbed']}; shares cover only the time before, "
                        f"and ± rests on the {doc['samples']} samples taken", bool(doc["sampler_disturbed"])),
                       (f"sampler covered {doc['sampled_s']:.2f} s of its run's {doc['sampler_elapsed_s']:.2f} s: "
                        "shares are rough", doc["sampler_elapsed_s"] > max(0.1, 2 * doc["sampled_s"])),
                       *[(f"the {m} run took {doc['sampled_wall_s' if m == 'sampler' else 'traced_wall_s']:.2f} s "
                          f"against {wall:.2f} s plain, so its shares describe another run (a tick cuts a C-level "
                          "sleep, poll or select short); rank by the other column and ablate", True) for m in unlike],
                       (f"output differs between runs ({', '.join(varies)}): the gate and ablate.py's check "
                        "will not hold; fix it with a seed or a flag", bool(varies)),
                       (f"not written by every run: {', '.join(k for k, v in doc['outputs'].items() if 'not written' in v)}",
                        any("not written" in v for v in doc["outputs"].values())),
                       (f"machine busy (load {load[0]:.1f} on {os.cpu_count()} CPUs): timings are noisy",
                        max(load) > (os.cpu_count() or 1) / 2)]:
        if cond:
            print(f"WARNING  {warn}")
    print("\nPython frames by the sampler's self time; time in libraries, C and I/O goes to the nearest project frame")
    print("   self   incl     ± | cP incl     calls | function")
    for r in doc["frames"][:a.top]:
        print(f"  {pct(r['self'])} {pct(r['profile_share'])} {pct(r['se'])} | {pct(r['cp_cum'])} {r['calls'] or '-':>9}"
              f" | {r['name']} ({r['at']}) {' '.join(f'[{f}]' for f in r['flags'])}")
    print("\ncProfile by self time; C calls by name")
    print("  self wall cum wall     calls | function")
    for r in doc["by_self"][:a.top]:
        print(f"    {pct(r['self_wall'])}   {pct(r['cum_wall'])} {r['calls']:>9} | "
              f"{r['name']} {' '.join(f'[{f}]' for f in r['flags'])}")
    code = 0
    if a.compare:
        doc["gate"] = compare(json.loads(Path(a.compare).read_text()), doc, a.compare, a.focus)
        code = 0 if not a.focus or doc["gate"]["passed"] else 2
    for f in raw_names:
        shutil.move(str(tmp / f), str(out / f))
    (out / "hotspots.json").write_text(json.dumps(doc, indent=1))
    print(f"\nwritten  {out / 'hotspots.json'}, cprofile_wall.prof, importtime.txt, samples.json")
    sys.exit(code)


if __name__ == "__main__":
    main()
