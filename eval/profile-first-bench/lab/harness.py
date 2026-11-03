"""Run a task program with one component stubbed, in this fresh process.

usage (from a work copy of tasks/TASK):
    PYTHONHASHSEED=0 python3 -P -s -S harness.py TASK VARIANT [--record] -- ENTRY ARGS...
VARIANT is "none" or a component name from stubs/TASK.py. --record runs the real program with
every Replay stub recording, which the stubbed runs then read from .replay/ in the work copy.
"""
import atexit
import importlib.util
import os
import sys

LAB = os.path.dirname(os.path.abspath(__file__))


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def main():
    task, variant, rest = sys.argv[1], sys.argv[2], sys.argv[3:]
    record = bool(rest) and rest[0] == "--record"
    rest = rest[1:] if record else rest
    rest = rest[1:] if rest and rest[0] == "--" else rest
    entry, args = rest[0], rest[1:]
    work = os.getcwd()
    sys.path[:0] = [work, LAB]
    import stubkit

    stubs = load(os.path.join(LAB, "stubs", f"{task}.py"), "_bench_stubs").STUBS
    if variant != "none" and variant not in stubs:
        raise SystemExit(f"{task}: no stub named {variant!r}; have {sorted(stubs)}")
    ctx = stubkit.Ctx(os.path.join(work, ".replay"), record)
    active = list(stubs.values()) if record else ([] if variant == "none" else [stubs[variant]])
    for s in active:
        s.before_import(ctx)
    sys.argv = [entry] + args
    app = load(os.path.join(work, entry), os.path.splitext(entry)[0])
    for s in active:
        s.after_import(app, ctx)

    def finish():
        sys.stdout.flush()
        for s in active:
            s.finish(ctx)
    # Registered before main() runs, so it runs after any exit handler the program registers.
    atexit.register(finish)
    app.main(args)


if __name__ == "__main__":
    main()
