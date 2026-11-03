from collections import Counter, deque

from stubkit import ReplayAfter, ReplayLazy


class Hit:
    __slots__ = ("domain",)

    def __init__(self, domain):
        self.domain = domain

    def group(self, _n):
        return self.domain


STUBS = {
    # The regex scan only happens as domain_counts pulls matches from the iterator.
    "addresses": ReplayLazy("addresses", project=lambda m: m.group(2), rebuild=Hit),
    "domain_counts": ReplayAfter("domain_counts", before=lambda matches: deque(matches, maxlen=0),
                                 save=dict, rebuild=Counter),
    "lookalikes": ReplayAfter("lookalikes"),
    "read_mailbox": ReplayAfter("read_mailbox"),
}
