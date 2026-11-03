"""Shared harness for the loop-bench scorers: static checks, a sandboxed child run, output."""
import ast
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

ALLOWED_IMPORTS = {
    "math", "random", "heapq", "bisect", "collections", "itertools", "functools",
    "operator", "array", "re", "string", "typing", "time", "statistics",
    "dataclasses", "copy", "fractions", "decimal", "enum",
}
BANNED_NAMES = {
    "open", "exec", "eval", "compile", "__import__", "globals", "locals", "vars",
    "breakpoint", "input", "getattr", "setattr", "delattr", "exit", "quit", "help",
}
# Module attributes that lead back to sys/os/frames even from an allowed import.
BANNED_ATTRS = {
    "sys", "os", "inspect", "builtins", "importlib", "io", "subprocess", "gc", "types",
    "marshal", "pickle", "ctypes", "socket", "shutil", "pathlib", "glob", "tempfile",
    "threading", "multiprocessing", "signal", "traceback", "linecache", "tokenize",
    "codecs", "posix", "f_back", "f_globals", "f_locals", "f_builtins", "f_code",
    "gi_frame", "cr_frame", "ag_frame", "tb_frame", "tb_next", "co_code", "modules",
    # attribute access or evaluation driven by strings
    "attrgetter", "methodcaller", "get_field", "get_value", "get_type_hints", "ForwardRef",
}
DUNDER_IN_STRING = re.compile(r"__\w+__")
SAFE_DUNDER_ATTRS = {
    "__init__", "__len__", "__contains__", "__iter__", "__next__", "__getitem__",
    "__setitem__", "__delitem__", "__eq__", "__lt__", "__le__", "__gt__", "__ge__",
    "__hash__", "__repr__", "__str__",
}
MAX_SOURCE_BYTES = 100_000
INVALID_SCORE = -1e9
# -I without its -E: -E would drop PYTHONHASHSEED, and the child's env is built from nothing anyway.
CHILD_FLAGS = ["-P", "-s", "-S"]


def _dunder(name):
    return name.startswith("__") and name.endswith("__")


def static_check(src):
    """Return a list of rule violations in the candidate source (empty when clean)."""
    if len(src.encode()) > MAX_SOURCE_BYTES:
        return [f"source larger than {MAX_SOURCE_BYTES} bytes"]
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        return [f"syntax error: {e}"]
    problems = []
    modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                root = a.name.split(".")[0]
                if root not in ALLOWED_IMPORTS:
                    problems.append(f"line {node.lineno}: import {a.name} is not allowed")
                modules.add(a.asname or root)
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".")[0]
            if node.level or root not in ALLOWED_IMPORTS:
                problems.append(f"line {node.lineno}: from {node.module} import is not allowed")
            for a in node.names:
                if a.name.startswith("_") or a.name in BANNED_ATTRS or a.name == "*":
                    problems.append(f"line {node.lineno}: importing {a.name} is not allowed")
        elif isinstance(node, ast.Name):
            if node.id in BANNED_NAMES or (_dunder(node.id) and node.id != "__name__"):
                problems.append(f"line {node.lineno}: name {node.id} is not allowed")
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            if DUNDER_IN_STRING.search(node.value):
                problems.append(f"line {node.lineno}: dunder name inside a string")
        elif isinstance(node, ast.Attribute):
            if _bad_attr(node.attr):
                problems.append(f"line {node.lineno}: attribute .{node.attr} is not allowed")
        elif isinstance(node, ast.MatchClass):
            for name in node.kwd_attrs:
                if _bad_attr(name):
                    problems.append(f"line {node.lineno}: attribute {name}= in a pattern is not allowed")
        for name in _bound_names(node):
            if _dunder(name) and name not in SAFE_DUNDER_ATTRS:
                problems.append(f"line {getattr(node, 'lineno', '?')}: defining {name} is not allowed")
    return problems


def _bound_names(node):
    """Names a node binds as plain strings, which the ast.Name check never sees. A dunder bound this
    way (a module __getattr__, __del__, __init_subclass__, ...) runs implicitly, after the checks."""
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return [node.name]
    if isinstance(node, ast.alias):
        return [node.asname or node.name.split(".")[0]]
    if isinstance(node, (ast.ExceptHandler, ast.MatchAs, ast.MatchStar)):
        return [node.name] if node.name else []
    if isinstance(node, ast.MatchMapping):
        return [node.rest] if node.rest else []
    if isinstance(node, ast.arg):
        return [node.arg]
    if isinstance(node, (ast.Global, ast.Nonlocal)):
        return list(node.names)
    if isinstance(node, _TYPE_PARAMS):
        return [node.name]
    return []


_TYPE_PARAMS = tuple(getattr(ast, n) for n in ("TypeVar", "ParamSpec", "TypeVarTuple") if hasattr(ast, n))


def _reach():
    """Attribute names through which an allowed module hands out a module we did not allow, or a
    private object of its own. They are refused on any receiver: an alias, an argument or a
    container hides which object an attribute is read from, so the name is what can be checked."""
    import importlib
    import types
    names, seen = set(), set()
    todo = [importlib.import_module(m) for m in sorted(ALLOWED_IMPORTS)]
    while todo:
        mod = todo.pop()
        if mod.__name__ in seen:
            continue
        seen.add(mod.__name__)
        for k, v in vars(mod).items():
            if _dunder(k):
                continue
            if isinstance(v, types.ModuleType):
                if v.__name__.split(".")[0] in ALLOWED_IMPORTS:
                    todo.append(v)  # collections.abc and the like: allowed, but its privates count
                    if k.startswith("_"):
                        names.add(k)
                else:
                    names.add(k)
            elif k.startswith("_"):
                names.add(k)
    return frozenset(names)


