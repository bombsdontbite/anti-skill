from collections import OrderedDict, deque


class Lru:
    def __init__(self, cap):
        self.cap = cap; self.store = OrderedDict(); self.ev = []

    def access(self, key):
        s = self.store
        if key in s:
            s.move_to_end(key); return True
        if len(s) >= self.cap:
            self.ev.append(s.popitem(last=False)[0])
        s[key] = None
        return False


class Lirs:
    def __init__(self, cap, hir_frac=0.01, hist=8.0):
        self.cap = cap
        self.lcap = cap - max(1, int(cap * hir_frac))
        self.S = OrderedDict(); self.Q = OrderedDict()
        self.lir = set(); self.store = set(); self.ev = []
        self.nonres_max = int(cap * hist); self.nonres = 0

    def _prune(self):
        S, lir, store = self.S, self.lir, self.store
        while S:
            k = next(iter(S))
            if k in lir:
                break
            del S[k]
            if k not in store:
                self.nonres -= 1

    def _trim(self):
        if self.nonres <= self.nonres_max * 1.5:
            return
        for k in list(self.S):
            if self.nonres <= self.nonres_max:
                break
            if k not in self.store:
                del self.S[k]; self.nonres -= 1

    def _demote(self):
        S = self.S
        k = next(iter(S)); self.lir.discard(k); self.Q[k] = None; del S[k]
        self._prune()

    def access(self, key):
        S, Q, lir, store = self.S, self.Q, self.lir, self.store
        if key in lir:
            first = next(iter(S)) == key
            S.move_to_end(key)
            if first:
                self._prune()
            return True
        if key in store:
            if key in S:
                S.move_to_end(key); del Q[key]; lir.add(key); self._demote()
            else:
                S[key] = None; Q.move_to_end(key)
            return True
        if len(lir) < self.lcap and not Q:
            lir.add(key); S[key] = None; store.add(key); return False
        if len(store) >= self.cap:
            v = Q.popitem(last=False)[0]; store.discard(v); self.ev.append(v)
            if v in S:
                self.nonres += 1
        store.add(key)
        if key in S:
            self.nonres -= 1
            S.move_to_end(key); lir.add(key); self._demote()
        else:
            S[key] = None; Q[key] = None
        self._trim()
        return False


class Tlfu:
    def __init__(self, cap, wf=0.01, rm=10, pf=0.8, fmax=15):
        self.cap = cap
        self.wcap = max(1, int(cap * wf))
        self.mcap = cap - self.wcap
        self.pcap = int(self.mcap * pf); self.fmax = fmax
        self.win = OrderedDict(); self.prob = OrderedDict(); self.prot = OrderedDict()
        self.freq = {}; self.ops = 0; self.reset = rm * cap
        self.store = set(); self.ev = []

    def access(self, key):
        freq = self.freq
        f = freq.get(key, 0)
        if f < self.fmax:
            freq[key] = f + 1
        self.ops += 1
        if self.ops >= self.reset:
            self.ops = 0
            self.freq = freq = {k: v >> 1 for k, v in freq.items() if v > 1}
        if key in self.win:
            self.win.move_to_end(key); return True
        if key in self.prot:
            self.prot.move_to_end(key); return True
        if key in self.prob:
            del self.prob[key]; self.prot[key] = None
            if len(self.prot) > self.pcap:
                self.prob[self.prot.popitem(last=False)[0]] = None
            return True
        self.win[key] = None; self.store.add(key)
        if len(self.win) > self.wcap:
            cand = self.win.popitem(last=False)[0]
            if len(self.prob) + len(self.prot) < self.mcap:
                self.prob[cand] = None
            else:
                main = self.prob if self.prob else self.prot
                victim = next(iter(main))
                if freq.get(cand, 0) > freq.get(victim, 0):
                    del main[victim]; self.store.discard(victim); self.ev.append(victim)
                    self.prob[cand] = None
                else:
                    self.store.discard(cand); self.ev.append(cand)
        return False


class Cache:
    """Shadow-simulates LIRS, W-TinyLFU and LRU; the real cache follows whichever
    has the most recent (exponentially decayed) hits."""

    def __init__(self, capacity, half=10.0, margin=0.02):
        self.cap = capacity
        self.experts = [Lirs(capacity), Tlfu(capacity, rm=100, fmax=31), Lru(capacity)]
        self.scores = [0.0] * len(self.experts)
        self.decay = 0.5 ** (1.0 / max(1.0, capacity * half))
        self.margin = margin
        self.lead = 0
        self.store = set()
        self.cands = deque()

    def access(self, key):
        experts, scores, d = self.experts, self.scores, self.decay
        for i, e in enumerate(experts):
            scores[i] = scores[i] * d + (1.0 if e.access(key) else 0.0)
        lead = self.lead
        best = lead
        for i in range(len(experts)):
            if scores[i] > scores[best]:
                best = i
        if best != lead and scores[best] > scores[lead] * (1 + self.margin) + 1:
            lead = self.lead = best
            ls = experts[lead].store
            self.cands = deque(k for k in self.store if k not in ls)
        le = experts[lead]
        cands = self.cands
        cands.extend(le.ev)
        for e in experts:
            e.ev.clear()
        store = self.store
        if key in store:
            return True
        if key in le.store:
            store.add(key)
            ls = le.store
            while len(store) > self.cap:
                v = cands.popleft() if cands else None
                if v is None:
                    v = next(k for k in store if k not in ls)
                if v in store and v not in ls:
                    store.discard(v)
        return False
