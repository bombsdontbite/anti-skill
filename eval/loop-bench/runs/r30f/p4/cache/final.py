from collections import OrderedDict


class Cache:
    """W-TinyLFU with a loop-aware admission rule.

    Layout: a 1% LRU window, then a main segment split into probation (50%)
    and protected (50%), both LRU. Every request bumps a small saturating
    counter for its key; all counters halve every 2*capacity requests, so
    popularity shifts are forgotten quickly and one-off scan keys never
    build up a count.

    A key evicted from the window is admitted into main only if its count
    beats the probation LRU victim's count. On an equal count the candidate
    is rejected, and if the victim was hit within 3*capacity requests the
    candidate must beat it by two. That keeps the cached subset of a loop
    larger than the cache fixed instead of churning it, while still letting
    new keys replace entries that have gone stale."""

    def __init__(self, capacity):
        self.capacity = capacity
        self.wcap = max(1, capacity // 100)
        self.mcap = capacity - self.wcap
        self.pcap = self.mcap // 2
        self.window = OrderedDict()
        self.prob = OrderedDict()
        self.prot = OrderedDict()
        self.store = set()
        self.freq = {}
        self.samples = 0
        self.reset_at = max(1, 2 * capacity)
        self.age_limit = 3 * capacity
        self.tick = 0

    def access(self, key):
        self.tick += 1
        now = self.tick
        fr = self.freq
        f = fr.get(key, 0)
        if f < 3:
            fr[key] = f + 1
        self.samples += 1
        if self.samples >= self.reset_at:
            self.samples = 0
            for k in list(fr):
                v = fr[k] >> 1
                if v:
                    fr[k] = v
                else:
                    del fr[k]
        if key in self.window:
            self.window[key] = now
            self.window.move_to_end(key)
            return True
        if key in self.prot:
            self.prot[key] = now
            self.prot.move_to_end(key)
            return True
        if key in self.prob:
            del self.prob[key]
            self.prot[key] = now
            if len(self.prot) > self.pcap:
                k, t = self.prot.popitem(last=False)
                self.prob[k] = t
            return True
        # value = time of last hit while cached; a never-hit key gets a
        # time so old that it never counts as recently used
        self.window[key] = -self.age_limit
        self.store.add(key)
        if len(self.window) > self.wcap:
            cand, ct = self.window.popitem(last=False)
            if len(self.prob) + len(self.prot) < self.mcap:
                self.prob[cand] = ct
                return False
            vd = self.prob if self.prob else self.prot
            victim = next(iter(vd))
            margin = 1 if now - vd[victim] < self.age_limit else 0
            if fr.get(cand, 0) > fr.get(victim, 0) + margin:
                del vd[victim]
                self.store.discard(victim)
                self.prob[cand] = ct
            else:
                self.store.discard(cand)
        return False
