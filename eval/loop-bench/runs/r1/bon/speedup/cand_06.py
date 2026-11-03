def usage_report(sessions, windows):
    """The reference loop as a filtered comprehension per window."""
    out = []
    for lo, hi in windows:
        ov = [r * ((e if e < hi else hi) - (s if s > lo else lo))
              for s, e, r in sessions if s < hi and e > lo]
        out.append((sum(ov), len(ov)))
    return out
