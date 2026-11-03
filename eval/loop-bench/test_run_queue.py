"""run_queue.sh on a temp run folder with a fake claude and sysctl first on PATH: no agent, seconds.

usage: python3 eval/loop-bench/test_run_queue.py   (needs zsh)
The runner is copied beside a stub audit_reads.py, so nothing reads ~/.claude or the real runs/.
RUN_QUEUE=<path> tests another copy of the runner (the one-at-a-time cases only, for an old one).
"""
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "arms"))
import progress  # noqa: E402

RUNNER = os.environ.get("RUN_QUEUE") or os.path.join(HERE, "run_queue.sh")
LOAD = "{ 1.00 1.00 1.00 }"
# Each agent notes its start and end in $HOME/events, sleeps, and writes final.py unless told not to.
FAKE_CLAUDE = r'''#!/usr/bin/env python3
import json, os, sys, time
brief = sys.argv[sys.argv.index("-p") + 1]
def note(what):
    with open(os.path.join(os.environ["HOME"], "events"), "a") as f:
        f.write(f"{time.time():.4f} {what} {os.getcwd()}\n")
if brief.startswith("Reply with"):
    note("probe")
else:
    note("start")
    with open(os.path.join(os.environ["HOME"], "seen"), "a") as f:
        f.write(json.dumps([os.getcwd(), sorted(os.listdir("."))]) + "\n")
    with open("brief.txt", "w") as f:
        f.write(brief)
    if os.path.exists("make_stop"):
        open(os.path.join("..", "..", "STOP"), "w").close()
    time.sleep(0.8)
    if not os.path.exists("no_final"):
        with open("final.py", "w") as f:
            f.write("x = 1\n")
    note("end")
print(json.dumps({"is_error": False}))
'''
FAKE_AUDIT = r'''import os, time
with open(os.path.join(os.environ["HOME"], "events"), "a") as f:
    f.write(f"{time.time():.4f} audit -\n")
print("0 flags")
'''


def executable(path, text):
    with open(path, "w") as f:
        f.write(text)
    os.chmod(path, os.stat(path).st_mode | stat.S_IXUSR)


