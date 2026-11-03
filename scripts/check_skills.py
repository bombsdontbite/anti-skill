"""Every skill (plugins/*/skills/*) has valid frontmatter and no broken relative link; the marketplace and plugin manifests parse.

Usage: python3 scripts/check_skills.py   Exits 1 and names each problem.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LINK = re.compile(r"\]\(([^)#\s]+)(?:#[^)]*)?\)")
problems = []

for skill in sorted(ROOT.glob("plugins/*/skills/*")):
    md = skill / "SKILL.md"
    if not md.is_file():
        problems.append(f"{skill.name}: no SKILL.md")
        continue
    text = md.read_text(encoding="utf-8")
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not m:
        problems.append(f"{skill.name}: SKILL.md has no frontmatter")
        continue
    fields = dict(re.findall(r"^(\w[\w-]*):\s*(.*)$", m.group(1), re.M))
    # A YAML parser reads ": " or " #" in an unquoted value (or its continuation lines) as a new key
    # or a comment; Claude Code is lenient, stricter loaders (GitHub, other tools) reject the file.
    key, value = None, {}
    for line in m.group(1).split("\n"):
        k = re.match(r"^(\w[\w-]*):\s*(.*)$", line)
        if k:
            key = k.group(1)
            value[key] = k.group(2)
        elif key:
            value[key] += " " + line.strip()
    for k, v in value.items():
        if v[:1] not in "\"'|>" and (": " in v or " #" in v or v[:1] in "[]{}&*!%@`,"):
            problems.append(f"{skill.name}: frontmatter {k} is not valid YAML as written; quote it")
    if fields.get("name") != skill.name:
        problems.append(f"{skill.name}: frontmatter name is {fields.get('name')!r}, not the folder name")
    desc = fields.get("description", "").strip()
    if not desc or len(desc) > 1024:
        problems.append(f"{skill.name}: description is empty or longer than 1024 characters ({len(desc)})")

def markdown_files():
    """Tracked and untracked-but-unignored .md files; git-ignored scratch (.work/) is skipped."""
    try:
        cmd = ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard", "--", "*.md"]
        out = subprocess.run(cmd, cwd=ROOT, capture_output=True, check=True).stdout
        return sorted({ROOT / p for p in out.decode().split("\0") if p})
    except (OSError, subprocess.CalledProcessError):
        return sorted(ROOT.glob("**/*.md"))


for md in markdown_files():
    if not md.exists():  # deleted in the work tree but still in the index
        continue
    rel = md.relative_to(ROOT).parts
    if any(p in rel for p in ("_work", ".venv", "node_modules")):
        continue
    if rel[:3] == ("eval", "loop-bench", "runs") and len(rel) > 5:  # agents' own workspaces
        continue
    if rel[:2] == ("eval", "runs") and rel[-1] != "README.md" and "skill" not in rel:  # model answers are data
        continue
    # An overlay file lands at the same path in the public export, beside the ref's files and the
    # other overlay files, so its links resolve from there.
    overlay = rel[:2] == ("scripts", "public_overlay")
    bases = [ROOT.joinpath(*rel[2:]).parent, md.parent] if overlay else [md.parent]
    text = re.sub(r"^(`{3,})[^\n]*\n.*?^\1[ \t]*$", "", md.read_text(encoding="utf-8"), flags=re.M | re.S)
    for target in LINK.findall(text):  # links inside fenced code are examples, not links
        if "://" in target or target.startswith("mailto:"):
            continue
        if not any((b / target).exists() for b in bases):
            problems.append(f"{md.relative_to(ROOT)}: link to {target} does not resolve")

for manifest in [ROOT / ".claude-plugin" / "marketplace.json", *ROOT.glob("plugins/*/.claude-plugin/plugin.json")]:
    try:
        json.loads(manifest.read_text())
    except (OSError, ValueError) as e:
        problems.append(f"{manifest.relative_to(ROOT)}: {e}")

# The release tag is cut from these: both manifests and the newest dated CHANGELOG section agree.
try:
    market = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text())
    versions = {p["name"]: p.get("version") for p in market["plugins"]}
    for manifest in ROOT.glob("plugins/*/.claude-plugin/plugin.json"):
        plugin = json.loads(manifest.read_text())
        if versions.get(plugin["name"]) != plugin.get("version"):
            problems.append(f"{manifest.relative_to(ROOT)}: version {plugin.get('version')} but marketplace.json "
                            f"says {versions.get(plugin['name'])}")
    dated = re.search(r"^## \[([^]]+)\] - \d{4}-\d{2}-\d{2}[ \t]*$", (ROOT / "CHANGELOG.md").read_text(), re.M)
    badge = re.search(r"img\.shields\.io/badge/version-([0-9][0-9A-Za-z.]*)-", (ROOT / "README.md").read_text(encoding="utf-8"))
    if badge and badge.group(1) not in versions.values():
        problems.append(f"README.md: version badge says {badge.group(1)}, no manifest carries that version")
    if dated and dated.group(1) not in versions.values():
        problems.append(f"CHANGELOG.md: newest dated section is {dated.group(1)}, no manifest carries that version")
except (OSError, ValueError, KeyError, TypeError) as e:
    problems.append(f"manifest versions: {e!r}")

print("\n".join(problems) or "skills ok")
sys.exit(1 if problems else 0)
