"""Times report.dedup on 20k customers and checks the result; prints seconds (lower is better)."""
import time

import report

customers = [r[0] for r in report.load()]
expected = list(dict.fromkeys(customers))
start = time.perf_counter()
got = report.dedup(customers)
elapsed = time.perf_counter() - start
assert got == expected, "wrong result"
print(f"{elapsed:.4f}")
