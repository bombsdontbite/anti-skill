import random
from collections import OrderedDict


class LRU:
    def __init__(self, capacity):
        self.cap = capacity; self.store = OrderedDict(); self.ev = []

    def access(self, key):
        s = self.store
        if key in s:
            s.move_to_end(key); return True
        if len(s) >= self.cap: self.ev.append(s.popitem(last=False)[0])
        s[key] = True; return False


class PBEL:
    """Approximate Belady: evict the sampled key whose next request is predicted latest.

    Next request = last access + smoothed inter-arrival time; once overdue, the guess moves
    further out the longer the key stays silent. Keys seen once are predicted far away, so a
    new key is admitted only if some sampled key is predicted even later.
    """
    SAMPLE = 32
    ALPHA = 0.25
    OVER = 0.5
    NEW = 64.0
    GH = 8

    def __init__(self, capacity):
        self.cap = capacity; self.t = 0
        self.keys = []; self.pos = {}
        self.last = {}; self.irt = {}
        self.rng = random.Random(7)
        self.store = self.pos; self.ev = []

    def _pred(self, k, t):
        l = self.last[k]; i = self.irt.get(k)
        if i is None: return t + self.NEW * self.cap
        p = l + i
        if p < t:
            p = t + self.OVER * (t - l)
        return p

    def access(self, key):
        self.t += 1; t = self.t; last = self.last; irt = self.irt
        l = last.get(key)
        if l is not None:
            d = t - l; o = irt.get(key)
            irt[key] = d if o is None else o + self.ALPHA * (d - o)
        last[key] = t
        if key in self.pos: return True
        if len(self.keys) >= self.cap:
            ks = self.keys; r = self.rng.random; n = len(ks)
            bi = -1; bp = -1
            for _ in range(self.SAMPLE):
                i = int(r() * n); p = self._pred(ks[i], t)
                if p > bp: bp = p; bi = i
            if self._pred(key, t) >= bp:
                self._gc(); return False
            k = ks[bi]; e = ks[-1]; ks[bi] = e; self.pos[e] = bi; ks.pop(); del self.pos[k]; self.ev.append(k)
        self.pos[key] = len(self.keys); self.keys.append(key)
        self._gc()
        return False

    def _gc(self):
        if len(self.last) > self.GH * self.cap * 2:
            t = self.t; lim = self.GH * self.cap * 4
            last = self.last; irt = self.irt; pos = self.pos
            for k in [k for k, l in last.items() if t - l > lim and k not in pos]:
                del last[k]; irt.pop(k, None)
            if len(last) > self.GH * self.cap: self.GH *= 2


class Cache:
    """Runs PBEL and LRU as shadows and makes the real cache follow whichever is hitting more.

    A switch needs the short-term score ahead by a margin and the long-term score to agree.
    After a switch the real cache converges to the new leader by evicting keys it lacks.
    """
    DECAY = 4.0
    H = 0.015
    DECAY2 = 64.0

    def __init__(self, capacity):
        self.cap = capacity
        self.sh = [PBEL(capacity), LRU(capacity)]
        self.sc = [0.0] * len(self.sh); self.sc2 = [0.0] * len(self.sh)
        self.a = 1.0 - 1.0 / (self.DECAY * capacity)
        self.a2 = 1.0 - 1.0 / (self.DECAY2 * capacity)
        self.lead = 0
        self.store = set(); self.orph = []

    def access(self, key):
        R = self.store; hit = key in R
        sh = self.sh; L = sh[self.lead]
        a = self.a; sc = self.sc
        a2 = self.a2; sc2 = self.sc2
        for i, s in enumerate(sh):
            x = 1.0 if s.access(key) else 0.0
            sc[i] = sc[i] * a + x; sc2[i] = sc2[i] * a2 + x
        best = self.lead
        for i in range(len(sh)):
            if sc[i] > sc[best]: best = i
        if best != self.lead and sc[best] > sc[self.lead] + self.H * self.DECAY * self.cap and sc2[best] >= sc2[self.lead]:
            self.lead = best; L = sh[best]
            ls = L.store; self.orph = [k for k in R if k not in ls]
        ls = L.store
        for s in sh:
            if s is L:
                for k in s.ev:
                    if k in R: self.orph.append(k)
            s.ev.clear()
        if not hit and key in ls:
            if len(R) >= self.cap:
                self._evict(ls)
            R.add(key)
        return hit

    def _evict(self, ls):
        R = self.store; o = self.orph
        while o:
            k = o.pop()
            if k in R and k not in ls:
                R.discard(k); return
        o.extend(k for k in R if k not in ls)
        if o:
            R.discard(o.pop()); return
        R.pop()
