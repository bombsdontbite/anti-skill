"""Ingests smart-meter readings into readings.db, rejecting meter ids that fail their check digit.

usage: python3 app.py readings.csv
"""
import csv
import os
import sqlite3
import sys

DB = "readings.db"
BATCH = 5  # small batches: a crash mid-file loses at most a few readings


def luhn_ok(number):
    total = 0
    for i, ch in enumerate(reversed(number)):
        d = ord(ch) - 48
        if i % 2:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def parse_rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        r = csv.reader(f)
        next(r)
        return [(meter, ts, float(kwh)) for meter, ts, kwh in r]


def open_db(path):
    for p in (path, path + "-journal"):
        if os.path.exists(p):
            os.remove(p)
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE readings (meter TEXT, ts TEXT, kwh REAL)")
    conn.commit()
    return conn


def save_batch(conn, batch):
    conn.executemany("INSERT INTO readings VALUES (?, ?, ?)", batch)
    conn.commit()


def main(argv):
    rows = parse_rows(argv[0])
    conn = open_db(DB)
    batch, rejected = [], 0
    for meter, ts, kwh in rows:
        if not luhn_ok(meter):
            rejected += 1
            continue
        batch.append((meter, ts, kwh))
        if len(batch) == BATCH:
            save_batch(conn, batch)
            batch = []
    if batch:
        save_batch(conn, batch)
    conn.commit()
    count, total = conn.execute("SELECT COUNT(*), ROUND(SUM(kwh), 3) FROM readings").fetchone()
    print(f"rows: {len(rows)}  stored: {count}  rejected: {rejected}  total kWh: {total}")
    top = conn.execute("SELECT meter, ROUND(SUM(kwh), 3) AS s FROM readings GROUP BY meter "
                       "ORDER BY s DESC, meter LIMIT 5").fetchall()
    for meter, s in top:
        print(f"  {meter}  {s}")
    conn.close()


if __name__ == "__main__":
    main(sys.argv[1:])
