import random
from collections import OrderedDict


class _Core:
    """W-TinyLFU over a shared frequency table, with a settable window size."""

    def __init__(self, cap, w):
        self.cap = cap; self.w = w
        self.win = OrderedDict(); self.prob = OrderedDict(); self.prot = OrderedDict()
        self.store = set()
        self.out = []

    def access(self, key, f):
        if key in self.win:
            self.win.move_to_end(key); return True
        if key in self.prot:
            self.prot.move_to_end(key); return True
        if key in self.prob:
            del self.prob[key]; self.prot[key] = True
            pcap = int((self.cap - self.w) * 0.8)
            while len(self.prot) > pcap:
                k, _ = self.prot.popitem(last=False); self.prob[k] = True
            return True
        self.store.add(key)
        self.win[key] = True
        wcap = self.w; mcap = self.cap - wcap
        win, prob, prot = self.win, self.prob, self.prot
        while len(win) > wcap:
            cand, _ = win.popitem(last=False)
            if len(prob) + len(prot) < mcap:
                prob[cand] = True; continue
            vq = prob if prob else prot
            victim = next(iter(vq))
            if f.get(cand, 0) > f.get(victim, 0):
                del vq[victim]; self.store.discard(victim); self.out.append(victim); prob[cand] = True
            else:
                self.store.discard(cand); self.out.append(cand)
        while len(self.store) > self.cap:
            vq = prob if prob else prot
            k, _ = vq.popitem(last=False); self.store.discard(k); self.out.append(k)
        return False




