"""profile-first's scripts keep the guarantees its SKILL.md relies on.

Usage: python3 scripts/test_profile_first.py   Each case runs the scripts on a program of a second or less.
"""
import contextlib
import importlib.util
import io
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "plugins/anti-skill/skills/profile-first/scripts"
HOTSPOTS, ABLATE = SCRIPTS / "hotspots.py", SCRIPTS / "ablate.py"

WORK = """
def work():
    return sum(i * i for i in range(400_000))
"""
# libc's usleep returns early on EINTR and nothing retries it: the sampler's tick cuts it short
C_WAIT = WORK + """
import ctypes
libc = ctypes.CDLL(None)
def c_wait():
    for _ in range(4):
        libc.usleep(100_000)
c_wait()
work()
"""
# time.sleep retries after a signal (PEP 475), so this run is the same under the sampler
PY_WAIT = WORK + """
import time
time.sleep(0.4)
work()
"""


def load(path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def compare(old, new):
    with contextlib.redirect_stdout(io.StringIO()):  # the gate prints its table; the log stays readable
        return load(HOTSPOTS).compare(old, new, "old.json", "app.py:f")


def tree(root):
    """Every file under root with its bytes, to tell whether anything changed."""
    return {str(p.relative_to(root)): p.read_bytes() for p in sorted(Path(root).rglob("*")) if p.is_file()}


class Case(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="pf-test-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.proj = self.tmp / "proj"
        self.proj.mkdir()

    def run_script(self, script, *args):
        return subprocess.run([sys.executable, str(script), *args], cwd=self.proj, capture_output=True, text=True,
                              timeout=120)

    def profile(self, program):
        (self.proj / "app.py").write_text(program)
        r = self.run_script(HOTSPOTS, "--", sys.executable, "app.py")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return r.stdout, json.loads((self.proj / "profile/hotspots.json").read_text())


class SampledRunUnlikePlain(Case):
    def test_c_wait_cut_short_is_flagged(self):
        out, doc = self.profile(C_WAIT)
        self.assertIn("sampler", doc["unlike_plain"], out)
        self.assertIn("WARNING  the sampler run took", out)
        self.assertLess(doc["sampled_wall_s"], 0.7 * doc["wall_s"])

    def test_python_sleep_is_not_flagged(self):
        out, doc = self.profile(PY_WAIT)
        self.assertEqual(doc["unlike_plain"], [], out)
        self.assertNotIn("plain, so its shares describe another run", out)

    def test_gate_refuses_an_unlike_profile(self):
        old = gate_doc(share=0.5, walls=[1.0, 1.0, 1.0])
        new = gate_doc(share=0.1, walls=[0.5, 0.5, 0.5])
        old["unlike_plain"] = ["sampler"]
        gate = compare(old, new)
        self.assertFalse(gate["passed"])
        self.assertTrue(gate["reason"].startswith("unclear: a profiled run was unlike"), gate["reason"])


def gate_doc(share, walls):
    return {"command": ["app.py"], "python": "python3", "cwd": "/p", "env": {}, "outputs": {},
            "input": {"files": {}, "stdin_sha": None, "partial": [], "hash_mb": 256},
            "stdout_sha": ["x"], "wall_runs_s": walls, "wall_s": sorted(walls)[len(walls) // 2],
            "frames": [{"name": "app.py:f", "at": "app.py:1", "se": 0.01}] if share else [],
            "profile_share": {"app.py:f": share} if share else {}, "seen": ["app.py:f"] * bool(share),
            "unlike_plain": []}


class GateNamesTheFailingCondition(unittest.TestCase):
    def test_wall_only_failure(self):
        gate = compare(gate_doc(0.12, [9.4, 10.0, 10.9]), gate_doc(0.0, [8.1, 8.8, 9.7]))
        self.assertFalse(gate["passed"])
        self.assertTrue(gate["reason"].startswith("wall within range: share"), gate["reason"])

    def test_share_only_failure(self):
        gate = compare(gate_doc(0.5, [1.0, 1.0, 1.0]), gate_doc(0.49, [0.5, 0.5, 0.5]))
        self.assertTrue(gate["reason"].startswith("share not beyond noise: share"), gate["reason"])

    def test_pass(self):
        gate = compare(gate_doc(0.5, [1.0, 1.0, 1.0]), gate_doc(0.1, [0.5, 0.5, 0.5]))
        self.assertTrue(gate["passed"], gate["reason"])
        self.assertTrue(gate["reason"].startswith("share "), gate["reason"])


class ForeignProfileFolder(Case):
    def test_a_package_named_profile_is_left_alone(self):
        (self.proj / "app.py").write_text("print(1)\n")
        pkg = self.proj / "profile"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("")
        (pkg / "samples.json").write_text("my notes")
        before = tree(self.proj)
        r = self.run_script(HOTSPOTS, "--", sys.executable, "app.py")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("pass --out another folder", r.stderr)
        self.assertEqual(tree(self.proj), before)

    def test_its_own_folder_is_reused(self):
        self.profile("print(1)\n")
        _, doc = self.profile("print(2)\n")
        self.assertEqual(shlex.split(doc["command_line"]), [sys.executable, "app.py"])


class UnreadableInput(unittest.TestCase):
    @unittest.skipIf(hasattr(os, "geteuid") and os.geteuid() == 0, "root reads a mode-000 file")
    def test_unreadable_file_counts_as_partial(self):
        hs = load(HOTSPOTS)
        with tempfile.TemporaryDirectory() as d:
            data = Path(d) / "data"
            data.mkdir()
            (data / "ok.txt").write_text("a")
            locked = data / "locked.txt"
            locked.write_text("b")
            locked.chmod(0)
            try:
                digest, partial = hs.input_sha(data, 1 << 20)
            finally:
                locked.chmod(0o600)
            self.assertTrue(partial)

    def test_non_utf8_name_is_hashed(self):
        hs = load(HOTSPOTS)
        with tempfile.TemporaryDirectory() as d:
            try:
                with open(os.path.join(os.fsencode(d), b"caf\xe9.csv"), "wb") as f:
                    f.write(b"x")
            except OSError:
                self.skipTest("this file system refuses a name that is not UTF-8 (APFS)")
            digest, partial = hs.input_sha(Path(d), 1 << 20)
            self.assertFalse(partial)


class BaseRunsInACopy(Case):
    PROGRAM = "open('out.txt', 'w').write('done')\nprint('ok')\n"

    def setUp(self):
        super().setUp()
        (self.proj / "app.py").write_text(self.PROGRAM)

    def ablate(self, *cwd_args):
        return self.run_script(ABLATE, "--name", "app.py:f", "--base", f"{sys.executable} app.py",
                               "--variant", f"{sys.executable} app.py", "--check", "out.txt", "--repeats", "5",
                               *cwd_args)

    def test_original_folder_untouched(self):
        before = tree(self.proj)
        base, variant = self.tmp / "base", self.tmp / "ablate"
        shutil.copytree(self.proj, base)
        shutil.copytree(self.proj, variant)
        r = self.ablate("--base-cwd", str(base), "--variant-cwd", str(variant))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("written  profile/ablate/app.py_f.json", r.stdout)
        after = {k: v for k, v in tree(self.proj).items() if not k.startswith("profile/")}
        self.assertEqual(after, before)
        self.assertTrue((base / "out.txt").is_file() and (variant / "out.txt").is_file())

    def test_base_in_the_project_is_refused(self):
        before = tree(self.proj)
        for cwd in (".", str(self.proj), str(self.tmp), str(self.proj / "sub")):
            r = self.ablate("--base-cwd", cwd)
            self.assertNotEqual(r.returncode, 0, cwd)
            self.assertIn("overlaps it", r.stderr, cwd)
        r = self.ablate()
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(tree(self.proj), before)


if __name__ == "__main__":
    unittest.main(verbosity=2)
