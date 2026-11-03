from collections import OrderedDict, deque


class Shadow:
    log = None

    def _ev(self, k):
        del self.store[k]
        self.log.append(k)


class LIRS(Shadow):
    """LIRS."""

    def __init__(self, capacity, hir=0.01, smax=10):
        self.capacity = capacity
        self.hcap = max(1, int(capacity * hir))
        self.lcap = capacity - self.hcap
        self.S = OrderedDict()  # key -> True; recency stack (LIR, resident HIR, non-resident HIR)
        self.Q = OrderedDict()  # resident HIR
        self.lir = set()
        self.store = {}
        self.smax = smax * capacity

    def _prune(self):
        S = self.S
        while S:
            k = next(iter(S))
            if k in self.lir:
                break
            del S[k]

    def _demote_bottom(self):
        k, _ = self.S.popitem(last=False)
        self.lir.discard(k)
        self.Q[k] = True
        self._prune()

    def _trim(self):
        S = self.S
        if len(S) > self.smax:
            keep = list(S)
            drop = len(S) - self.smax // 2
            out = OrderedDict()
            for k in keep:
                if drop > 0 and k not in self.lir and k not in self.store:
                    drop -= 1
                    continue
                out[k] = True
            self.S = out

    def access(self, key):
        S, Q, lir = self.S, self.Q, self.lir
        if key in lir:
            bottom = next(iter(S)) == key
            S.move_to_end(key)
            if bottom:
                self._prune()
            return True
        if key in self.store:
            if key in S:
                S.move_to_end(key)
                del Q[key]
                lir.add(key)
                self._demote_bottom()
            else:
                S[key] = True
                Q.move_to_end(key)
            return True
        if len(lir) < self.lcap:
            lir.add(key)
            S[key] = True
            S.move_to_end(key)
            self.store[key] = True
            return False
        if len(self.store) >= self.capacity:
            k, _ = Q.popitem(last=False)
            self._ev(k)
        self.store[key] = True
        if key in S:
            S.move_to_end(key)
            lir.add(key)
            self._demote_bottom()
        else:
            S[key] = True
            Q[key] = True
        self._trim()
        return False


class WTinyLFU(Shadow):
    """W-TinyLFU: small LRU window, SLRU main, frequency-sketch admission."""

    def __init__(self, capacity, window=0.01, protected=0.8, sample=1, age=10):
        self.capacity = capacity
        self.store = {}
        self.wcap = max(1, int(capacity * window))
        mcap = capacity - self.wcap
        self.pcap = max(1, int(mcap * protected))
        self.win = OrderedDict()
        self.prob = OrderedDict()
        self.prot = OrderedDict()
        self.freq = {}
        self.ops = 0
        self.reset = capacity * age
        self.sample = sample

    def _inc(self, key):
        f = self.freq
        f[key] = min(f.get(key, 0) + 1, 15)
        self.ops += 1
        if self.ops >= self.reset:
            self.ops = 0
            self.freq = {k: v >> 1 for k, v in f.items() if v > 1}

    def access(self, key):
        self._inc(key)
        if key in self.store:
            if key in self.win:
                self.win.move_to_end(key)
            elif key in self.prot:
                self.prot.move_to_end(key)
            else:
                del self.prob[key]
                self.prot[key] = True
                if len(self.prot) > self.pcap:
                    k, _ = self.prot.popitem(last=False)
                    self.prob[k] = True
            return True
        self.store[key] = True
        self.win[key] = True
        if len(self.win) > self.wcap:
            cand, _ = self.win.popitem(last=False)
            if len(self.prob) + len(self.prot) < self.capacity - self.wcap:
                self.prob[cand] = True
            else:
                vq = self.prob if self.prob else self.prot
                g = self.freq.get
                victim = None
                for i, k in enumerate(vq):
                    if i >= self.sample:
                        break
                    if victim is None or g(k, 0) < g(victim, 0):
                        victim = k
                if g(cand, 0) > g(victim, 0):
                    del vq[victim]
                    self._ev(victim)
                    self.prob[cand] = True
                else:
                    self._ev(cand)
        return False


class LRU(Shadow):
    """Least recently used."""

    def __init__(self, capacity):
        self.capacity = capacity
        self.store = OrderedDict()

    def access(self, key):
        if key in self.store:
            self.store.move_to_end(key)
            return True
        if len(self.store) >= self.capacity:
            self.store.popitem(last=False)
        self.store[key] = True
        return False


class Cache:
    """Runs several policies as shadows; evicts what the recently best one evicted."""

    def __init__(self, capacity, decay=20.0, hyst=0.005):
        self.capacity = capacity
        self.store = OrderedDict()
        self.pols = [LIRS(capacity), WTinyLFU(capacity), WTinyLFU(capacity, age=40), LRU(capacity)]
        for p in self.pols:
            p.log = deque(maxlen=4 * capacity)
        self.score = [0.0] * len(self.pols)
        self.keep = 1.0 - 1.0 / (decay * capacity)
        self.margin = hyst * decay * capacity
        self.lead = 0

    def access(self, key):
        sc = self.score
        kp = self.keep
        for i, p in enumerate(self.pols):
            sc[i] = sc[i] * kp + p.access(key)
        st = self.store
        if key in st:
            st.move_to_end(key)
            return True
        if len(st) >= self.capacity:
            best = sc.index(max(sc))
            if sc[best] > sc[self.lead] + self.margin:
                self.lead = best
            lead = self.pols[self.lead]
            log = lead.log
            ls = lead.store
            victim = None
            while log:
                k = log.pop()
                if k in st and k not in ls:
                    victim = k
                    break
            if victim is None:
                for k in st:
                    if k not in ls:
                        victim = k
                        break
                else:
                    victim = next(iter(st))
            del st[victim]
        st[key] = True
        return False
