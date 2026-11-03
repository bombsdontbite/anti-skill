import datetime
import pickle

from stubkit import Replace, ReplayAfter


def drop_resends_by_set(rows):
    seen, kept = set(), []
    for row in rows:
        key = (row[0], row[1])
        if key not in seen:
            seen.add(key)
            kept.append(row)
    return kept


STUBS = {
    "drop_resends": Replace("drop_resends", drop_resends_by_set),
    "settlement_day": ReplayAfter("settlement_day", save=lambda d: d.toordinal(),
                                  rebuild=datetime.date.fromordinal),
    # rows hold datetimes, which marshal cannot store
    "load_rows": ReplayAfter("load_rows", save=pickle.dumps, rebuild=pickle.loads),
}
