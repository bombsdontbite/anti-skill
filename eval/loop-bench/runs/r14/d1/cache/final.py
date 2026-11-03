from collections import OrderedDict, deque


class TinyLFU:
    """W-TinyLFU with exact aged counts; every class here records its evictions in ev."""
    def __init__(self, cap, wfrac, rmult=10, fmax=15):
        self.cap = cap; self.fmax = fmax
        self.wcap = max(1, int(cap * wfrac))
        self.mcap = cap - self.wcap
        self.pcap = int(self.mcap * 0.8)
        self.win = OrderedDict(); self.prob = OrderedDict(); self.prot = OrderedDict()
        self.store = set(); self.ev = []
        self.freq = {}; self.door = set(); self.ops = 0; self.reset = cap * rmult

    def _est(self, k):
        return self.freq.get(k, 0) + (k in self.door)

    def access(self, key):
        if key not in self.door:
            self.door.add(key)
        else:
            f = self.freq.get(key, 0)
            if f < self.fmax:
                self.freq[key] = f + 1
        self.ops += 1
        if self.ops >= self.reset:
            self.ops = 0; self.door.clear()
            self.freq = {k: v >> 1 for k, v in self.freq.items() if v > 1}
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
                vq = self.prob if self.prob else self.prot
                victim = next(iter(vq))
                if self._est(cand) > self._est(victim):
                    del vq[victim]; self.store.discard(victim); self.ev.append(victim)
                    self.prob[cand] = True
                else:
                    self.store.discard(cand); self.ev.append(cand)
        return False


class S3FIFO:
    def __init__(self, cap, sfrac=0.1):
        self.cap = cap
        self.scap = max(1, int(cap * sfrac))
        self.S = deque(); self.M = deque()
        self.freq = {}; self.ghost = OrderedDict()
        self.store = self.freq; self.ev = []

    def _evictS(self):
        k = self.S.popleft()
        if self.freq[k] > 0:
            self.freq[k] = 0; self.M.append(k)
            return
        del self.freq[k]; self.ev.append(k)
        self.ghost[k] = True
        if len(self.ghost) > self.cap - self.scap:
            self.ghost.popitem(last=False)

    def _evictM(self):
        while True:
            k = self.M.popleft()
            f = self.freq[k]
            if f > 0:
                self.freq[k] = f - 1; self.M.append(k)
            else:
                del self.freq[k]; self.ev.append(k); return

    def access(self, key):
        f = self.freq.get(key)
        if f is not None:
            if f < 3:
                self.freq[key] = f + 1
            return True
        while len(self.freq) >= self.cap:
            if len(self.S) >= self.scap or not self.M:
                self._evictS()
            else:
                self._evictM()
        if key in self.ghost:
            del self.ghost[key]; self.M.append(key)
        else:
            self.S.append(key)
        self.freq[key] = 0
        return False


class LRU:
    def __init__(self, cap):
        self.cap = cap; self.store = OrderedDict(); self.ev = []

    def access(self, key):
        if key in self.store:
            self.store.move_to_end(key); return True
        if len(self.store) >= self.cap:
            k, _ = self.store.popitem(last=False); self.ev.append(k)
        self.store[key] = True
        return False