class _ARC:
    """ARC."""

    def __init__(self, capacity):
        self.c = capacity
        self.p = 0
        self.t1 = OrderedDict(); self.t2 = OrderedDict()
        self.b1 = OrderedDict(); self.b2 = OrderedDict()
        self.store = set()
        self.out = []

    def _replace(self, in_b2):
        if self.t1 and (len(self.t1) > self.p or (in_b2 and len(self.t1) == self.p)):
            k, _ = self.t1.popitem(last=False); self.b1[k] = True
        else:
            k, _ = self.t2.popitem(last=False); self.b2[k] = True
        self.store.discard(k); self.out.append(k)

    def access(self, key):
        c = self.c
        if key in self.t1:
            del self.t1[key]; self.t2[key] = True; return True
        if key in self.t2:
            self.t2.move_to_end(key); return True
        if key in self.b1:
            self.p = min(c, self.p + max(1, len(self.b2) // max(1, len(self.b1))))
            self._replace(False); del self.b1[key]; self.t2[key] = True; self.store.add(key); return False
        if key in self.b2:
            self.p = max(0, self.p - max(1, len(self.b1) // max(1, len(self.b2))))
            self._replace(True); del self.b2[key]; self.t2[key] = True; self.store.add(key); return False
        l1 = len(self.t1) + len(self.b1)
        if l1 == c:
            if len(self.t1) < c:
                self.b1.popitem(last=False); self._replace(False)
            else:
                k, _ = self.t1.popitem(last=False); self.store.discard(k); self.out.append(k)
        elif l1 < c:
            tot = l1 + len(self.t2) + len(self.b2)
            if tot >= c:
                if tot == 2 * c: self.b2.popitem(last=False)
                self._replace(False)
        self.t1[key] = True; self.store.add(key); return False

class _LIRS:
    """LIRS."""

    def __init__(self, capacity, hfrac=0.01, ghost_mult=3):
        self.cap = capacity
        self.hcap = max(1, int(capacity * hfrac))
        self.lcap = capacity - self.hcap
        self.S = OrderedDict()  # key -> True; recency stack (end = top)
        self.Q = OrderedDict()  # resident HIR
        self.lir = set()
        self.store = set()
        self.out = []
        self.maxS = capacity * ghost_mult

    def _prune(self):
        S = self.S
        while S:
            k = next(iter(S))
            if k in self.lir: break
            del S[k]

    def _demote_bottom(self):
        S = self.S
        k, _ = S.popitem(last=False)
        self.lir.discard(k)
        self.Q[k] = True
        self._prune()

    def access(self, key):
        S, Q, lir = self.S, self.Q, self.lir
        if key in lir:
            first = next(iter(S)) == key
            S.move_to_end(key)
            if first: self._prune()
            return True
        if key in self.store:  # resident HIR
            if key in S:
                del Q[key]; lir.add(key); S.move_to_end(key)
                self._demote_bottom()
            else:
                Q.move_to_end(key); S[key] = True
            self._trim()
            return True
        # miss
        if len(lir) < self.lcap:
            lir.add(key); S[key] = True; S.move_to_end(key); self.store.add(key); return False
        if len(self.store) >= self.cap:
            k, _ = Q.popitem(last=False); self.store.discard(k); self.out.append(k)
        self.store.add(key)
        if key in S:
            lir.add(key); S.move_to_end(key)
            self._demote_bottom()
        else:
            Q[key] = True; S[key] = True
        self._trim()
        return False

    def _trim(self):
        S = self.S
        if len(S) > 2 * self.maxS:
            st = self.store
            for k in [k for k in S if k not in st][:len(S) - self.maxS]:
                del S[k]


class _PRD:
    """Evict the resident whose predicted next access is furthest away; bypass if the new key's is."""

    def __init__(self, capacity, K=32, dmult=4.0, alpha=0.5, bypass=True):
        self.cap = capacity; self.K = K; self.alpha = alpha; self.bypass = bypass
        self.D = capacity * dmult
        self.last = {}; self.est = {}
        self.t = 0
        self.store = {}; self.keys = []
        self.out = []
        self.rng = random.Random(1)

    def _nxt(self, k, t):
        l = self.last[k]; e = self.est.get(k)
        n = l + (e if e is not None else self.D)
        if n < t: n = t + (t - l)
        return n

    def access(self, key):
        self.t += 1; t = self.t
        l = self.last.get(key)
        if l is not None:
            iv = t - l; e = self.est.get(key)
            self.est[key] = iv if e is None else e + self.alpha * (iv - e)
        self.last[key] = t
        s = self.store
        if key in s: return True
        keys = self.keys
        if len(keys) < self.cap:
            s[key] = len(keys); keys.append(key); return False
        n = len(keys); last = self.last; est = self.est; D = self.D
        K = self.K if self.K < n else n
        i = int(self.rng.random() * n)
        vi = -1; vn = -1
        for _ in range(K):
            k = keys[i]; l = last[k]; x = l + est.get(k, D)
            if x < t: x = t + t - l
            if x > vn: vn = x; vi = i
            i += 1
            if i == n: i = 0
        if self.bypass and self._nxt(key, t) >= vn: return False
        v = keys[vi]; del s[v]; self.out.append(v)
        keys[vi] = key; s[key] = vi
        return False

class Cache:
    """Mirror whichever shadow policy has had the most hits lately; only requested keys are added.

    Shadows: W-TinyLFU (1% and 20% windows), ARC, LIRS and two predicted-reuse policies.
    """

    def __init__(self, capacity, half=10.0, margin=0.1, lam=1.0, every=0.5, age=10):
        self.cap = capacity
        self.all = [_Core(capacity, max(1, int(capacity * 0.01))), _Core(capacity, max(1, int(capacity * 0.2))),
                    _ARC(capacity), _LIRS(capacity), _PRD(capacity, 32, 1.0, 0.5), _PRD(capacity, 32, 16.0, 0.25)]
        self.ncore = 2
        self.score = [0.0] * len(self.all)
        self.decay = 0.5 ** (1.0 / (capacity * half))
        self.freq = {}
        self.reset_at = int(capacity * age)
        self.ops = 0
        self.store = OrderedDict()
        self.lead = 0; self.pend = []
        self.lam = lam; self.margin = margin * capacity
        self.every = max(1, int(capacity * every)); self.ov = [0] * len(self.all)

    def access(self, key):
        self.ops += 1
        f = self.freq
        f[key] = f.get(key, 0) + 1
        if self.ops % self.reset_at == 0:
            self.freq = f = {a: b >> 1 for a, b in f.items() if b > 1}
        d = self.decay; sc = self.score; al = self.all; nc = self.ncore
        for i in range(len(al)):
            s = al[i]
            sc[i] = sc[i] * d + (s.access(key, f) if i < nc else s.access(key))
        R = self.store
        if self.ops % self.every == 0:
            self.ov = [sum(1 for k in R if k in s.store) for s in al]
        ov = self.ov; lam = self.lam
        best = 0; bv = -1.0
        for i in range(len(sc)):
            v = sc[i] + lam * ov[i]
            if v > bv: best = i; bv = v
        if best != self.lead and bv > sc[self.lead] + lam * ov[self.lead] + self.margin:
            self.lead = best; self.pend = []
        L = al[self.lead]
        pend = self.pend
        pend.extend(L.out)
        if len(pend) > 4 * self.cap: del pend[:-self.cap]
        for s in al: s.out.clear()
        if key in R:
            R.move_to_end(key); return True
        lead = L.store
        if key in lead or len(R) < self.cap:
            R[key] = True
            if len(R) > self.cap:
                v = None
                while pend:
                    k = pend.pop()
                    if k in R and k not in lead:
                        v = k; break
                if v is None:
                    for k in R:
                        if k not in lead: v = k; break
                del R[v]
        return False
