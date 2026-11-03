"""RESULTS.md's charts: deterministic, --check catches a stale or missing SVG, and every gain a
chart prints is stated in the file it is cited from."""
import os, shutil, sys, tempfile, unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import results_charts as rc  # noqa: E402


class ResultsCharts(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_same_input_same_bytes(self):
        self.assertEqual(rc.render(), rc.render())

    def test_committed_svgs_are_current(self):
        self.assertEqual(rc.main(["--check"]), 0)

    def test_check_fails_on_stale_and_missing(self):
        self.assertEqual(rc.main(["--check", "--out", self.tmp]), 1)  # nothing written yet
        self.assertEqual(rc.main(["--out", self.tmp]), 0)
        self.assertEqual(rc.main(["--check", "--out", self.tmp]), 0)
        name = sorted(rc.CHARTS)[0]
        path = os.path.join(self.tmp, name)
        with open(path, "ab") as fh:
            fh.write(b" ")
        self.assertEqual(rc.main(["--check", "--out", self.tmp]), 1)
        os.remove(path)
        self.assertEqual(rc.main(["--check", "--out", self.tmp]), 1)

    def test_every_printed_gain_is_stated_where_it_is_cited(self):
        for name, (svg, checks) in rc.render().items():
            self.assertTrue(checks, name)
            for shown, src in checks:
                self.assertIn(f">{shown}<", svg, f"{name}: {shown} is not drawn")
                with open(os.path.join(rc.ROOT, src), encoding="utf-8") as fh:
                    self.assertIn(shown, fh.read(), f"{name} prints {shown}, which {src} does not state")

    def test_every_chart_is_embedded(self):
        with open(os.path.join(rc.ROOT, "RESULTS.md"), encoding="utf-8") as fh:
            results = fh.read()
        for name in rc.CHARTS:
            self.assertIn(f"({rc.OUT}/{name})".replace(os.sep, "/"), results)


if __name__ == "__main__":
    unittest.main()