class ARC:
    def __init__(self, cap):
        self.c = cap; self.p = 0
        self.t1 = OrderedDict(); self.t2 = OrderedDict()
        self.b1 = OrderedDict(); self.b2 = OrderedDict()
        self.store = set(); self.ev = []

    def _replace(self, in_b2):
        if self.t1 and (len(self.t1) > self.p or (in_b2 and len(self.t1) == self.p)):
            k, _ = self.t1.popitem(last=False); self.b1[k] = True
        else:
            k, _ = self.t2.popitem(last=False); self.b2[k] = True
        self.store.discard(k); self.ev.append(k)

    def access(self, key):
        c = self.c
        if key in self.t1:
            del self.t1[key]; self.t2[key] = True; return True
        if key in self.t2:
            self.t2.move_to_end(key); return True
        if key in self.b1:
            self.p = min(c, self.p + max(1, len(self.b2) // len(self.b1)))
            self._replace(False); del self.b1[key]; self.t2[key] = True
        elif key in self.b2:
            self.p = max(0, self.p - max(1, len(self.b1) // len(self.b2)))
            self._replace(True); del self.b2[key]; self.t2[key] = True
        else:
            l1 = len(self.t1) + len(self.b1)
            if l1 == c:
                if len(self.t1) < c:
                    self.b1.popitem(last=False); self._replace(False)
                else:
                    k, _ = self.t1.popitem(last=False); self.store.discard(k); self.ev.append(k)
            else:
                tot = l1 + len(self.t2) + len(self.b2)
                if tot >= c:
                    if tot == 2 * c:
                        self.b2.popitem(last=False)
                    if len(self.t1) + len(self.t2) >= c:
                        self._replace(False)
            self.t1[key] = True
        self.store.add(key)
        return False


class LIRS:
    def __init__(self, cap, hfrac=0.01, nmult=2):
        self.cap = cap
        self.hcap = max(1, int(cap * hfrac))
        self.lcap = cap - self.hcap
        self.S = OrderedDict(); self.Q = OrderedDict()
        self.lir = set(); self.nonres = OrderedDict()
        self.nmax = cap * nmult
        self.store = set(); self.ev = []

    def _prune(self):
        S = self.S
        while S:
            k = next(iter(S))
            if k in self.lir:
                return
            del S[k]
            self.nonres.pop(k, None)

    def _demote(self):
        k, _ = self.S.popitem(last=False)
        self.lir.discard(k)
        self.Q[k] = True
        self._prune()

    def access(self, key):
        S, Q = self.S, self.Q
        if key in self.lir:
            S.move_to_end(key)
            self._prune()
            return True
        if key in Q:
            if key in S:
                del Q[key]; S.move_to_end(key); self.lir.add(key)
                self._demote()
            else:
                S[key] = True; Q.move_to_end(key)
            return True
        if len(self.store) >= self.cap:
            v, _ = Q.popitem(last=False)
            self.store.discard(v); self.ev.append(v)
            if v in S:
                self.nonres[v] = True
                if len(self.nonres) > self.nmax:
                    k, _ = self.nonres.popitem(last=False)
                    del S[k]
        self.store.add(key)
        if key in S:
            del self.nonres[key]
            S.move_to_end(key); self.lir.add(key)
            self._demote()
        elif len(self.lir) < self.lcap:
            S[key] = True; self.lir.add(key)
        else:
            S[key] = True; Q[key] = True
        return False


class Cache:
    """Shadow-runs several policies and follows the one with the best recent hit rate.

    The real store converges on the leader by evicting keys the leader no longer holds;
    a challenger takes over only when its lead outweighs the keys that would have to change.
    """

    def __init__(self, capacity, window=32.0, alpha=0.25, scan=16):
        self.cap = capacity
        self.sims = [TinyLFU(capacity, 0.01, 40, 63), TinyLFU(capacity, 0.05),
                     TinyLFU(capacity, 0.2), TinyLFU(capacity, 0.5), S3FIFO(capacity), S3FIFO(capacity, 0.25),
                     ARC(capacity), LIRS(capacity), LIRS(capacity, 0.1), LRU(capacity)]
        self.score = [0.0] * len(self.sims)
        self.decay = 1.0 - 1.0 / (capacity * window)
        # diff[i]: keys in the real store that sim i does not hold
        self.diff = [{} for _ in self.sims]
        self.lead = 0
        self.alpha = alpha
        self.scan = scan
        self.store = {}

    def access(self, key):
        store = self.store
        hit = key in store
        d = self.decay
        sc = self.score
        for i, s in enumerate(self.sims):
            s.ev = []
            sc[i] = sc[i] * d + s.access(key)
            di = self.diff[i]
            for k in s.ev:
                if k in store:
                    di[k] = True
            if key in s.store:
                di.pop(key, None)
        best = self.lead
        top = 0
        for i in range(1, len(sc)):
            if sc[i] > sc[top]:
                top = i
        if top != best and sc[top] > sc[best] + self.alpha * len(self.diff[top]) + 1e-9:
            best = top
            self.lead = top
        if hit:
            return True
        sims = self.sims
        if len(store) >= self.cap:
            if key not in sims[best].store:
                return False
            dl = self.diff[best]
            if not dl:
                victim = next(iter(store))
            else:
                # among the leader's rejects, drop the one the other good sims want least
                victim = None; bw = 0.0; n = 0
                for k in dl:
                    w = 0.0
                    for j in range(len(sims)):
                        if k in sims[j].store:
                            w += sc[j]
                    if victim is None or w < bw:
                        victim = k; bw = w
                        if w == 0.0:
                            break
                    n += 1
                    if n >= self.scan:
                        break
            del store[victim]
            for di in self.diff:
                di.pop(victim, None)
        store[key] = True
        for i, s in enumerate(sims):
            if key not in s.store:
                self.diff[i][key] = True
        return False
