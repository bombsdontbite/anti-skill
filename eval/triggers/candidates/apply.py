"""Applies one trigger candidate to a copy of the plugin, never to the shipped one.

usage: python3 eval/triggers/candidates/apply.py CANDIDATE PLUGIN_DIR
CANDIDATE is a folder name here (desc, hook-start, hook-prompt); PLUGIN_DIR is plugins/anti-skill
inside a separate worktree made for that arm.
"""
import json
import re
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SHIPPED = (HERE.parents[2] / "plugins" / "anti-skill").resolve()


def set_description(skill_md: Path, text: str) -> None:
    body = skill_md.read_text(encoding="utf-8")
    head, sep, rest = body.partition("\n---\n")
    if not head.startswith("---\n") or not sep:
        raise SystemExit(f"{skill_md}: no frontmatter")
    # A JSON string is a valid YAML double-quoted scalar.
    new_head, n = re.subn(r"(?m)^description: .*$", lambda _: "description: " + json.dumps(text, ensure_ascii=False), head)
    if n != 1:
        raise SystemExit(f"{skill_md}: expected one description line, found {n}")
    skill_md.write_text(new_head + sep + rest, encoding="utf-8")


def main(argv):
    if len(argv) != 3:
        raise SystemExit(__doc__)
    cand, plugin = HERE / argv[1], Path(argv[2]).resolve()
    if not cand.is_dir() or cand.name.startswith((".", "_")):
        raise SystemExit(f"no candidate {argv[1]!r} in {HERE}")
    if plugin == SHIPPED:
        raise SystemExit(f"refusing to change the shipped plugin at {plugin}; use a separate worktree")
    if not (plugin / ".claude-plugin" / "plugin.json").is_file():
        raise SystemExit(f"{plugin} is not a plugin folder")
    descs = cand / "descriptions.json"
    if descs.is_file():
        for skill, text in json.loads(descs.read_text(encoding="utf-8")).items():
            set_description(plugin / "skills" / skill / "SKILL.md", text)
    hooks = cand / "hooks"
    if hooks.is_dir():
        if (plugin / "hooks").exists():
            raise SystemExit(f"{plugin / 'hooks'} exists; start from a clean worktree")
        shutil.copytree(hooks, plugin / "hooks")
    print(f"applied {cand.name} to {plugin}")


if __name__ == "__main__":
    main(sys.argv)
