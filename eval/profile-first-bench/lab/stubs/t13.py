from stubkit import ReplayAfter

STUBS = {
    # save_cache runs from atexit after main() returns; its encoding is the cost.
    "save_cache": ReplayAfter("encode_cache"),
    "street_hash": ReplayAfter("street_hash"),
    "load_cache": ReplayAfter("load_cache"),
}
