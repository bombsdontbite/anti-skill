def usage_report(sessions, windows):
    """For each window, the rate-weighted overlap with every session and how many sessions touch it.

    sessions: list of (start, end, rate) ints, start < end, half-open [start, end).
    windows:  list of (lo, hi) ints, lo < hi, half-open [lo, hi).
    Returns a list of (usage, count): usage = sum of rate * overlap length, count = number of
    sessions whose overlap with the window is longer than zero.
    """
    report = []
    for lo, hi in windows:
        usage = 0
        count = 0
        for start, end, rate in sessions:
            a = max(start, lo)
            b = min(end, hi)
            if b > a:
                usage += rate * (b - a)
                count += 1
        report.append((usage, count))
    return report
