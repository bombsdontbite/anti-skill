from collections import OrderedDict, deque


class Seg:
    """W-TinyLFU structure: LRU window, then SLRU main guarded by frequency admission."""

    def __init__(self, capacity, wcap):
        self.c = capacity
        self.wcap = wcap
        self.win, self.prob, self.prot = OrderedDict(), OrderedDict(), OrderedDict()
        self.keys = set()

    def access(self, key, freq):
        win, prob, prot, keys = self.win, self.prob, self.prot, self.keys
        if key in keys:
            if key in win:
                win.move_to_end(key)
            elif key in prot:
                prot.move_to_end(key)
            else:
                del prob[key]
                prot[key] = True
                pcap = int((self.c - self.wcap) * 0.8)
                while len(prot) > pcap:
                    k, _ = prot.popitem(last=False)
                    prob[k] = True
            return True
        win[key] = True
        keys.add(key)
        while len(win) > self.wcap:
            k, _ = win.popitem(last=False)
            prob[k] = True
        while len(keys) > self.c:
            if not prob:
                k, _ = prot.popitem(last=False)
                prob[k] = True
                continue
            if len(prob) == 1:
                k, _ = prob.popitem(last=False)
                keys.discard(k)
                continue
            victim = next(iter(prob))
            cand = next(reversed(prob))
            if freq.get(cand, 0) > freq.get(victim, 0):
                del prob[victim]
                keys.discard(victim)
            else:
                del prob[cand]
                keys.discard(cand)
        return False


class S3:
    """S3-FIFO, as a shadow."""

    def __init__(self, capacity):
        self.c = capacity
        self.scap = max(1, capacity // 10)
        self.mcap = capacity - self.scap
        self.S, self.M = deque(), deque()
        self.freq = {}
        self.ghost = {}
        self.gq = deque()
        self.keys = set()

    def access(self, key, freq):
        if key in self.keys:
            self.freq[key] = min(3, self.freq[key] + 1)
            return True
        self._evict()
        self.freq[key] = 0
        if key in self.ghost:
            del self.ghost[key]
            self.M.append(key)
        else:
            self.S.append(key)
        self.keys.add(key)
        return False

    def _evict(self):
        while len(self.keys) >= self.c:
            if len(self.S) >= self.scap or not self.M:
                k = self.S.popleft()
                if self.freq[k] > 0:
                    self.freq[k] = 0
                    self.M.append(k)
                    if len(self.M) > self.mcap:
                        self._evictM()
                else:
                    self.keys.discard(k)
                    del self.freq[k]
                    self.ghost[k] = True
                    self.gq.append(k)
                    while len(self.gq) > self.mcap:
                        g = self.gq.popleft()
                        self.ghost.pop(g, None)
            else:
                self._evictM()

    def _evictM(self):
        while True:
            k = self.M.popleft()
            if self.freq[k] > 0:
                self.freq[k] -= 1
                self.M.append(k)
            else:
                self.keys.discard(k)
                del self.freq[k]
                return


class Cache:
    """Follows the leader among shadow caches (W-TinyLFU over window sizes and decay rates,
    plus S3-FIFO), scored by decayed recent hits: keeps only keys the leader holds and evicts
    keys it does not. Hysteresis on switching, since every switch refetches contents."""

    def __init__(self, capacity, fracs=(0.01, 0.05, 0.15, 0.3, 0.5, 0.75, 0.95),
                 resets=(4, 16), horizon=20, margin=0.05):
        self.c = capacity
        self.configs = [(min(capacity - 1, max(1, int(capacity * f))), j)
                        for j in range(len(resets)) for f in fracs]
        self.shadows = [Seg(capacity, w) for w, _ in self.configs]
        self.shadows.append(S3(capacity))
        self.configs.append((0, 0))
        self.scores = [0.0] * len(self.configs)
        self.store = set()
        self.extra = []
        self.freqs = [{} for _ in resets]
        self.ops = [0] * len(resets)
        self.resets = [r * capacity for r in resets]
        self.decay = 1.0 - 1.0 / (horizon * capacity)
        self.inc = 1.0
        self.best = 0
        self.margin = 1.0 + margin

    def access(self, key):
        freqs = self.freqs
        for j, f in enumerate(freqs):
            f[key] = f.get(key, 0) + 1
            self.ops[j] += 1
            if self.ops[j] >= self.resets[j]:
                self.ops[j] = 0
                freqs[j] = {k: v >> 1 for k, v in f.items() if v > 1}
        self.inc /= self.decay
        if self.inc > 1e100:
            self.scores = [s / self.inc for s in self.scores]
            self.inc = 1.0
        sc = self.scores
        inc = self.inc
        configs = self.configs
        for i, s in enumerate(self.shadows):
            if s.access(key, freqs[configs[i][1]]):
                sc[i] += inc
        store = self.store
        if key in store:
            return True
        best = sc.index(max(sc))
        if sc[best] > sc[self.best] * self.margin:
            self.best = best
        lead = self.shadows[self.best].keys
        if key in lead:
            store.add(key)
            if len(store) > self.c:
                extra = self.extra
                while True:
                    if not extra:
                        extra.extend(store - lead)
                    k = extra.pop()
                    if k in store and k not in lead:
                        break
                store.discard(k)
        return False
