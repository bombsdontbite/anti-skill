import random
from collections import OrderedDict

DK = 30          # score window, in multiples of capacity
DWELL = 2        # minimum requests between switches, in multiples of capacity
MARGIN = 5.0
G = 1.0          # hits a switch must gain per key it would replace
GHOST = 200      # keys remembered after eviction, in multiples of capacity
K = 32           # keys sampled per eviction
ND = 0.9999
SHR = 0.2
BYPASS = 0.7
ETA = 0.1
FMIN = 0.3
FMAX = 20.0


class LRU:
    def __init__(self, c, ev):
        self.c = c; self.ev = ev; self.store = OrderedDict()

    def access(self, key):
        s = self.store
        if key in s:
            s.move_to_end(key); return True
        if len(s) >= self.c:
            k, _ = s.popitem(last=False); self.ev.append(k)
        s[key] = True
        return False


class Pred:
    """Evict the sampled key whose predicted next use is furthest away."""

    def __init__(self, c, ev):
        self.c = c; self.ev = ev
        self.store = {}; self.keys = []
        self.last = {}; self.first = {}; self.cnt = {}; self.iv = {}
        self.t = 0; self.rng = random.Random(1)
        self.ghost_cap = GHOST * c
        # Decayed counts of first sightings, returns, and first-return distances.
        self.nn = 1.0; self.nr = 1.0; self.ds = float(c); self.newi = 2.0 * c
        self.bypass = BYPASS
        self.pb = {}; self.pv = {}   # bypassed key <-> the victim kept instead

    def access(self, key):
        self.t += 1; now = self.t
        last = self.last; iv = self.iv
        L = last.get(key)
        if L is not None:
            n = self.cnt[key] = self.cnt[key] + 1
            if n == 2: self.nr += 1; self.ds += now - L
            iv[key] = (now - self.first[key] + SHR * self.newi) / (n - 1 + SHR)
        else:
            self.first[key] = now; self.cnt[key] = 1
            self.nn = self.nn * ND + 1; self.nr *= ND; self.ds *= ND
            # Expected gap before a never-seen key returns: mean return distance / return rate.
            self.newi = (self.ds / self.nr) * (self.nn / self.nr)
        last[key] = now
        pb = self.pb; pv = self.pv
        if key in pb:
            v = pb.pop(key); pv.pop(v, None)
            self.bypass = min(FMAX, self.bypass * (1 + ETA))
        elif key in pv:
            b = pv.pop(key); pb.pop(b, None)
            self.bypass = max(FMIN, self.bypass / (1 + ETA))
        store = self.store
        if key in store: return True
        if len(store) >= self.c:
            keys = self.keys; n = len(keys); rnd = self.rng.random; newi = self.newi
            best = None; bp = -1
            for _ in range(K):
                k = keys[int(rnd() * n)]
                Lk = last[k]; p = Lk + iv.get(k, newi)
                if p < now: p = now + now - Lk
                if p > bp: bp = p; best = k
            if iv.get(key, newi) > self.bypass * (bp - now):
                if best not in pv:
                    pb[key] = best; pv[best] = key
                    if len(pb) > self.c:
                        b = next(iter(pb)); pv.pop(pb.pop(b), None)
                return False
            i = store.pop(best); lastk = keys.pop()
            if lastk != best: keys[i] = lastk; store[lastk] = i
            self.ev.append(best)
        store[key] = len(self.keys); self.keys.append(key)
        if len(last) > self.ghost_cap + self.c:
            for k in list(last):
                if k not in store:
                    del last[k]; iv.pop(k, None); self.first.pop(k, None); self.cnt.pop(k, None)
                    if len(last) <= self.ghost_cap: break
        return False


class Cache:
    """Follow whichever shadow policy has the most recent hits, switching only when it pays."""

    def __init__(self, capacity):
        self.c = capacity
        self.evs = [[], []]
        self.pols = [Pred(capacity, self.evs[0]), LRU(capacity, self.evs[1])]
        self.score = [0.0, 0.0]
        self.lead = 0
        self.dwell = DWELL * capacity
        self.since = 0
        self.decay = 1 - 1 / (DK * capacity)
        self.store = set()
        self.diff = set()   # cached keys the leader does not hold

    def access(self, key):
        sc = self.score; pols = self.pols; evs = self.evs; decay = self.decay
        for i in range(len(pols)):
            sc[i] *= decay
            if pols[i].access(key): sc[i] += 1.0
        lead = self.lead
        best = lead
        for i in range(len(pols)):
            if sc[i] > sc[best]: best = i
        store = self.store; diff = self.diff
        self.since += 1
        switch = False
        if best != lead and self.since > self.dwell and sc[best] > sc[lead] + MARGIN:
            bs = pols[best].store
            nd = 0
            for k in store:
                if k not in bs: nd += 1
            if sc[best] - sc[lead] > G * nd:
                switch = True
            else:
                self.since = self.dwell - self.c // 4
        if switch:
            lead = self.lead = best
            self.since = 0
            ls = pols[lead].store
            self.diff = diff = {k for k in store if k not in ls}
        else:
            for k in evs[lead]:
                if k in store: diff.add(k)
        for ev in evs: ev.clear()
        ls = pols[lead].store
        diff.discard(key)
        if key in store:
            if key not in ls: diff.add(key)
            return True
        if key in ls:
            store.add(key)
            if len(store) > self.c:
                store.discard(diff.pop() if diff else next(iter(store - {key})))
        return False
