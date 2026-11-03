"""Shared by smoke.py and measure_shares.py: work copies, variant commands, one timed run."""
import hashlib
import json
import os
import resource
import shutil
import subprocess
import sys
import time

LAB = os.path.dirname(os.path.abspath(__file__))
BENCH = os.path.dirname(LAB)
TASKS = os.path.join(BENCH, "tasks")
HARNESS = os.path.join(LAB, "harness.py")
# -I without its -E: -E drops PYTHONHASHSEED, and the env below is built from nothing anyway.
HARNESS_FLAGS = ["-P", "-s", "-S"]
CHILD_ENV = {"PATH": "/usr/bin:/bin", "PYTHONHASHSEED": "0"}


def manifest():
    with open(os.path.join(LAB, "manifest.json"), encoding="utf-8") as f:
        return json.load(f)


def task_digest(tid):
    """Digest of a task folder's files, so shares measured on other code can be told apart."""
    h = hashlib.sha256()
    root = os.path.join(TASKS, tid)
    paths = []
    for d, dirs, files in os.walk(root):
        dirs[:] = [x for x in dirs if x != "__pycache__"]
        paths += [os.path.join(d, n) for n in files if n != ".DS_Store"]
    for path in sorted(paths):
        h.update(os.path.relpath(path, root).encode() + b"\0")
        with open(path, "rb") as f:
            h.update(f.read())
    return h.hexdigest()[:16]


def lower_priority():
    try:
        os.nice(19 - os.nice(0))
    except OSError:
        pass


def sizes(spec, tiny):
    """(label, gen args or None, program args) for each input size a task is measured at."""
    if tiny:
        return [("tiny", spec["gen_tiny"], spec["args"])]
    out = [("prod", spec["gen"], spec["args"])]
    if "toy" in spec:  # t05 ships its toy input; t16 generates it with the generator's defaults
        out.append(("toy", spec["toy"].get("gen"), spec["toy"]["args"]))
    return out


def prepare(tid, work, gen_args):
    if os.path.exists(work):
        shutil.rmtree(work)
    shutil.copytree(os.path.join(TASKS, tid), work, ignore=shutil.ignore_patterns("__pycache__"))
    if gen_args is not None:
        subprocess.run([sys.executable, "gen_input.py", *gen_args], cwd=work, check=True,
                       stdout=subprocess.DEVNULL, timeout=600)
    os.makedirs(os.path.join(work, ".out"), exist_ok=True)


def command(tid, spec, variant, args, record=False):
    if variant == "plain":
        return [sys.executable, spec["entry"], *args]
    return [sys.executable, *HARNESS_FLAGS, HARNESS, tid, variant, *(["--record"] if record else []), "--",
            spec["entry"], *args]


def run(cmd, work, label, timeout=120):
    out_path = os.path.join(work, ".out", label + ".txt")
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    with open(out_path, "wb") as out:
        t = time.perf_counter()
        r = subprocess.run(cmd, cwd=work, stdout=out, stderr=subprocess.PIPE, timeout=timeout, env=CHILD_ENV)
        wall = time.perf_counter() - t
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    if r.returncode:
        raise RuntimeError(f"{' '.join(cmd)} failed in {work}:\n{r.stderr.decode(errors='replace')[-2000:]}")
    with open(out_path, "rb") as f:
        digest = hashlib.sha256(f.read()).hexdigest()
    cpu = (after.ru_utime - before.ru_utime) + (after.ru_stime - before.ru_stime)
    return {"wall": wall, "cpu": cpu, "sha": digest}
