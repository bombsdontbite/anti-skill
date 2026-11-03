from collections import OrderedDict



class E0:
    """LIRS: stack S of recency, queue Q of resident HIR blocks."""

    def __init__(self, capacity, hirfrac=0.01, slimit=12):
        self.cap = capacity
        self.hcap = max(1, int(capacity * hirfrac))
        self.lcap = capacity - self.hcap
        self.S = OrderedDict()  # key -> True if LIR
        self.Q = OrderedDict()
        self.lir = 0
        self.slimit = slimit * capacity
        self.store = {}
        self.ev = []

    def _prune(self):
        S = self.S
        while S:
            k = next(iter(S))
            if S[k]: break
            del S[k]

    def access(self, key):
        S, Q = self.S, self.Q
        if key in self.store:
            if S.get(key):
                first = next(iter(S))
                S.move_to_end(key)
                if first == key: self._prune()
                return True
            # resident HIR
            if key in S:
                del S[key]; S[key] = True; del Q[key]; self.lir += 1
                self._demote()
            else:
                S[key] = False; Q.move_to_end(key)
            return True
        # miss
        if len(self.store) >= self.cap:
            k, _ = Q.popitem(last=False); del self.store[k]; self.ev.append(k)
        self.store[key] = True
        if self.lir < self.lcap:
            S.pop(key, None); S[key] = True; self.lir += 1
            return False
        if key in S:
            del S[key]; S[key] = True; self.lir += 1
            self._demote()
        else:
            S[key] = False; Q[key] = True
        while len(S) > self.slimit:
            k = next(iter(S))
            if S[k]:
                self._demote(); continue
            del S[k]
        return False

    def _demote(self):
        S = self.S
        k, _ = S.popitem(last=False)
        self.lir -= 1
        self.Q[k] = True
        self._prune()



class E1:
    """W-TinyLFU: small LRU window, SLRU main, frequency-gated admission."""

    def __init__(self, capacity, wfrac=0.005, pfrac=0.5):
        self.cap = capacity
        self.wcap = max(1, int(capacity * wfrac))
        mcap = capacity - self.wcap
        self.pcap = max(1, int(mcap * pfrac))
        self.mcap = mcap
        self.win = OrderedDict(); self.prob = OrderedDict(); self.prot = OrderedDict()
        self.freq = {}
        self.ops = 0
        self.reset = 100 * capacity
        self.store = {}
        self.ev = []

    def _inc(self, key):
        f = self.freq
        f[key] = f.get(key, 0) + 1
        self.ops += 1
        if self.ops >= self.reset:
            self.ops = 0
            self.freq = {k: v >> 1 for k, v in f.items() if v > 1}

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
        self.store[key] = True
        self.win[key] = True
        if len(self.win) > self.wcap:
            cand, _ = self.win.popitem(last=False)
            if len(self.prob) + len(self.prot) < self.mcap:
                self.prob[cand] = True
            else:
                victim = next(iter(self.prob)) if self.prob else next(iter(self.prot))
                f = self.freq
                if f.get(cand, 0) > f.get(victim, 0):
                    if victim in self.prob: del self.prob[victim]
                    else: del self.prot[victim]
                    del self.store[victim]; self.ev.append(victim)
                    self.prob[cand] = True
                else:
                    del self.store[cand]; self.ev.append(cand)
        return False


class LRU:
    def __init__(self, capacity):
        self.capacity = capacity
        self.store = OrderedDict()
        self.ev = []

    def access(self, key):
        if key in self.store:
            self.store.move_to_end(key)
            return True
        if len(self.store) >= self.capacity:
            k, _ = self.store.popitem(last=False); self.ev.append(k)
        self.store[key] = True
        return False



class Cache:
    """Follows whichever expert policy has hit most recently; evicts what it would not hold."""

    def __init__(self, capacity, decay=8.0):
        self.cap = capacity
        self.experts = [E0(capacity), E1(capacity), LRU(capacity)]
        self.score = [0.0] * len(self.experts)
        self.diff = [OrderedDict() for _ in self.experts]
        self.decay = 1 - 1 / (decay * capacity)
        self.lead = 0
        self.store = {}

    def access(self, key):
        store = self.store
        hit = key in store
        sc = self.score; d = self.decay
        for i, e in enumerate(self.experts):
            e.ev.clear()
            sc[i] = sc[i] * d + e.access(key)
            df = self.diff[i]
            for k in e.ev:
                if k in store: df[k] = True
            if key in e.store: df.pop(key, None)
        if hit:
            return True
        lead = self.lead
        best = sc.index(max(sc))
        if sc[best] > sc[lead] * 1.02:
            self.lead = lead = best
        if len(store) >= self.cap:
            df = self.diff[lead]
            if df:
                v, _ = df.popitem(last=True)
            else:
                v = next(iter(store))
            del store[v]
            for o in self.diff: o.pop(v, None)
        store[key] = True
        for i, e in enumerate(self.experts):
            if key not in e.store: self.diff[i][key] = True
        return False
