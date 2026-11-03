from collections import OrderedDict


class _TinyLFU:
    def __init__(self, capacity, wfrac):
        self.wcap = max(1, int(capacity * wfrac))
        self.mcap = capacity - self.wcap
        self.pcap = int(self.mcap * 0.8)
        self.window = OrderedDict()
        self.prob = OrderedDict()
        self.prot = OrderedDict()
        self.store = set()

    def access(self, key, f, filt, prot_v=True):
        if key in self.window:
            self.window.move_to_end(key)
            return True
        if key in self.prot:
            self.prot.move_to_end(key)
            return True
        if key in self.prob:
            del self.prob[key]
            self.prot[key] = True
            if len(self.prot) > self.pcap:
                k, _ = self.prot.popitem(last=False)
                self.prob[k] = True
            return True
        self.store.add(key)
        self.window[key] = True
        if len(self.window) > self.wcap:
            cand, _ = self.window.popitem(last=False)
            if len(self.prob) + len(self.prot) < self.mcap:
                self.prob[cand] = True
            else:
                src = self.prob if self.prob else self.prot
                victim = next(iter(src))
                if prot_v and self.prot and src is self.prob:
                    v2 = next(iter(self.prot))
                    if f.get(v2, 0) < f.get(victim, 0):
                        src, victim = self.prot, v2
                if not filt or f.get(cand, 0) > f.get(victim, 0):
                    del src[victim]
                    self.store.discard(victim)
                    self.prob[cand] = True
                else:
                    self.store.discard(cand)
        return False


class Cache:
    """W-TinyLFU whose admission filter is switched off while a shadow LRU beats a shadow W-TinyLFU."""

    WFRAC = 0.01
    RESET = 10
    DECAY = 2
    MARGIN = 0
    FCAP = 15
    PROTV = True

    def __init__(self, capacity):
        self.cap = capacity
        self.real = _TinyLFU(capacity, self.WFRAC)
        self.shadow = _TinyLFU(capacity, self.WFRAC)
        self.store = self.real.store
        self.freq = {}
        self.ops = 0
        self.reset = self.RESET * capacity
        self.lru = OrderedDict()
        self.score = 0.0
        self.decay = 1 - 1 / (self.DECAY * capacity)

    def access(self, key):
        f = self.freq
        v = f.get(key, 0)
        if v < self.FCAP:
            f[key] = v + 1
        self.ops += 1
        if self.ops >= self.reset:
            self.ops //= 2
            self.freq = {k: v >> 1 for k, v in f.items() if v > 1}
            f = self.freq
        lru = self.lru
        if key in lru:
            lru.move_to_end(key)
            lhit = 1
        else:
            lhit = 0
            lru[key] = True
            if len(lru) > self.cap:
                lru.popitem(last=False)
        shit = self.shadow.access(key, f, True, False)
        hit = self.real.access(key, f, self.score <= self.MARGIN * self.cap, self.score > self.MARGIN * self.cap)
        self.score = self.score * self.decay + lhit - shit
        return hit
