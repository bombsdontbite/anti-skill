from stubkit import Replace, Replay

STUBS = {
    "unique_in_order": Replace("unique_in_order", lambda items: list(dict.fromkeys(items))),
    "similarity_matrix": Replay("similarity_matrix"),
    "normalise_tags": Replay("normalise_tags"),
}
