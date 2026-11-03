"""Tests for score_answers.py, on fake shares: python3 -B test_score_answers.py"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import score_answers as sa  # noqa: E402
import runner  # noqa: E402  (lab/ is on the path score_answers set)

with open(os.path.join(HERE, "lab", "manifest.json"), encoding="utf-8") as f:
    MANIFEST = json.load(f)

FAKE = {"tasks": {
    "t01": {"top": "spelling_import", "clock": "cpu", "components": {
        "spelling_import": {"share": {"median": 0.9}}, "confusion_cube": {"share": {"median": 0.001}},
        "correct_queries": {"share": {"median": 0.03}}}},
    "t05": {"top": "match_deliveries", "clock": "cpu", "toy": {"top": "build_rate_grid"}, "components": {
        "match_deliveries": {"share": {"median": 0.8}}, "build_rate_grid": {"share": {"median": 0.04}},
        "load_rows": {"share": {"median": 0.08}}}},
    "t17": {"top": "markup", "clock": "cpu", "components": {
        "markup": {"share": {"median": 0.63}}, "reading_stats": {"share": {"median": 0.27}},
        "slug_table": {"share": {"median": 0.03}}}},
    "t18": {"top": "find_overlaps", "clock": "cpu", "components": {
        "find_overlaps": {"share": {"median": 0.69}}, "open_sheet": {"share": {"median": 0.04}},
        "rota_grid": {"share": {"median": 0.0}}}},
}}


def where(tid, text):
    spec = MANIFEST["tasks"][tid]
    return sa.match(text, spec, sa.spans(tid, spec))


def app_line(tid, needle):
    with open(os.path.join(sa.TASKS, tid, "app.py"), encoding="utf-8") as f:
        return next(i for i, line in enumerate(f, 1) if needle in line)


class ParseShare(unittest.TestCase):
    def test_forms(self):
        self.assertEqual(sa.parse_share("62%"), 62)
        self.assertEqual(sa.parse_share(" ~62.5 % "), 62.5)
        self.assertEqual(sa.parse_share("60-70%"), 65)
        self.assertEqual(sa.parse_share("<1%"), 0.5)
        self.assertEqual(sa.parse_share("about 3,5%"), 3.5)
        self.assertIsNone(sa.parse_share("most of it"))


class Match(unittest.TestCase):
    def test_function_name(self):
        self.assertEqual(where("t02", "app.py:write_report"), "write_report")
        self.assertEqual(where("t02", "write_report()"), "write_report")
        self.assertEqual(where("t02", "app.py:parse_duration"), "parse_duration")

    def test_line_number_picks_innermost(self):
        n = app_line("t02", "if \"0\" <= ch <= \"9\"")
        self.assertEqual(where("t02", f"app.py:{n}"), "parse_duration")
        self.assertEqual(where("t02", f"app.py line {n}"), "parse_duration")

    def test_module_and_import_line(self):
        self.assertEqual(where("t01", "spelling.py"), "spelling_import")
        self.assertEqual(where("t01", "spelling.py:<module>"), "spelling_import")
        self.assertEqual(where("t01", f"app.py:{app_line('t01', 'import spelling')}"), "spelling_import")
        self.assertEqual(where("t01", "spelling.py:correct"), "correct_queries")

    def test_keywords_and_library_frames(self):
        self.assertEqual(where("t02", "json/encoder.py:_iterencode_dict"), "write_report")
        self.assertEqual(where("t06", "logging/__init__.py:emit"), "logging")
        self.assertEqual(where("t08", "sqlite3 commit"), "save_batch")

    def test_unmatched(self):
        self.assertIsNone(where("t02", "app.py:main"))
        self.assertIsNone(where("t02", "app.py:main (csv and json)"))  # a tie is not a match


class MatchHardTier(unittest.TestCase):
    def test_the_profiler_rows_name_the_misleading_component(self):
        self.assertEqual(where("t11", "app.py:domain_counts"), "domain_counts")
        self.assertEqual(where("t12", "app.py:price_basket"), "price_basket")
        self.assertEqual(where("t13", "json/decoder.py:raw_decode"), "load_cache")
        self.assertEqual(where("t14", "app.py:read_postings"), "read_postings")
        self.assertEqual(where("t15", "app.py:coverage"), "coverage")
        self.assertEqual(where("t17", "app.py:reading_stats"), "reading_stats")

    def test_the_measured_hot_spots(self):
        self.assertEqual(where("t11", f"app.py:{app_line('t11', 'ADDRESS = re.compile')}"), "addresses")
        self.assertEqual(where("t12", "app.py:AuditTrail.add"), "audit_trail")
        self.assertEqual(where("t12", "the audit trail keeping every basket (GC)"), "audit_trail")
        self.assertEqual(where("t13", "app.py:save_cache (atexit)"), "save_cache")
        self.assertEqual(where("t13", f"app.py:{app_line('t13', 'atexit.register')}"), "save_cache")
        self.assertEqual(where("t14", "indexer.py"), "start_indexer")
        self.assertEqual(where("t14", "indexer.py:tokens"), "start_indexer")
        self.assertEqual(where("t15", "app.py:pack"), "pack")
        self.assertEqual(where("t16", "app.py:drop_resends"), "drop_resends")
        self.assertEqual(where("t17", "markup.py"), "markup")
        self.assertEqual(where("t17", "markup.py:emphasis"), "markup")
        self.assertEqual(where("t17", f"app.py:{app_line('t17', 'markup.emphasis')}"), "markup")
        self.assertEqual(where("t18", "app.py:find_overlaps"), "find_overlaps")

    def test_a_named_function_beats_a_line_number(self):
        loop = app_line("t18", "for person, team, day")
        self.assertEqual(where("t18", f"app.py:open_sheet (csv.reader, consumed at line {loop})"), "open_sheet")
        self.assertEqual(where("t18", f"app.py:open_sheet (consumed in find_overlaps line {loop})"), "open_sheet")
        self.assertEqual(where("t18", f"find_overlaps line {loop} (the read loop)"), "find_overlaps")
        scan = app_line("t11", "ADDRESS = re.compile")
        self.assertEqual(where("t11", f"app.py:domain_counts (line {scan}, the regex scan)"), "domain_counts")

    def test_a_line_number_at_the_head_beats_a_function_in_the_context(self):
        loop = app_line("t18", "for person, team, day")
        self.assertEqual(where("t18", f"app.py:{loop} (the reader open_sheet returns)"), "find_overlaps")
        rows = app_line("t02", "csv.DictReader(f)")
        self.assertEqual(where("t02", f"app.py:{rows} (DictReader row loop, before parse_duration)"), "load_orders")
        events = app_line("t12", "def load_events") + 2
        self.assertEqual(where("t12", f"app.py:{events} (json per line; events later go to add)"), "load_events")

    def test_main_is_still_a_miss(self):
        for tid in ("t11", "t12", "t13", "t14", "t15", "t16", "t17", "t18"):
            self.assertIsNone(where(tid, "app.py:main"), tid)


class ScoreRun(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.shares = os.path.join(self.tmp, "shares.json")
        with open(self.shares, "w") as f:
            json.dump(FAKE, f)
        self.truth = sa.truths(MANIFEST, self.shares, False)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def run_dir(self, tid, answer, arm="plain"):
        d = os.path.join(self.tmp, arm, tid)
        shutil.copytree(os.path.join(sa.TASKS, tid), d)
        if answer is not None:
            with open(os.path.join(d, "ANSWER.txt"), "w") as f:
                f.write(answer)
        return d

    def score(self, tid, answer, threshold=10, arm="plain"):
        d = self.run_dir(tid, answer, arm)
        return sa.score_run(d, tid, MANIFEST["tasks"][tid], self.truth[tid], threshold)

    def test_hit_with_share_error(self):
        r = self.score("t01", "hotspot: spelling.py:<module> | 80% | -X importtime\n"
                              "cleared: app.py:confusion_cube | 0.1% | timed it\n")
        self.assertTrue(r["top1"])
        self.assertAlmostEqual(r["top1_share_error"], 10)
        self.assertFalse(r["decoy_named"])
        self.assertTrue(r["decoy_cleared"])

    def test_decoy_named_and_miss(self):
        r = self.score("t05", "- hotspot: `app.py:build_rate_grid` | 70% | cProfile on the sample\n"
                              "hotspot: app.py:load_rows | 20% |\n")
        self.assertFalse(r["top1"])
        self.assertFalse(r["topk"])
        self.assertTrue(r["decoy_named"])
        self.assertTrue(r["named_toy_top"])
        self.assertEqual(sorted(round(e) for e in r["share_errors"]), [12, 66])

    def test_decoy_below_threshold_is_not_named(self):
        r = self.score("t05", "hotspot: app.py:match_deliveries | 85% | x\n"
                              "hotspot: app.py:build_rate_grid | 4% | x\n")
        self.assertTrue(r["top1"])
        self.assertFalse(r["decoy_named"])

    def test_a_component_split_over_lines_is_scored_on_its_sum(self):
        r = self.score("t18", "hotspot: app.py:find_overlaps (lines 26-32, pair loop) | 46% | x\n"
                              "hotspot: app.py:open_sheet (consumed at line 21) | 28% | x\n"
                              "hotspot: app.py:find_overlaps (lines 21-24, grouping) | 22% | x\n"
                              "hotspot: app.py:main | 2% | x\n")
        self.assertTrue(r["top1"])
        self.assertEqual(r["stated_shares"], {"find_overlaps": 68, "open_sheet": 28})
        self.assertAlmostEqual(r["top1_share_error"], 1)
        self.assertEqual(sorted(round(e) for e in r["share_errors"]), [1, 24])
        self.assertEqual(r["unmatched"], ["app.py:main"])

    def test_top1_is_the_first_line_and_the_sum_is_reported_beside_it(self):
        r = self.score("t17", "hotspot: app.py:reading_stats | 26% | x\n"
                              "hotspot: markup.py:emphasis | 14% | x\n"
                              "hotspot: markup.py:typography | 11% | x\n"
                              "hotspot: markup.py:glossary | 10% | x\n")
        self.assertFalse(r["top1"])
        self.assertIsNone(r["top1_share_error"])
        self.assertTrue(r["top1_by_sum"])
        self.assertTrue(r["topk"])
        self.assertEqual(sorted(round(e) for e in r["share_errors"]), [1, 28])

    def test_a_part_listed_after_its_whole_is_not_summed(self):
        r = self.score("t17", "hotspot: markup.py:escape, typography, emphasis (the passes) | 52% | x\n"
                              "hotspot: app.py:reading_stats | 25% | x\n"
                              "hotspot: markup.py:emphasis | 11% | x\n"
                              "hotspot: markup.py:escape, typography, emphasis (the passes) | 52% | x\n")
        self.assertEqual(r["stated_shares"], {"markup": 52, "reading_stats": 25})
        self.assertAlmostEqual(r["top1_share_error"], 11)
        self.assertEqual([i.get("repeat") for i in r["items"]], [False, False, True, True])

    def test_a_tie_in_the_sum_is_no_top(self):
        r = self.score("t17", "hotspot: markup.py:emphasis | 20% | x\nhotspot: app.py:reading_stats | 20% | x\n")
        self.assertTrue(r["top1"])
        self.assertFalse(r["top1_by_sum"])

    def test_decoy_threshold_applies_to_the_sum(self):
        one = self.score("t18", "hotspot: app.py:find_overlaps | 70% | x\nhotspot: app.py:rota_grid | 6% | x\n")
        self.assertFalse(one["decoy_named"])
        two = self.score("t18", "hotspot: app.py:find_overlaps | 70% | x\nhotspot: app.py:rota_grid | 6% | x\n"
                                "hotspot: app.py:rota_grid (inner loop) | 6% | x\n", arm="two")
        self.assertTrue(two["decoy_named"])
        bare = self.score("t18", "hotspot: app.py:find_overlaps | 70% | x\nhotspot: app.py:rota_grid | ? | x\n",
                          arm="bare")
        self.assertTrue(bare["decoy_named"])

    def test_missing_invalid_modified(self):
        self.assertEqual(self.score("t01", None)["status"], "missing")
        self.assertEqual(self.score("t05", "the grid is slow\n")["status"], "invalid")
        d = self.run_dir("t01", "hotspot: spelling.py | 90% | x\n", arm="edited")
        with open(os.path.join(d, "app.py"), "a") as f:
            f.write("# edited\n")
        r = sa.score_run(d, "t01", MANIFEST["tasks"]["t01"], self.truth["t01"], 10)
        self.assertEqual(r["modified"], ["app.py"])

    def test_cli_fails_closed(self):
        self.run_dir("t01", "hotspot: spelling.py | 90% | x\n")
        cmd = [sys.executable, "-B", os.path.join(HERE, "score_answers.py"), os.path.join(self.tmp, "plain"),
               "--shares", self.shares]
        ok = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(ok.returncode, 0, ok.stderr)
        self.assertIn("TOTAL", ok.stdout)
        self.run_dir("t02", "hotspot: app.py:write_report | 90% | x\n")  # not in the fake shares
        bad = subprocess.run(cmd, capture_output=True, text=True)
        self.assertNotEqual(bad.returncode, 0)
        empty = subprocess.run(cmd[:3] + [os.path.join(self.tmp, "nothing"), "--shares", self.shares],
                               capture_output=True, text=True)
        self.assertIn("no runs", empty.stderr)
        self.assertNotEqual(empty.returncode, 0)

    def test_wall_only_shares_are_refused(self):
        old = {"tasks": {t: {k: v for k, v in e.items() if k != "clock"} for t, e in FAKE["tasks"].items()}}
        with open(self.shares, "w") as f:
            json.dump(old, f)
        with self.assertRaises(SystemExit) as cm:
            sa.truths(MANIFEST, self.shares, False)
        self.assertIn("wall time alone", str(cm.exception))


class HarnessLaunch(unittest.TestCase):
    """The lab's child processes hash strings alike on every run; under the old -I they did not."""

    def hashes(self, flags):
        work = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, work)
        os.makedirs(os.path.join(work, ".out"))
        cmd = [sys.executable, *flags, "-c", "print(hash('abc'))"]
        return [runner.run(cmd, work, f"h{i}")["sha"] for i in range(2)]

    def test_hash_seed_holds(self):
        a, b = self.hashes(runner.HARNESS_FLAGS)
        self.assertEqual(a, b)
        a, b = self.hashes(["-I"])
        self.assertNotEqual(a, b)


if __name__ == "__main__":
    unittest.main()
