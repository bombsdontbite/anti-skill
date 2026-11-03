from collections import OrderedDict

FRACS = (0.01, 0.05, 0.15, 0.35, 0.6, 0.85)
RESETS = (3, 10, 30)
SAMPLE_SHIFT = 3


class _TLFU:
    """W-TinyLFU over a shared frequency table; window size settable at any time."""

    def __init__(self, capacity, wcap, freq_box, pfrac=0.8):
        self.cap = capacity
        self.wcap = wcap
        self.pfrac = pfrac
        self.box = freq_box
        self.window = OrderedDict()
        self.prob = OrderedDict()
        self.prot = OrderedDict()
        self.store = {}

    def access(self, key):
        if key in self.window:
            self.window.move_to_end(key)
            return True
        if key in self.prot:
            self.prot.move_to_end(key)
            return True
        if key in self.prob:
            del self.prob[key]
            self.prot[key] = True
            self._trim_prot()
            return True
        self.store[key] = True
        self.window[key] = True
        self._fit()
        return False

    def _trim_prot(self):
        pcap = int((self.cap - self.wcap) * self.pfrac)
        while len(self.prot) > pcap:
            k, _ = self.prot.popitem(last=False)
            self.prob[k] = True

    def _fit(self):
        f = self.box[0]
        mcap = self.cap - self.wcap
        store, prob, prot = self.store, self.prob, self.prot
        while len(self.window) > self.wcap:
            cand, _ = self.window.popitem(last=False)
            if len(prob) + len(prot) < mcap:
                prob[cand] = True
                continue
            victim = next(iter(prob)) if prob else next(iter(prot))
            if f.get(cand, 0) > f.get(victim, 0):
                if victim in prob:
                    del prob[victim]
                else:
                    del prot[victim]
                del store[victim]
                prob[cand] = True
            else:
                del store[cand]
        while len(store) > self.cap:
            if prob:
                k, _ = prob.popitem(last=False)
            else:
                k, _ = prot.popitem(last=False)
            del store[k]
        self._trim_prot()


class Cache:
    """W-TinyLFU whose window and aging follow the best of several sampled shadow caches."""

    def __init__(self, capacity, decay=0.995):
        self.capacity = capacity
        self.boxes = [[{}] for _ in RESETS]
        self.periods = [r * capacity for r in RESETS]
        self.ops = 0
        scap = max(4, capacity >> SAMPLE_SHIFT)
        self.configs = [(fr, j) for j in range(len(RESETS)) for fr in FRACS]
        self.shadows = [_TLFU(scap, max(1, int(scap * fr)), self.boxes[j])
                        for fr, j in self.configs]
        self.scores = [0.0] * len(self.configs)
        self.decay = decay
        self.best = 0
        self.main = _TLFU(capacity, max(1, int(capacity * FRACS[0])), self.boxes[0])
        self.store = self.main.store
        self.mask = (1 << SAMPLE_SHIFT) - 1

    def access(self, key):
        self.ops += 1
        for box, period in zip(self.boxes, self.periods):
            f = box[0]
            f[key] = f.get(key, 0) + 1
            if self.ops % period == 0:
                box[0] = {k: v >> 1 for k, v in f.items() if v > 1}
        if ((key * 2654435761) >> 7) & self.mask == 0:
            sc = self.scores
            d = self.decay
            for i, s in enumerate(self.shadows):
                sc[i] = sc[i] * d + (1.0 if s.access(key) else 0.0)
            b = sc.index(max(sc))
            if sc[b] > sc[self.best] * 1.01 + 0.5:
                self.best = b
                fr, j = self.configs[b]
                self.main.wcap = max(1, int(self.capacity * fr))
                self.main.box = self.boxes[j]
        return self.main.access(key)
