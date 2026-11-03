"""Tests for measurers.py's reading of a profile, on made-up stats: python3 -B test_measurers.py"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import measurers as pm  # noqa: E402

M = pm.runner.manifest()["tasks"]
LIB = os.path.join(os.sep, "usr", "lib", "python3.15")


def row(tt, ct, callers=None):
    return (1, 1, tt, ct, callers or {})


def pick(tid, stats, col=2):
    root = os.path.realpath(os.path.join(pm.runner.TASKS, tid))
    return pm.pick(stats, root, M[tid], pm.sa.spans(tid, M[tid]), col)


class Pick(unittest.TestCase):
    def test_builtin_row_is_charged_to_its_caller_in_the_task(self):
        main = ("app.py", 46, "main")
        read_postings = ("app.py", 25, "read_postings")
        communicate = (os.path.join(LIB, "subprocess.py"), 1180, "communicate")
        read = ("~", 0, "<method 'read' of '_io.BufferedReader' objects>")
        stats = {main: row(0.01, 1.0), read_postings: row(0.0, 0.95, {main: (1, 1, 0, 0.95)}),
                 communicate: row(0.0, 0.95, {read_postings: (1, 1, 0, 0.95)}),
                 read: row(0.94, 0.94, {communicate: (1, 1, 0.94, 0.94)})}
        where, comp, share = pick("t14", stats)
        self.assertEqual(comp, "read_postings")
        self.assertEqual(where, "app.py:25 read_postings")
        self.assertEqual(share, 98.9)

    def test_library_row_is_read_by_keyword_first(self):
        emit = (os.path.join(LIB, "logging", "__init__.py"), 1100, "emit")
        apply_rules = ("app.py", 42, "apply_rules")
        stats = {emit: row(0.5, 0.5, {apply_rules: (1, 1, 0.5, 0.5)}), apply_rules: row(0.1, 0.6)}
        self.assertEqual(pick("t06", stats)[1], "logging")

    def test_rows_that_name_no_component_are_skipped(self):
        main = ("app.py", 63, "main")
        module = ("app.py", 1, "<module>")
        stats = {main: row(0.6, 1.0), module: row(0.3, 1.0), ("app.py", 14, "reading_stats"): row(0.1, 0.1)}
        self.assertEqual(pick("t17", stats)[1], "reading_stats")
        self.assertEqual(pick("t17", stats, col=3)[1], "reading_stats")

    def test_cumtime_reads_only_task_rows_and_helper_modules(self):
        build = ("spelling.py", 22, "_build_variants")
        module = ("spelling.py", 1, "<module>")
        exec_ = ("~", 0, "<built-in method builtins.exec>")
        stats = {exec_: row(0.0, 2.0), module: row(0.01, 1.5), build: row(1.4, 1.4)}
        where, comp, _ = pick("t01", stats, col=3)
        self.assertEqual((where, comp), ("spelling.py:<module>", "spelling_import"))

    def test_nothing_named(self):
        self.assertEqual(pick("t02", {("app.py", 80, "main"): row(1.0, 1.0)}), (None, None, None))


class Inputs(unittest.TestCase):
    def test_casual_runs_on_what_ships_or_the_defaults(self):
        self.assertEqual(pm.casual_input(M["t05"]), (None, ["fixtures/sample.csv"]))
        self.assertEqual(pm.casual_input(M["t16"]), ([], ["payments.csv"]))
        self.assertEqual(pm.casual_input(M["t11"]), ([], ["mailbox.txt"]))

    def test_tiers(self):
        self.assertEqual(sorted(t for t in M if pm.tier_of(M[t]) == "hard"),
                         [f"t{i}" for i in range(11, 19)])


if __name__ == "__main__":
    unittest.main()