class RunQueue(unittest.TestCase):
    def setUp(self):
        self.tmp = os.path.realpath(tempfile.mkdtemp(prefix="run-queue-"))  # the runner logs /private/var, not /var
        self.bench = os.path.join(self.tmp, "lb")
        self.run_dir = os.path.join(self.bench, "runs", "r90")
        self.home = os.path.join(self.tmp, "home")
        self.bin = os.path.join(self.tmp, "bin")
        for d in (self.run_dir, self.home, self.bin):
            os.makedirs(d)
        shutil.copy(RUNNER, os.path.join(self.bench, "run_queue.sh"))
        executable(os.path.join(self.bench, "audit_reads.py"), FAKE_AUDIT)
        executable(os.path.join(self.bin, "claude"), FAKE_CLAUDE)
        executable(os.path.join(self.bin, "sysctl"), f"#!/bin/sh\necho '{LOAD}'\n")
        self.arm = os.path.join(self.tmp, "arm-x", "SKILL.md")
        os.makedirs(os.path.dirname(self.arm))
        open(self.arm, "w").close()
        self.nudge = os.path.join(self.tmp, "nudge.txt")
        with open(self.nudge, "w") as f:
            f.write("Think twice.")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def queue(self, lines, marks=None):
        """Writes the queue and a workspace per entry; marks: {entry: [file names to create]}."""
        with open(os.path.join(self.run_dir, "queue"), "w") as f:
            f.write("".join(line + "\n" for line in lines))
        self.marks = {line.split()[0]: set() for line in lines if line and not line.startswith("#")}
        for entry in self.marks:
            os.makedirs(os.path.join(self.run_dir, entry), exist_ok=True)
        for entry, names in (marks or {}).items():
            self.marks[entry] |= set(names)
            for n in names:
                open(os.path.join(self.run_dir, entry, n), "w").close()

    def claim(self, entry):
        return os.path.join(self.run_dir, ".claims", entry.replace("/", "__"))

    def run_queue(self, jobs):
        env = dict(os.environ, PATH=f"{self.bin}{os.pathsep}{os.environ['PATH']}", HOME=self.home, JOBS=str(jobs))
        r = subprocess.run(["zsh", os.path.join(self.bench, "run_queue.sh"), "r90"], env=env,
                           capture_output=True, text=True, timeout=60)
        self.assertEqual(r.returncode, 0, r.stderr)
        with open(os.path.join(self.run_dir, "queue.log")) as f:
            log = f.read().splitlines()
        for line in log:
            self.assertRegex(line, r"^\d\d:\d\d:\d\d \S")
        return log, [line[9:] for line in log]

    def events(self):
        out = []
        with open(os.path.join(self.home, "events")) as f:
            for line in f:
                t, what, where = line.split(" ", 2)
                out.append((float(t), what, os.path.relpath(where.strip(), self.run_dir)))
        return sorted(out)

    def check_events(self, entries, jobs):
        """Each entry ran exactly once, never more than `jobs` at a time; one probe, one audit, last;
        every workspace holds only its marks and what the agent and the runner write there (no claim)."""
        ev = self.events()
        self.assertEqual([w for _, w, _ in ev].count("probe"), 1)
        self.assertEqual(ev[-1][1], "audit")
        self.assertEqual(sorted(p for _, w, p in ev if w == "start"), sorted(entries))
        self.assertEqual(sorted(p for _, w, p in ev if w == "end"), sorted(entries))
        running = most = 0
        for _, w, _ in ev:
            running += {"start": 1, "end": -1}.get(w, 0)
            most = max(most, running)
        self.assertEqual(most, min(jobs, len(entries)))
        for e, marks in self.marks.items():
            want = set(marks)
            if e in entries:
                want |= {"agent.json", "agent.err", "brief.txt"} | (set() if "no_final" in marks else {"final.py"})
            self.assertEqual(set(os.listdir(os.path.join(self.run_dir, e))), want, e)
        for e in entries:
            self.assertFalse(os.path.exists(self.claim(e)), e)
        # What each agent saw in its folder at its start: no claim, nothing earlier runs lacked.
        with open(os.path.join(self.home, "seen")) as f:
            seen = {os.path.relpath(d, self.run_dir): names for d, names in map(json.loads, f)}
        self.assertEqual(seen, {e: sorted(self.marks[e] | {"agent.json", "agent.err"}) for e in entries})

    def main_queue(self):
        self.queue(["a/dedup -", f"b/cache {self.arm}", f"b/cache {self.arm}", "# a comment", "",
                    f"c/tsp {self.nudge}", "d/regex - claude-x-model", "e/knapsack -"],
                   marks={"a/dedup": ["final.py"], "e/knapsack": ["no_final"]})

    def test_one_at_a_time_keeps_todays_log(self):
        self.main_queue()
        _, lines = self.run_queue(1)
        start = f" on claude-opus-5-5 ({LOAD})"
        self.assertEqual(lines, [
            "skip a/dedup (final.py exists)",
            "start b/cache" + start, "done b/cache exit=0 final=yes", "skip b/cache (final.py exists)",
            "start c/tsp" + start, "done c/tsp exit=0 final=yes",
            f"start d/regex on claude-x-model ({LOAD})", "done d/regex exit=0 final=yes",
            "start e/knapsack" + start, "done e/knapsack exit=0 final=no",
            "queue finished", "audit: 0 flags"])
        self.check_events(["b/cache", "c/tsp", "d/regex", "e/knapsack"], 1)
        with open(os.path.join(self.run_dir, "c/tsp", "brief.txt")) as f:
            brief = f.read()
        self.assertIn(" Think twice. You may score", brief)
        self.assertIn("The laptop is shared: run at most one Python process at a time, always with `nice -n 19`", brief)

    @unittest.skipIf(os.environ.get("RUN_QUEUE"), "an old runner has no JOBS")
    def test_two_at_a_time_run_each_entry_once_in_queue_order(self):
        self.main_queue()
        log, lines = self.run_queue(2)
        start = f" on claude-opus-5-5 ({LOAD}) jobs=2"
        self.assertEqual([x for x in lines if x.startswith(("start", "skip", "queue started"))], [
            "queue started, jobs=2", "skip a/dedup (final.py exists)", "start b/cache" + start,
            f"skip b/cache (claimed: {self.claim('b/cache')} exists)", "start c/tsp" + start,
            f"start d/regex on claude-x-model ({LOAD}) jobs=2", "start e/knapsack" + start])
        self.assertEqual(sorted(x for x in lines if x.startswith("done")), [
            "done b/cache exit=0 final=yes", "done c/tsp exit=0 final=yes",
            "done d/regex exit=0 final=yes", "done e/knapsack exit=0 final=no"])
        self.assertEqual(lines[-2:], ["queue finished", "audit: 0 flags"])
        self.check_events(["b/cache", "c/tsp", "d/regex", "e/knapsack"], 2)

        with open(os.path.join(self.run_dir, "queue")) as f:
            q = f.read()
        mtime = progress.read_log(os.path.join(self.run_dir, "queue.log"))[1]
        s = progress.parse("loop-bench", q, log, mtime)
        self.assertEqual((s["state"], s["done"], s["no_final"], s["running"], s["jobs"]),
                         ("finished", {"a/dedup", "b/cache", "c/tsp", "d/regex"}, {"e/knapsack"}, {}, 2))
        # Up to the first done, the reader sees both agents running.
        first_done = next(i for i, x in enumerate(lines) if x.startswith("done"))
        s = progress.parse("loop-bench", q, log[:first_done], mtime)
        self.assertEqual(list(s["running"]), ["b/cache", "c/tsp"])
        out = progress.report(self.run_dir, s, mtime, 1.0, False)
        self.assertEqual(len(re.findall(r"^running: ", out, re.M)), 2, out)

    def stop_case(self, jobs):
        self.queue(["a/dedup -", "b/dedup -", "c/dedup -", "d/dedup -"], marks={"b/dedup": ["make_stop"]})
        _, lines = self.run_queue(jobs)
        self.assertEqual([x for x in lines if x.startswith("start")],
                         [f"start {e} on claude-opus-5-5 ({LOAD})" + (" jobs=2" if jobs > 1 else "")
                          for e in ("a/dedup", "b/dedup")])
        self.assertEqual(lines.count("STOP file found"), 1)
        self.assertEqual(lines[-2:], ["queue finished", "audit: 0 flags"])
        dones = [i for i, x in enumerate(lines) if x.startswith("done")]
        self.assertEqual(len(dones), 2)
        self.assertLess(dones[-1], lines.index("queue finished"))
        self.check_events(["a/dedup", "b/dedup"], jobs)
        return lines

    def test_stop_stops_new_starts(self):
        self.assertEqual(self.stop_case(1)[-3:], ["STOP file found", "queue finished", "audit: 0 flags"])

    @unittest.skipIf(os.environ.get("RUN_QUEUE"), "an old runner has no JOBS")
    def test_stop_stops_new_starts_two_at_a_time(self):
        self.stop_case(2)

    @unittest.skipIf(os.environ.get("RUN_QUEUE"), "an old runner has no claims")
    def test_a_left_claim_skips_its_entry_until_removed(self):
        self.queue(["a/dedup -", "b/dedup -"])
        os.makedirs(self.claim("a/dedup"))
        _, lines = self.run_queue(1)
        self.assertEqual(lines[0], f"skip a/dedup (claimed: {self.claim('a/dedup')} exists)")
        self.check_events(["b/dedup"], 1)
        os.rmdir(self.claim("a/dedup"))
        os.remove(os.path.join(self.run_dir, "queue.log"))
        os.remove(os.path.join(self.home, "events"))
        os.remove(os.path.join(self.home, "seen"))
        _, lines = self.run_queue(1)
        self.assertEqual(lines[:3], [f"start a/dedup on claude-opus-5-5 ({LOAD})", "done a/dedup exit=0 final=yes",
                                     "skip b/dedup (final.py exists)"])

    @unittest.skipIf(os.environ.get("RUN_QUEUE"), "an old runner has no JOBS")
    def test_jobs_must_be_a_positive_whole_number(self):
        self.queue(["a/dedup -"])
        for bad in ("0", "two", "-1"):
            env = dict(os.environ, PATH=f"{self.bin}{os.pathsep}{os.environ['PATH']}", HOME=self.home, JOBS=bad)
            r = subprocess.run(["zsh", os.path.join(self.bench, "run_queue.sh"), "r90"], env=env,
                               capture_output=True, text=True, timeout=10)
            self.assertEqual(r.returncode, 2, bad)
            self.assertIn("JOBS must be", r.stderr)
        self.assertFalse(os.path.exists(os.path.join(self.home, "events")))


if __name__ == "__main__":
    unittest.main(verbosity=2)
