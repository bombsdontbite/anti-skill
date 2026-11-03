"""The help-centre's lightweight markup, one pass per feature over a block's words."""

QUOTES = {"--": "&ndash;", "---": "&mdash;", "...": "&hellip;", "(c)": "&copy;"}
ABBR = {"FAQ": "Frequently asked questions", "BLIK": "Polish mobile payments", "PIN": "Card PIN",
        "OTP": "One-time password", "VAT": "Value-added tax", "SMS": "Text message"}
GLOSSARY = {"voucher", "refund", "subscription", "courier", "tracking"}


def block_kind(words):
    first = words[0]
    if first[0] == "#":
        return "h" + str(min(len(first), 4)), words[1:]
    if first == "-" or first == "*":
        return "li", words[1:]
    if first == ">":
        return "blockquote", words[1:]
    return "p", words


def escape(words):
    return [w.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            if "&" in w or "<" in w or ">" in w else w for w in words]


def typography(words):
    return [QUOTES[w] if w in QUOTES else (w[:-1] + "&rsquo;" if w[-1:] == "'" else w) for w in words]


def emphasis(words):
    return [f"<strong>{w[2:-2]}</strong>" if w[:2] == "**" and w[-2:] == "**" and w[2:-2]
            else f"<em>{w[1:-1]}</em>" if w[0] == "_" and w[-1] == "_" and w[1:-1]
            else f"<code>{w[1:-1]}</code>" if w[0] == "`" and w[-1] == "`" and w[1:-1]
            else w for w in words]


def links(words, base):
    return [f'<a href="{base}{w[w.index("](") + 2:-1]}">{w[1:w.index("](")]}</a>'
            if w[0] == "[" and w[-1] == ")" and "](" in w else w for w in words]


def tickets(words, base):
    return [f'<a href="{base}tickets/{w[1:]}">{w}</a>' if w[0] == "#" and w[1:].isdigit() else w
            for w in words]


def abbreviations(words):
    return [f'<abbr title="{ABBR[w]}">{w}</abbr>' if w in ABBR else w for w in words]


def glossary(words, seen):
    out = []
    for w in words:
        if w in GLOSSARY and w not in seen:
            seen.add(w)
            w = f'<dfn id="g-{w}">{w}</dfn>'
        out += (w,)
    return out


def wrap(kind, words):
    return f"<{kind}>{' '.join(words)}</{kind}>"
