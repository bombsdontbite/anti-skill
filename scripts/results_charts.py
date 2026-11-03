"""Draws RESULTS.md's charts from the committed score files, so a chart cannot drift from its data.

usage: python3 scripts/results_charts.py [--check] [--out DIR]

Writes assets/results/*.svg (or DIR). With --check it writes nothing and exits 1 if any committed
SVG differs from what it would write now. Same input, byte-identical output: no clock, no
randomness, fixed float formatting.
"""
import argparse, json, os, statistics, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join("assets", "results")
R29 = os.path.join("eval", "loop-bench", "runs", "r29")

W = 800
PAD = 24
PANEL_W = (W - 3 * PAD) / 2
TOP, BASE = 130.0, 370.0  # plot area: top of the axis and the zero line
AXIS_TOP = 25  # both panels share it, so their columns line up
ACCENT = "#e8590c"
INK = "#1f2328"
MUTED = "#57606a"
GRID = "#eaeef2"
FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"

# Arms of run 29, by label prefix (decide_r29.py): label lines, colour, prefix.
EVOLVE = (("Claude Code", "with evolve"), ACCENT, "r29n")
NUDGE = (("Plain, told to", "keep going"), "#8c959f", "r29u")
PLAIN = (("Plain", "Claude Code"), "#57606a", "r28pl")


def f(v):
    s = f"{v:.2f}"
    return "0.00" if s == "-0.00" else s


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def arm_scores(results, prefix):
    """Medians of the labels that start with prefix followed by a digit, as decide_r29.py matches them."""
    out = []
    for label in sorted(results):
        rest = label[len(prefix):]
        if label.startswith(prefix) and rest[:1].isdigit():
            out.append(results[label]["median"])
    return out


def text(x, y, s, size=13, fill=INK, anchor="start", weight="normal"):
    w = ' font-weight="600"' if weight == "bold" else ""
    a = f' text-anchor="{anchor}"' if anchor != "start" else ""
    return f'<text x="{f(x)}" y="{f(y)}" font-size="{size}" fill="{fill}"{a}{w}>{esc(s)}</text>'


def panel(x, title, bars, top_value, step, tick_fmt):
    """One bar chart from zero: bars of (label lines, colour, mean, value text)."""
    parts = [text(x, 98, title, 14, INK, weight="bold")]
    x0, x1 = x + 44, x + PANEL_W

    def sy(v):
        return BASE - v / top_value * (BASE - TOP)

    n = int(round(top_value / step))
    for k in range(n + 1):
        v = k * step
        colour = MUTED if k == 0 else GRID
        parts.append(f'<line x1="{f(x0)}" y1="{f(sy(v))}" x2="{f(x1)}" y2="{f(sy(v))}" stroke="{colour}" stroke-width="1"/>')
        parts.append(text(x0 - 8, sy(v) + 4, tick_fmt(v), 12, MUTED, "end"))
    slot = (x1 - x0) / len(bars)
    bw = 80.0
    for i, (label, colour, mean, value_s) in enumerate(bars):
        cx = x0 + slot * (i + 0.5)
        parts.append(f'<rect x="{f(cx - bw / 2)}" y="{f(sy(mean))}" width="{f(bw)}" height="{f(BASE - sy(mean))}" fill="{colour}"/>')
        parts.append(text(cx, sy(mean) - 8, value_s, 13, INK, "middle", "bold"))
        for j, ln in enumerate(label):
            parts.append(text(cx, BASE + 20 + 16 * j, ln, 12, INK, "middle"))
    return parts


def figure(title, subtitle, desc, body, height):
    head = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{height}" viewBox="0 0 {W} {height}" role="img" aria-labelledby="t d" font-family="{FONT}">',
        f'<title id="t">{esc(title)}</title>',
        f'<desc id="d">{esc(desc)}</desc>',
        f'<rect x="0.5" y="0.5" width="{W - 1}" height="{height - 1}" rx="8" fill="#ffffff" stroke="#d0d7de"/>',
        text(PAD, 36, title, 16, INK, weight="bold"),
        text(PAD, 58, subtitle, 13, MUTED),
    ]
    return "\n".join(head + body + ["</svg>"]) + "\n"


def load(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return json.load(fh)


def evolve_chart():
    """Run 29 on the secret test seed: dedup and cache, each arm's gain over plain's mean."""
    checks, body = [], []
    for i, (task, name) in enumerate((("dedup", "Near-duplicate finder"), ("cache", "Cache policy"))):
        res = load(os.path.join(R29, f"{task}_test.json"))["results"]
        arms = [(lab, col, arm_scores(res, pre)) for lab, col, pre in (EVOLVE, NUDGE, PLAIN)]
        if min(len(a[2]) for a in arms) == 0:
            raise SystemExit(f"{task}: an arm has no scores")
        base = statistics.mean(arms[-1][2])
        gains = [100 * (statistics.mean(a[2]) / base - 1) for a in arms[:2]]
        if min(gains) < 0 or max(gains) > AXIS_TOP:
            raise SystemExit(f"{task}: a gain falls outside the axis 0-{AXIS_TOP}%")
        bars = [(lab, col, g, f"{g:+.1f}%") for (lab, col, _), g in zip(arms, gains)]
        # Each gain and the file that states it: evolve's in RESULTS.md, the nudge's in run 29's
        # README (RESULTS.md gives evolve against the nudge instead).
        for (_, _, _, shown), src in zip(bars, ("RESULTS.md", os.path.join(R29, "README.md"))):
            checks.append((shown, src))
        body += panel(PAD + i * (PANEL_W + PAD), name, bars, AXIS_TOP, 5, lambda v: f"{v:.0f}%")
    desc = ("Bar charts of each group's gain over plain Claude Code's mean on a secret test set. "
            "Near-duplicate finder: evolve gains far more than plain told to keep going. Cache policy: "
            "both gain little, and about the same.")
    svg = figure("evolve against plain Claude Code, on a secret test set",
                 "Gain over plain Claude Code (plain = 0), mean per group. Higher is better.",
                 desc, body, int(BASE + 56))
    return svg, checks


CHARTS = {
    "evolve-run29.svg": evolve_chart,
}


def render():
    """{file name: (svg text, [(gain printed, the file that states it)])}."""
    return {name: fn() for name, fn in sorted(CHARTS.items())}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true", help="exit 1 if a committed SVG is stale")
    ap.add_argument("--out", default=os.path.join(ROOT, OUT))
    a = ap.parse_args(argv)
    stale = []
    for name, (svg, _) in render().items():
        path = os.path.join(a.out, name)
        data = svg.encode("utf-8")
        if a.check:
            try:
                with open(path, "rb") as fh:
                    same = fh.read() == data
            except FileNotFoundError:
                same = False
            if not same:
                stale.append(name)
        else:
            os.makedirs(a.out, exist_ok=True)
            with open(path, "wb") as fh:
                fh.write(data)
    if stale:
        print("stale or missing, run python3 scripts/results_charts.py: " + ", ".join(stale), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
