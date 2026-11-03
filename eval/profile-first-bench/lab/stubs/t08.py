from stubkit import Replace, Replay


def save_without_commit(conn, batch):
    # main() commits once after the loop, so the stored rows are the same.
    conn.executemany("INSERT INTO readings VALUES (?, ?, ?)", batch)


STUBS = {
    "save_batch": Replace("save_batch", save_without_commit),
    "luhn_ok": Replay("luhn_ok"),
    "parse_rows": Replay("parse_rows"),
}
