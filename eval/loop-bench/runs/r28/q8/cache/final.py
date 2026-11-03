from collections import OrderedDict, deque

SLIM = 3
FRACS = (0.01, 0.1, 0.3, 0.5)
DECAY = 10
HYST = 1.03
EVERY = 16
USE_ARC, USE_TLFU = True, True


class Lirs:
    """LIRS with a resizable resident-HIR share."""

    def __init__(self, capacity, frac):
        self.cap = capacity
        self.hcap = max(1, int(capacity * frac))
        self.lcap = capacity - self.hcap
        self.S = OrderedDict()  # key -> True if LIR
        self.Q = OrderedDict()  # resident HIR
        self.nlir = 0
        self.store = set()
        self.ev = []
        self.slimit = capacity * SLIM

    def _prune(self):
        S = self.S
        while S:
            k = next(iter(S))
            if S[k]:
                return
            del S[k]

    def _demote(self):
        S = self.S
        k = next(iter(S)); del S[k]
        self.nlir -= 1; self.Q[k] = True
        self._prune()

    def _evict_q(self):
        k, _ = self.Q.popitem(last=False); self.store.discard(k); self.ev.append(k)

    def _resize(self, h):
        self.hcap = h
        self.lcap = self.cap - self.hcap
        while self.nlir > self.lcap:
            self._demote()
        while len(self.Q) > self.hcap:
            self._evict_q()

    def access(self, key):
        S, Q = self.S, self.Q
        if key in self.store:
            if S.get(key):
                S.move_to_end(key)
                self._prune()
            elif key in S:
                del S[key]; S[key] = True; del Q[key]
                self.nlir += 1
                self._demote()
            else:
                S[key] = False; Q.move_to_end(key)
            return True
        if self.nlir < self.lcap:
            S.pop(key, None); S[key] = True; self.nlir += 1; self.store.add(key)
            return False
        while len(Q) >= self.hcap:
            self._evict_q()
        self.store.add(key)
        if key in S:
            del S[key]; S[key] = True; self.nlir += 1
            self._demote()
        else:
            S[key] = False; Q[key] = True
        if len(S) > 2 * self.slimit:
            st = self.store
            drop = len(S) - self.slimit
            for k in list(S):
                if drop <= 0: break
                if not S[k] and k not in st:
                    del S[k]; drop -= 1
        return False


class Arc:
    def __init__(self, capacity):
        self.c = capacity
        self.p = 0
        self.t1, self.t2, self.b1, self.b2 = OrderedDict(), OrderedDict(), OrderedDict(), OrderedDict()
        self.store = set()
        self.ev = []

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
            self.p = min(c, self.p + max(len(self.b2) // len(self.b1), 1))
            self._replace(False); del self.b1[key]; self.t2[key] = True; self.store.add(key); return False
        if key in self.b2:
            self.p = max(0, self.p - max(len(self.b1) // len(self.b2), 1))
            self._replace(True); del self.b2[key]; self.t2[key] = True; self.store.add(key); return False
        l1 = len(self.t1) + len(self.b1)
        if l1 == c:
            if len(self.t1) < c:
                self.b1.popitem(last=False); self._replace(False)
            else:
                k, _ = self.t1.popitem(last=False); self.store.discard(k); self.ev.append(k)
        elif l1 < c and l1 + len(self.t2) + len(self.b2) >= c:
            if l1 + len(self.t2) + len(self.b2) == 2 * c:
                self.b2.popitem(last=False)
            self._replace(False)
        self.t1[key] = True; self.store.add(key); return False


class Tlfu:
    """W-TinyLFU: window LRU, SLRU main, frequency-sketch admission."""

    def __init__(self, capacity, wfrac=0.01, pfrac=0.8):
        self.cap = capacity
        self.wcap = max(1, int(capacity * wfrac))
        mcap = capacity - self.wcap
        self.pcap = int(mcap * pfrac)
        self.win, self.prob, self.prot = OrderedDict(), OrderedDict(), OrderedDict()
        self.freq = {}
        self.ops = 0
        self.reset = capacity * 10
        self.store = set()
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
        self.win[key] = True; self.store.add(key)
        if len(self.win) > self.wcap:
            cand, _ = self.win.popitem(last=False)
            if len(self.prob) + len(self.prot) < self.cap - self.wcap:
                self.prob[cand] = True
            elif not self.prob and not self.prot:
                self.store.discard(cand); self.ev.append(cand)
            else:
                victim = next(iter(self.prob)) if self.prob else next(iter(self.prot))
                f = self.freq
                if f.get(cand, 0) > f.get(victim, 0):
                    if victim in self.prob: del self.prob[victim]
                    else: del self.prot[victim]
                    self.store.discard(victim); self.ev.append(victim); self.prob[cand] = True
                else:
                    self.store.discard(cand); self.ev.append(cand)
        return False


class Cache:
    """Follows whichever shadow policy has the most recent hits, evicting only keys it dropped."""

    def __init__(self, capacity):
        self.cap = capacity
        self.experts = [Lirs(capacity, f) for f in FRACS]
        if USE_ARC:
            self.experts.append(Arc(capacity))
        if USE_TLFU:
            self.experts.append(Tlfu(capacity))
        self.score = [0.0] * len(self.experts)
        self.keep = 1.0 - 1.0 / (capacity * DECAY)
        self.n = 0
        self.best = 0
        self.cand = deque()
        self.store = set()

    def access(self, key):
        sc, keep, ex = self.score, self.keep, self.experts
        for i, e in enumerate(ex):
            sc[i] = sc[i] * keep + e.access(key)
        lead = ex[self.best]
        self.cand.extend(lead.ev)
        for e in ex:
            e.ev.clear()
        self.n += 1
        if self.n % EVERY == 0:
            b = max(range(len(sc)), key=lambda i: sc[i])
            if b != self.best and sc[b] > sc[self.best] * HYST:
                self.best = b
                lead = ex[b]
                ls = lead.store
                self.cand = deque(k for k in self.store if k not in ls)
        st = self.store
        if key in st:
            return True
        if len(st) >= self.cap:
            ls, cand = lead.store, self.cand
            while cand:
                k = cand.popleft()
                if k in st and k not in ls:
                    break
            else:
                k = next((k for k in st if k not in ls), None)
                if k is None:
                    k = next(iter(st))
            st.discard(k)
        st.add(key)
        return False
