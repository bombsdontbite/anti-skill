"""Local checks of the trigger candidates; no model is called. python3 eval/triggers/candidates/test_candidates.py"""
import json
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SHIPPED = ROOT / "plugins" / "anti-skill"
HOOK = HERE / "hook-prompt" / "hooks" / "prompt-keywords.sh"


def shipped_description(skill):
    head = (SHIPPED / "skills" / skill / "SKILL.md").read_text(encoding="utf-8").split("\n---\n", 1)[0]
    return re.search(r"(?m)^description: (.*)$", head).group(1).strip('"')


def run_hook(stdin: bytes, env=None):
    # The command hooks.json runs, with the plugin root filled in.
    cmd = f'sh "{HOOK}" 2>/dev/null || true'
    return subprocess.run(["/bin/sh", "-c", cmd], input=stdin, capture_output=True, timeout=10, env=env)


def prompt_json(text, last=True):
    # Claude Code writes raw UTF-8 JSON on one line; key order is not promised.
    fields = {"session_id": "s", "transcript_path": "/h/.claude/projects/-work-slow-bench/s.jsonl",
              "cwd": "/work/slow-profile-bench", "hook_event_name": "UserPromptSubmit"}
    fields = {**fields, "prompt": text} if last else {"prompt": text, **fields}
    return json.dumps(fields, ensure_ascii=False).encode()


class Descriptions(unittest.TestCase):
    def test_each_is_shorter_than_the_shipped_one_and_names_the_other_skill(self):
        descs = json.loads((HERE / "desc" / "descriptions.json").read_text(encoding="utf-8"))
        self.assertEqual(set(descs), {"evolve", "profile-first"})
        for skill, text in descs.items():
            self.assertLess(len(text), len(shipped_description(skill)), skill)
            self.assertTrue(text.startswith("Use when"), skill)
        self.assertIn("profile-first", descs["evolve"])
        self.assertIn("evolve", descs["profile-first"])


class HookPrompt(unittest.TestCase):
    def test_fires_on_speed_and_score_words(self):
        for text in ("Can you speed up this parser?", "the scorer gives 0.71, push the Score up",
                     "Optimise the packing step", "this job got slower last week", "profile the export",
                     "line one\nSlow since the upgrade", 'it prints "done" too late: make it faster',
                     "café: optimizing the menu loader", "BENCHMARKS look bad"):
            for last in (True, False):
                out = run_hook(prompt_json(text, last))
                self.assertEqual(out.returncode, 0, text)
                self.assertTrue(out.stdout.startswith(b"anti-skill: "), (text, last))
                self.assertEqual(out.stdout.count(b"\n"), 1, text)

    def test_silent_without_a_keyword_even_when_other_fields_have_one(self):
        for text in ("explain what this function does", "fix the off-by-one in pagination",
                     "explain it quickly", 'set "prompt": "x" in the config', "rename fastercsv"):
            for last in (True, False):
                out = run_hook(prompt_json(text, last))
                self.assertEqual((out.returncode, out.stdout), (0, b""), (text, last))

    def test_exits_zero_and_silent_on_bad_input(self):
        for stdin in (b"", b"not json slow", b"[1, 2]", b'{"prompt": 5}', b"\xff\xfe slow", b'{"prompt": null}',
                      b'{"prompt": "unterminated slow'):
            out = run_hook(stdin)
            self.assertEqual((out.returncode, out.stdout, out.stderr), (0, b"", b""), stdin)

    def test_exits_zero_and_silent_without_its_tools(self):
        out = subprocess.run(["/bin/sh", str(HOOK)], input=prompt_json("faster"), capture_output=True, timeout=10,
                             env={"PATH": "/nonexistent"})
        self.assertEqual((out.returncode, out.stdout), (0, b""))

    def test_median_run_under_50_ms_and_a_large_paste_under_a_second(self):
        times = []
        for _ in range(15):
            t = time.perf_counter()
            run_hook(prompt_json("make the benchmark score higher"))
            times.append(time.perf_counter() - t)
        self.assertLess(statistics.median(times), 0.050, f"median {statistics.median(times) * 1000:.1f} ms")
        paste = "def f(x):\n    return x + 1  # \"quoted\" \\ text\n" * 20000 + "why is it slow?"
        t = time.perf_counter()
        out = run_hook(prompt_json(paste))
        self.assertLess(time.perf_counter() - t, 1.0)
        self.assertTrue(out.stdout.startswith(b"anti-skill: "))


class HookFiles(unittest.TestCase):
    def test_hooks_files_parse_and_name_the_plugin_root(self):
        for cand, event in (("hook-start", "SessionStart"), ("hook-prompt", "UserPromptSubmit")):
            cfg = json.loads((HERE / cand / "hooks" / "hooks.json").read_text(encoding="utf-8"))
            (cmd,) = [h["command"] for m in cfg["hooks"][event] for h in m["hooks"]]
            self.assertIn('"${CLAUDE_PLUGIN_ROOT}"/hooks/', cmd)
            self.assertTrue(cmd.endswith("|| true"), cand)

    def test_session_start_text_is_two_sentences_at_most(self):
        text = (HERE / "hook-start" / "hooks" / "session-start.txt").read_text(encoding="utf-8")
        self.assertLessEqual(len(re.findall(r"[.!?](?:\s|$)", text)), 2)
        self.assertLess(len(text), 300)


class Apply(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.plugin = self.tmp / "anti-skill"
        shutil.copytree(SHIPPED, self.plugin)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def apply(self, cand, target):
        return subprocess.run([sys.executable, str(HERE / "apply.py"), cand, str(target)], capture_output=True, text=True)

    def test_refuses_the_shipped_plugin(self):
        out = self.apply("desc", SHIPPED)
        self.assertNotEqual(out.returncode, 0)
        self.assertIn("refusing", out.stderr)

    def test_desc_replaces_only_the_description_lines(self):
        before = {s: (self.plugin / "skills" / s / "SKILL.md").read_text(encoding="utf-8") for s in ("evolve", "profile-first")}
        self.assertEqual(self.apply("desc", self.plugin).returncode, 0)
        descs = json.loads((HERE / "desc" / "descriptions.json").read_text(encoding="utf-8"))
        for s, old in before.items():
            new = (self.plugin / "skills" / s / "SKILL.md").read_text(encoding="utf-8")
            changed = [(a, b) for a, b in zip(old.splitlines(), new.splitlines()) if a != b]
            self.assertEqual(len(changed), 1, s)
            self.assertEqual(json.loads(changed[0][1][len("description: "):]), descs[s])
            self.assertEqual(len(old.splitlines()), len(new.splitlines()))

    def test_hook_candidates_add_a_hooks_folder_once(self):
        self.assertEqual(self.apply("hook-prompt", self.plugin).returncode, 0)
        self.assertTrue((self.plugin / "hooks" / "hooks.json").is_file())
        self.assertNotEqual(self.apply("hook-start", self.plugin).returncode, 0)


if __name__ == "__main__":
    unittest.main()
