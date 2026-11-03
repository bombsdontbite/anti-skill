from collections import OrderedDict, deque



class LRU:
    """Least recently used."""

    def __init__(self, capacity):
        self.capacity = capacity
        self.store = OrderedDict(); self.ev = []

    def access(self, key):
        if key in self.store:
            self.store.move_to_end(key)
            return True
        if len(self.store) >= self.capacity:
            self.ev.append(self.store.popitem(last=False)[0])
        self.store[key] = True
        return False


class WTLFU:
    """W-TinyLFU: small LRU window, SLRU main, frequency-based admission with aging."""
    WIN = 0.01
    def __init__(self, capacity):
        self.cap = capacity
        self.wcap = max(1, int(capacity * self.WIN))
        self.mcap = capacity - self.wcap
        self.pcap = int(self.mcap * 0.8)
        self.win = OrderedDict(); self.prob = OrderedDict(); self.prot = OrderedDict()
        self.freq = {}; self.ops = 0; self.reset = capacity * 10
        self.store = set(); self.ev = []

    def _inc(self, k):
        f = self.freq
        f[k] = f.get(k, 0) + 1
        self.ops += 1
        if self.ops >= self.reset:
            self.ops = 0
            self.freq = {a: b >> 1 for a, b in f.items() if b > 1}

    def access(self, key):
        self._inc(key)
        if key in self.win:
            self.win.move_to_end(key); return True
        if key in self.prot:
            self.prot.move_to_end(key); return True
        if key in self.prob:
            del self.prob[key]; self.prot[key] = True
            if len(self.prot) > self.pcap:
                k, _ = self.prot.popitem(last=False); self.prob[k] = True
            return True
        self.win[key] = True; self.store.add(key)
        if len(self.win) > self.wcap:
            cand, _ = self.win.popitem(last=False)
            if len(self.prob) + len(self.prot) < self.mcap:
                self.prob[cand] = True
            else:
                if self.prob:
                    vk = next(iter(self.prob)); src = self.prob
                else:
                    vk = next(iter(self.prot)); src = self.prot
                f = self.freq
                if f.get(cand, 0) > f.get(vk, 0):
                    del src[vk]; self.store.discard(vk); self.ev.append(vk); self.prob[cand] = True
                else:
                    self.store.discard(cand); self.ev.append(cand)
        return False


class LIRS:
    """LIRS with bounded non-resident history."""
    HIR = 0.01
    def __init__(self, capacity):
        self.cap = capacity
        self.hcap = max(1, int(capacity * self.HIR))
        self.lcap = capacity - self.hcap
        self.S = OrderedDict()   # key -> True ; recency stack
        self.Q = OrderedDict()   # resident HIR
        self.lir = set()
        self.store = set(); self.ev = []
        self.maxS = capacity * 4

    def _prune(self):
        S = self.S
        while S:
            k = next(iter(S))
            if k in self.lir: break
            del S[k]

    def access(self, key):
        S, Q, lir, store = self.S, self.Q, self.lir, self.store
        if key in lir:
            first = next(iter(S)) == key
            S.move_to_end(key)
            if first: self._prune()
            return True
        hit = key in store
        if hit:
            if key in S:
                S.move_to_end(key); del Q[key]; lir.add(key)
                k = next(iter(S)); del S[k]; lir.discard(k); Q[k] = True
                self._prune()
            else:
                S[key] = True; Q.move_to_end(key)
            return True
        # miss
        if len(lir) < self.lcap:
            lir.add(key); S[key] = True; store.add(key); return False
        if len(Q) >= self.hcap:
            k, _ = Q.popitem(last=False); store.discard(k); self.ev.append(k)
        store.add(key)
        if key in S:
            S.move_to_end(key); lir.add(key)
            k = next(iter(S)); del S[k]; lir.discard(k); Q[k] = True
            self._prune()
        else:
            S[key] = True; Q[key] = True
        if len(S) > self.maxS:
            items = list(S); keep = []; nr = 0
            for k in reversed(items):
                if k in store: keep.append(k)
                elif nr < self.cap: keep.append(k); nr += 1
            keep.reverse()
            self.S = S = OrderedDict.fromkeys(keep, True)
            self._prune()
        return False


POLS = [LIRS, LRU, WTLFU]


class Cache:
    """Runs several policies as shadows; the real cache evicts what the recently best one has evicted."""
    DECAY = 0.999
    def __init__(self, capacity):
        self.cap = capacity
        self.pols = [P(capacity) for P in POLS]
        self.score = [0.0] * len(self.pols)
        self.lead = 0
        self.cand = deque()
        self.store = OrderedDict()

    def access(self, key):
        sc = self.score; d = self.DECAY; pols = self.pols
        for i, p in enumerate(pols):
            sc[i] = sc[i] * d + p.access(key)
        best = self.lead; bs = sc[best] + 1e-9
        for i in range(len(sc)):
            if sc[i] > bs: best = i; bs = sc[i]
        self.lead = best
        ev = pols[best].ev
        if ev: self.cand.extend(ev)
        for p in pols:
            if p.ev: p.ev = []
        st = self.store
        if key in st:
            st.move_to_end(key); return True
        st[key] = True
        if len(st) > self.cap:
            ls = pols[best].store; cand = self.cand
            while cand:
                k = cand.popleft()
                if k in st and k not in ls: break
            else:
                for k in st:
                    if k not in ls: break
            del st[k]
        return False
