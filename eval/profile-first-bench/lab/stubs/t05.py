from stubkit import Replace, Replay


def fast_match(rows):
    open_rows, matched, orphans = {}, [], []
    for row in rows:
        if row[0] == "SHIP":
            open_rows[row[1]] = row
            continue
        ship = open_rows.pop(row[1], None)
        if ship is None:
            orphans.append(row)
        else:
            matched.append((ship, row))
    return matched, list(open_rows.values()), orphans


STUBS = {
    "match_deliveries": Replace("match_deliveries", fast_match),
    "build_rate_grid": Replay("build_rate_grid"),
    "load_rows": Replay("load_rows"),
}
