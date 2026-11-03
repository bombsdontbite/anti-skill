import sys
import types

from stubkit import ReplayAfter, Stub

PASSES = ["escape", "typography", "emphasis", "links", "tickets", "abbreviations", "glossary"]


class Markup(Stub):
    """markup.py is never imported: every pass hands its words on, and wrap() returns the
    recorded HTML of each block."""

    def __init__(self):
        self.html = []

    def before_import(self, ctx):
        if ctx.record:
            return
        it = iter(ctx.load("markup_wrap"))
        mod = types.ModuleType("markup")
        mod.block_kind = lambda words: ("", words)
        for name in PASSES:
            setattr(mod, name, lambda words, *_rest: words)
        mod.wrap = lambda kind, words: next(it)
        sys.modules["markup"] = mod

    def after_import(self, app, ctx):
        if ctx.record:
            real, html = app.markup.wrap, self.html

            def wrap(kind, words):
                out = real(kind, words)
                html.append(out)
                return out
            app.markup.wrap = wrap

    def finish(self, ctx):
        if ctx.record:
            ctx.save("markup_wrap", self.html)


STUBS = {
    "markup": Markup(),
    "reading_stats": ReplayAfter("reading_stats"),
    "slug_table": ReplayAfter("slug_table"),
}
