"""progress.py on synthetic queues in a temp dir: no real run folder, no agent.

usage: python3 eval/arms/test_progress.py
"""
import contextlib
import datetime
import io
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import progress  # noqa: E402

DAY = datetime.datetime(2026, 11, 1)
QUEUE = "a1 t01 plain 1\nb2 t01 skill 1\n# a comment\nc3 t02 skill 1 heavy 7\nd4 t02 plain 1\n"


def at(h, m, s=0, day=DAY):
    return day.replace(hour=h, minute=m, second=s)


class Progress(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="progress-")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def arms(self, log, queue=QUEUE, last_write=None):
        h = os.path.join(self.tmp, "run-x", ".harness")
        os.makedirs(h)
        with open(os.path.join(h, "queue"), "w") as f:
            f.write(queue)
        with open(os.path.join(h, "LOAD_MAX"), "w") as f:
            f.write("4.0\n")
        if log is not None:
            with open(os.path.join(h, "queue.log"), "w") as f:
                f.write(log)
            if last_write:
                os.utime(os.path.join(h, "queue.log"), (last_write.timestamp(), last_write.timestamp()))
        return os.path.join(self.tmp, "run-x")

    def state(self, log, last_write, kind="arms", queue=QUEUE):
        return progress.parse(kind, queue, log.splitlines(), last_write)

    def test_a_running_queue(self):
        log = ("10:00:00 queue started on claude-opus-5-5, load gate 3.0, cap $4\n"
               "10:00:05 start a1 ({ 1.0 1.0 1.0 })\n10:02:05 done a1 exit=0\n"
               "10:02:05 start b2 ({ 1.0 1.0 1.0 })\n10:06:05 done b2 exit=0\n"
               "10:06:05 start c3 under heavy ({ 1.0 1.0 1.0 })\n")
        s = self.state(log, at(10, 6, 5))
        out = progress.report("/x/run-x", s, at(10, 11, 5), 2.0, False)
        self.assertEqual(out.splitlines(), [
            "run-x (arms queue)", "done 2/4 (50%)",
            "running: c3 t02 skill, 5 min since start (by the log)",
            "median 3.0 min per finished agent (2 timed)",
            "left ≈ 3 min (estimate: 2 agent(s) at the median)"])

    def test_a_queue_across_midnight(self):
        log = "23:58:00 start a1 (x)\n00:03:00 done a1 exit=0\n00:03:00 start b2 (x)\n"
        s = self.state(log, at(0, 3, 0, DAY + datetime.timedelta(days=1)))
        self.assertEqual(s["durations"], {"a1": 5.0})
        self.assertEqual(s["running"], {"b2": at(0, 3, 0, DAY + datetime.timedelta(days=1))})

    def test_between_agents_names_the_load_gate(self):
        log = "10:00:00 queue started on m, load gate 3.0, cap $4\n10:00:01 start a1 (x)\n10:01:01 done a1 exit=0\n"
        s = self.state(log, at(10, 1, 1))
        self.assertIn("load 3.50 against the gate 3: waiting on the load gate",
                      progress.report("r", s, at(10, 5), 3.5, False))
        self.assertIn("under the gate, the next agent is starting", progress.report("r", s, at(10, 5), 1.0, False))

    def test_stopped_by_stop_and_after_an_error(self):
        s = self.state("10:00:00 start a1 (x)\n10:01:00 done a1 exit=0\n10:01:00 STOP file found\n"
                       "10:01:00 queue stopped\n", at(10, 1))
        out = progress.report("r", s, at(10, 2), 1.0, True)
        self.assertIn("state: stopped by STOP at 10:01:00", out)
        self.assertIn("STOP file present", out)
        self.assertNotIn("left ≈", out)
        s = self.state("10:00:00 start a1 (x)\n10:01:00 error a1 exit=1: kept as agent.error.1.json; STOP touched\n"
                       "10:01:00 queue stopped\n", at(10, 1))
        self.assertEqual((s["state"], s["done"]), ("stopped after an error", set()))

    def test_skips_count_as_done_and_a_restart_is_timed_from_its_last_start(self):
        log = ("09:00:00 start a1 (x)\n09:30:00 STOP file found\n09:30:00 queue stopped\n"
               "10:00:00 queue started on m, load gate 4.0, cap $4\n10:00:00 skip b2 (finished)\n"
               "10:00:00 restart a1 from the pristine case\n10:00:01 start a1 (x)\n10:03:01 done a1 exit=0\n")
        s = self.state(log, at(10, 3, 1))
        self.assertEqual((s["done"], s["durations"], s["gate"]), ({"a1", "b2"}, {"a1": 3.0}, 4.0))

    def test_a_loop_bench_queue(self):
        q = "plain1/dedup -\nv2a/dedup /r/runs/r15/arm-v2/SKILL.md\nn1/dedup /r/runs/r15/nudge.txt\n"
        self.assertEqual(progress.read_queue("loop-bench", q),
                         [("plain1/dedup", "dedup", "plain"), ("v2a/dedup", "dedup", "arm-v2"),
                          ("n1/dedup", "dedup", "nudge.txt")])
        log = ("01:00:00 skip plain1/dedup (final.py exists)\n01:00:00 start v2a/dedup on claude-opus-5-5 (x)\n"
               "01:10:00 done v2a/dedup exit=0 final=yes\n01:10:00 start n1/dedup on claude-opus-5-5 (x)\n")
        s = self.state(log, at(1, 10), kind="loop-bench", queue=q)
        out = progress.report("r15", s, at(1, 14), 1.0, False)
        self.assertIn("done 2/3 (67%)", out)
        self.assertIn("running: n1/dedup dedup nudge.txt, 4 min since start", out)
        self.assertIn("left ≈ 6 min", out)
        s = self.state(log + "01:20:00 done n1/dedup exit=0 final=yes\n01:20:00 queue finished\n"
                       "01:20:05 audit: 3 agents read nothing outside\n", at(1, 20, 5), kind="loop-bench", queue=q)
        self.assertEqual((s["state"], len(s["done"])), ("finished", 3))

    def loop_bench(self, queue, finals=(), log=None, guard=None, last_write=None):
        r = os.path.join(self.tmp, "runs", "r30")
        os.makedirs(r)
        with open(os.path.join(r, "queue"), "w") as f:
            f.write(queue)
        for e in finals:
            os.makedirs(os.path.join(r, e), exist_ok=True)
            open(os.path.join(r, e, "final.py"), "w").close()
        for name, text in (("queue.log", log), ("guard.log", guard)):
            if text is not None:
                p = os.path.join(r, name)
                with open(p, "w") as f:
                    f.write(text)
                if last_write:
                    os.utime(p, (last_write.timestamp(), last_write.timestamp()))
        return r

    def main_out(self, run):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(progress.main([run]), 0)
        return out.getvalue()

    def test_done_is_counted_from_the_workspaces_without_a_log(self):
        q = "p1/dedup -\np1/cache -\np1/dedup -\nq1/dedup /r/arm-q/SKILL.md\n"
        out = self.main_out(self.loop_bench(q, finals=["p1/dedup", "p1/cache", "q1/dedup"]))
        self.assertIn("done 3/3 (100%)\nstate: finished (no queue.log; counted from the workspaces)", out)
        self.assertNotIn("estimate", out)
        shutil.rmtree(os.path.join(self.tmp, "runs"))
        out = self.main_out(self.loop_bench(q, finals=["p1/dedup"]))
        self.assertIn("done 1/3 (33%)\nstate: not started (no queue.log)", out)

    def test_a_running_agents_draft_final_is_not_done(self):
        q = "a/dedup -\nb/dedup -\n"
        s = progress.parse("loop-bench", q, ["10:00:00 start a/dedup on m (x)"], at(10, 0), {"a/dedup"})
        self.assertEqual((list(s["running"]), s["done"]), (["a/dedup"], set()))

    def test_final_no_is_not_done_and_is_named(self):
        q = "a/dedup -\nb/dedup -\nc/dedup -\n"
        log = ("10:00:00 start a/dedup on m (x)\n10:05:00 done a/dedup exit=1 final=no\n"
               "10:05:00 start b/dedup on m (x)\n10:09:00 done b/dedup exit=0 final=yes\n")
        s = self.state(log, at(10, 9), kind="loop-bench", queue=q)
        self.assertEqual((s["done"], s["no_final"], s["durations"]),
                         ({"b/dedup"}, {"a/dedup"}, {"a/dedup": 5.0, "b/dedup": 4.0}))
        out = progress.report("r", s, at(10, 9, 30), 1.0, False)
        self.assertIn("done 1/3 (33%)\nended without final.py: a/dedup\nstate: between agents at 10:09:00", out)
        self.assertIn("left ≈ 9 min (estimate: 2 agent(s) at the median)", out)

    def test_loop_bench_logs_queue_finished_after_a_stop(self):
        q = "a/dedup -\nb/dedup -\n"
        log = ("10:00:00 start a/dedup on m (x)\n10:04:00 done a/dedup exit=0 final=yes\n"
               "10:04:00 STOP file found\n10:04:00 queue finished\n10:04:01 audit: 0 flags\n")
        s = self.state(log, at(10, 4, 1), kind="loop-bench", queue=q)
        self.assertEqual(s["state"], "stopped by STOP")
        out = progress.report("r", s, at(10, 34), 1.0, True)
        self.assertIn("state: stopped by STOP at 10:04:00 (30 min ago)", out)
        self.assertNotIn("load", out)
        s = self.state(log.replace("10:04:00 STOP file found\n", "10:04:00 start b/dedup on m (x)\n"
                                   "10:08:00 done b/dedup exit=0 final=yes\n"), at(10, 8), kind="loop-bench", queue=q)
        self.assertEqual(s["state"], "finished")

    def test_two_agents_at_once(self):
        q = "a/dedup -\nb/dedup -\nb/dedup -\nc/dedup -\nd/dedup -\n"
        log = ("10:00:00 queue started, jobs=2\n10:00:00 start a/dedup on m ({ 1 1 1 }) jobs=2\n"
               "10:00:01 start b/dedup on m ({ 1 1 1 }) jobs=2\n10:00:01 skip b/dedup (claimed: /r/.claims/b__dedup exists)\n"
               "10:10:00 done a/dedup exit=0 final=yes\n10:10:01 start c/dedup on m ({ 1 1 1 }) jobs=2\n")
        s = self.state(log, at(10, 10, 1), kind="loop-bench", queue=q)
        self.assertEqual((list(s["running"]), s["done"], s["jobs"], s["state"]),
                         (["b/dedup", "c/dedup"], {"a/dedup"}, 2, "running"))
        out = progress.report("r", s, at(10, 14, 1), 1.0, False)
        self.assertIn("done 1/4 (25%)\nrunning: b/dedup dedup plain, 14 min since start (by the log)\n"
                      "running: c/dedup dedup plain, 4 min since start (by the log)\n", out)
        # b has ~0 left at the 10 min median, c has 6, d has 10: 16 min over 2 workers.
        self.assertIn("left ≈ 8 min (estimate: 3 agent(s) at the median, 2 at a time)", out)
        s = self.state(log + "10:12:00 done b/dedup exit=0 final=no\n", at(10, 12), kind="loop-bench", queue=q)
        self.assertEqual((list(s["running"]), s["no_final"], s["state"]), (["c/dedup"], {"b/dedup"}, "running"))

    def test_a_stop_with_two_agents_waits_for_both(self):
        q = "a/dedup -\nb/dedup -\nc/dedup -\n"
        log = ("10:00:00 queue started, jobs=2\n10:00:00 start a/dedup on m (x) jobs=2\n"
               "10:00:01 start b/dedup on m (x) jobs=2\n10:05:00 done a/dedup exit=0 final=yes\n"
               "10:05:00 STOP file found\n")
        s = self.state(log, at(10, 5), kind="loop-bench", queue=q)
        self.assertEqual((list(s["running"]), s["state"]), (["b/dedup"], "stopped by STOP"))
        out = progress.report("r", s, at(10, 6), 1.0, True)
        self.assertIn("running: b/dedup dedup plain, 6 min since start (by the log)\n"
                      "state: stopped by STOP at 10:05:00; no new start, the agents above run to their end", out)
        self.assertNotIn("left ≈", out)
        s = self.state(log + "10:07:00 done b/dedup exit=0 final=yes\n10:07:00 queue finished\n",
                       at(10, 7), kind="loop-bench", queue=q)
        self.assertEqual((s["running"], s["state"], s["done"]), ({}, "stopped by STOP", {"a/dedup", "b/dedup"}))

    def test_a_restart_forgets_agents_a_killed_runner_never_closed(self):
        q = "a/dedup -\nb/dedup -\nc/dedup -\n"
        log = ("10:00:00 queue started, jobs=2\n10:00:00 start a/dedup on m (x) jobs=2\n"
               "10:00:01 start b/dedup on m (x) jobs=2\n11:00:00 queue started, jobs=2\n"
               "11:00:00 skip a/dedup (claimed: /r/.claims/a__dedup exists)\n11:00:01 start c/dedup on m (x) jobs=2\n")
        s = self.state(log, at(11, 0, 1), kind="loop-bench", queue=q)
        self.assertEqual((list(s["running"]), s["done"]), (["c/dedup"], set()))
        # One at a time there is no queue-started line: the next start or skip ends the last agent.
        s = self.state("10:00:00 start a/dedup on m (x)\n11:00:00 skip b/dedup (final.py exists)\n",
                       at(11, 0), kind="loop-bench", queue=q)
        self.assertEqual((s["running"], s["state"]), ({}, "between agents"))
        s = self.state("10:00:00 start a/dedup on m (x)\n11:00:00 STOP file found\n11:00:00 queue finished\n",
                       at(11, 0), kind="loop-bench", queue=q)
        self.assertEqual((s["running"], s["state"]), ({}, "stopped by STOP"))
        s = self.state("10:00:00 start a/dedup on m (x)\n11:00:00 STOP file found\n", at(11, 0), kind="loop-bench", queue=q)
        self.assertEqual(s["running"], {})

    def test_the_guard_log_reports_its_latest_state(self):
        g = progress.guard_state
        self.assertIsNone(g([], at(3, 0)))
        lines = ["02:10:00 limit seen in s4/dedup agent.err; STOP", "waiting for the limit to reset"]
        self.assertEqual(g(lines, at(2, 10)), ("waiting for the usage limit to reset", None, True))
        self.assertEqual(g(lines[:1], at(2, 10)),
                         ("a usage limit was hit and the queue was stopped", at(2, 10), True))
        lines += ["23:59:00 waiting for the limit to reset", "00:20:00 limit reset; resuming", ""]
        self.assertEqual(g(lines, at(0, 20, 0, DAY + datetime.timedelta(days=1))),
                         ("the usage limit reset and the queue resumed",
                          at(0, 20, 0, DAY + datetime.timedelta(days=1)), False))
        self.assertEqual(g(["07:00:00 guarded queue done"], at(7, 0)), ("the guard is done", at(7, 0), False))
        self.assertEqual(g(["07:00:00 something new"], at(7, 0)), ("last line: something new", at(7, 0), False))

    def test_a_guard_pause_keeps_the_estimate(self):
        q = "a/dedup -\nb/dedup -\nc/dedup -\n"
        log = ("02:00:00 start a/dedup on m (x)\n02:10:00 done a/dedup exit=0 final=yes\n"
               "02:10:00 STOP file found\n02:10:00 queue finished\n")
        run = self.loop_bench(q, finals=["a/dedup"], log=log, last_write=at(2, 10),
                              guard="02:10:30 limit seen in a/dedup; STOP\n02:11:00 waiting for the limit to reset\n")
        out = self.main_out(run)
        self.assertIn("guard: waiting for the usage limit to reset at 02:11:00", out)
        self.assertIn("left ≈ 20 min (estimate: 2 agent(s) at the median, after the limit resets)", out)

    def test_arms_reads_finished_agents_and_load_max(self):
        run = self.arms(None)
        for i, body in (("a1", '{"is_error": false}'), ("b2", '{"subtype": "error_max_budget_usd"}'),
                        ("c3", '{"is_error": true}'), ("d4", "{trunc")):
            os.makedirs(os.path.join(run, i))
            with open(os.path.join(run, i, "agent.json"), "w") as f:
                f.write(body)
        self.assertEqual(progress.finished_in_workspaces("arms", run, ["a1", "b2", "c3", "d4", "e5"]), {"a1", "b2"})
        with open(os.path.join(run, ".harness", "queue.log"), "w") as f:
            f.write("10:00:00 start c3 (x)\n10:02:00 done c3 exit=0\n")
        out = self.main_out(run)
        self.assertIn("done 3/4 (75%)", out)
        self.assertIn("against the gate 4: ", out)  # from .harness/LOAD_MAX: the log names no gate

    def test_main_reads_only_and_finds_both_layouts(self):
        run = self.arms("10:00:00 start a1 (x)\n10:01:00 done a1 exit=0\n10:01:00 queue finished\n",
                        last_write=at(10, 1))
        lb = os.path.join(self.tmp, "runs", "r9")
        os.makedirs(lb)
        with open(os.path.join(lb, "queue"), "w") as f:
            f.write("p/dedup -\n")
        with open(os.path.join(lb, "guard.log"), "w") as f:
            f.write("01:00:00 guarded queue done\n")

        def snapshot():
            return sorted((os.path.relpath(os.path.join(d, n), self.tmp), os.stat(os.path.join(d, n)).st_mtime_ns)
                          for d, ds, fs in os.walk(self.tmp) for n in ds + fs)
        before = snapshot()
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(progress.main([run]), 0)
            self.assertEqual(progress.main([lb]), 0)
        self.assertIn("run-x (arms queue)\ndone 1/4 (25%)\nstate: finished at 10:01:00", out.getvalue())
        self.assertIn("r9 (loop-bench queue)\ndone 0/1 (0%)\nstate: not started", out.getvalue())
        self.assertEqual(snapshot(), before)
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(progress.main([self.tmp]), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