# namedtuple's public API, which starts with an underscore; dataclasses._replace, the one module
# private of that name, only rebuilds an object from its fields.
PUBLIC_UNDERSCORE = {"_replace", "_asdict", "_make", "_fields", "_field_defaults"}
REACH_ATTRS = _reach() - PUBLIC_UNDERSCORE


def _bad_attr(name):
    if name in BANNED_ATTRS or name in REACH_ATTRS:
        return True
    if _dunder(name):
        return name not in SAFE_DUNDER_ATTRS
    return False


PREAMBLE = r'''
import sys, json, signal, time, builtins, io, os as _os
sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
_payload = json.loads(sys.stdin.read())
_out = sys.stdout
sys.stdout = sys.stderr

class _Timeout(BaseException):
    pass

def _alarm(signum, frame):
    raise _Timeout()

signal.signal(signal.SIGALRM, _alarm)

def _blocked(*a, **k):
    raise PermissionError("file and process access is not allowed")

builtins.open = _blocked
io.open = _blocked
# Should a candidate reach os anyway: no files, no processes, and no write to fd 1, which
# would forge the result line.
for _n in ("open", "fdopen", "listdir", "scandir", "walk", "popen", "system", "fork", "forkpty",
           "remove", "unlink", "rename", "replace", "chdir", "mkdir", "makedirs", "rmdir",
           "removedirs", "truncate", "symlink", "link", "chmod", "chown", "putenv", "kill",
           "killpg", "write", "dup", "dup2", "pipe", "execl", "execle", "execlp", "execlpe",
           "execv", "execve", "execvp", "execvpe", "spawnl", "spawnle", "spawnlp", "spawnlpe",
           "spawnv", "spawnve", "spawnvp", "spawnvpe", "posix_spawn", "posix_spawnp"):
    if hasattr(_os, _n):
        setattr(_os, _n, _blocked)

def _arm(seconds):
    signal.setitimer(signal.ITIMER_REAL, seconds)

def _disarm():
    signal.setitimer(signal.ITIMER_REAL, 0)

def _main():
    try:
        _arm(5.0)
        try:
            import candidate as _cand
        finally:
            _disarm()
        res = _run(_cand, _payload)
    except _Timeout:
        res = {"error": "time limit exceeded"}
    except BaseException as e:
        res = {"error": f"{type(e).__name__}: {e}"[:500]}
    _out.write(json.dumps(res) + "\n")
    _out.flush()
'''

FOOTER = "\n_main()\n"


def run_child(candidate_path, runner_body, payload, timeout, source=None):
    """Run the candidate in an isolated temp dir; return the runner's dict or {"error": ...}.

    `source` replaces reading `candidate_path` (the scorer's own reference code)."""
    src = source
    if src is None:
        try:
            with open(candidate_path, encoding="utf-8") as f:
                src = f.read()
        except OSError as e:
            return {"error": f"cannot read candidate: {e}"}
    problems = static_check(src)
    if problems:
        return {"error": "static check failed", "problems": problems[:20]}
    tmp = tempfile.mkdtemp(prefix="loopbench-")
    try:
        with open(os.path.join(tmp, "candidate.py"), "w", encoding="utf-8") as f:
            f.write(src)
        with open(os.path.join(tmp, "runner.py"), "w", encoding="utf-8") as f:
            f.write(PREAMBLE + runner_body + FOOTER)
        try:
            proc = subprocess.run(
                [sys.executable, *CHILD_FLAGS, "runner.py"], cwd=tmp, input=json.dumps(payload),
                capture_output=True, text=True, timeout=timeout,
                env={"PATH": "/usr/bin:/bin", "PYTHONHASHSEED": "0"},
            )
        except subprocess.TimeoutExpired:
            return {"error": f"time limit exceeded (whole run over {timeout}s)"}
        lines = [ln for ln in proc.stdout.splitlines() if ln.strip()]
        if not lines:
            return {"error": "candidate process produced no result",
                    "stderr": proc.stderr[-500:]}
        try:
            return json.loads(lines[-1])
        except json.JSONDecodeError:
            return {"error": "unreadable result from candidate process"}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def parse_args(argv):
    if len(argv) < 2 or argv[1].startswith("-"):
        sys.stderr.write("usage: python3 score.py <candidate.py> [--split train|test|stress]\n")
        sys.exit(2)
    split = "train"
    if "--split" in argv:
        i = argv.index("--split")
        split = argv[i + 1] if i + 1 < len(argv) else ""
    if split not in ("train", "test", "stress"):
        sys.stderr.write("--split must be train, test or stress\n")
        sys.exit(2)
    return argv[1], split


def test_seed(default):
    """The test split's seed; LOOP_BENCH_TEST_SEED replaces it for a fresh hidden set."""
    return os.environ.get("LOOP_BENCH_TEST_SEED", default)


def emit(valid, score, detail):
    out = {"valid": bool(valid), "score": round(score, 6) if valid else INVALID_SCORE,
           "detail": detail}
    print(json.dumps(out))


def fail(detail):
    emit(False, INVALID_SCORE, detail)
