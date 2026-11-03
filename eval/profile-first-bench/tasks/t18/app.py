"""Checks a month of timesheets for overlapping shifts and prints hours per team.

usage: python3 app.py timesheets.csv
"""
import csv
import sys

TEAMS = ["pick", "pack", "dispatch", "returns", "inbound", "yard"]


def open_sheet(path):
    f = open(path, newline="", encoding="utf-8")
    rows = csv.reader(f)
    next(rows)
    return rows


def find_overlaps(rows):
    """Shifts of one person on one day that overlap another of their shifts."""
    by_day, hours = {}, {}
    for person, team, day, start, end in rows:
        s, e = int(start), int(end)
        by_day.setdefault((person, day), []).append((s, e))
        hours[team] = hours.get(team, 0) + (e - s)
    overlaps = 0
    for shifts in by_day.values():
        for i in range(len(shifts)):
            a0, a1 = shifts[i]
            for j in range(i + 1, len(shifts)):
                b0, b1 = shifts[j]
                if a0 < b1 and b0 < a1:
                    overlaps += 1
    return overlaps, hours


def rota_grid():
    """Which team covers which quarter-hour of the week."""
    grid = {}
    for day in range(7):
        for q in range(96):
            grid[day, q] = TEAMS[(day * 96 + q) // 16 % len(TEAMS)]
    return grid


def main(argv):
    grid = rota_grid()
    overlaps, hours = find_overlaps(open_sheet(argv[0]))
    print(f"overlapping shift pairs: {overlaps}  rota slots: {len(grid)}")
    for team in TEAMS:
        print(f"  {team:9s} {hours.get(team, 0) / 60:10.1f} h")


if __name__ == "__main__":
    main(sys.argv[1:])
