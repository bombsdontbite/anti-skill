cp "$(dirname "$0")/../_fixture/report.py" .
python3 - <<'EOF'
s = open("report.py").read()
old = """    seen = []
    for c in customers:
        if c not in seen:
            seen.append(c)
    return seen"""
assert old in s
open("report_v2.py", "w").write(s.replace(old, "    return list(dict.fromkeys(customers))"))
EOF
