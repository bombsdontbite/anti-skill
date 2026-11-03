import random, heapq, math
from collections import OrderedDict, deque

class LRU:
    def __init__(self, c, ev):
        self.c = c; self.d = OrderedDict(); self.ev = ev
    def access(self, key):
        d = self.d
        if key in d:
            d.move_to_end(key); return True
        if len(d) >= self.c:
            k, _ = d.popitem(last=False); self.ev.append(k)
        d[key] = None; return False
    def has(self, k): return k in self.d

class LIRS:
    def __init__(self, c, ev, hfrac=0.01):
        self.c = c; self.hc = max(1, int(c * hfrac)); self.lc = c - self.hc
        self.S = OrderedDict(); self.Q = OrderedDict(); self.lir = set(); self.st = set()
        self.maxS = 3 * c; self.ev = ev
    def has(self, k): return k in self.st
    def _prune(self):
        S, lir = self.S, self.lir
        while S:
            k = next(iter(S))
            if k in lir: return
            del S[k]
    def access(self, key):
        S, Q, lir, st = self.S, self.Q, self.lir, self.st
        if key in lir:
            first = next(iter(S)) == key
            S.move_to_end(key)
            if first: self._prune()
            return True
        hit = key in st
        if not hit:
            if len(lir) < self.lc:
                lir.add(key); S[key] = 1; S.move_to_end(key); st.add(key); return False
            if len(Q) >= self.hc:
                k, _ = Q.popitem(last=False); st.discard(k); self.ev.append(k)
            st.add(key)
        if key in S:
            S.move_to_end(key); Q.pop(key, None); lir.add(key)
            k = next(iter(S)); lir.discard(k); del S[k]; Q[k] = None
            self._prune()
        else:
            S[key] = 0
            if hit: Q.move_to_end(key)
            else: Q[key] = None
        if len(S) > 2 * self.maxS:
            drop = len(S) - self.maxS
            for k in [k for k in S if k not in lir and k not in st][:drop]: del S[k]
        return hit

class TLFU:
    def __init__(self, c, ev):
        self.c = c; self.wc = max(1, c // 100); self.mc = c - self.wc; self.pc = int(self.mc * 0.8)
        self.win = OrderedDict(); self.prob = OrderedDict(); self.prot = OrderedDict()
        self.freq = {}; self.n = 0; self.sample = 10 * c; self.ev = ev
    def has(self, k): return k in self.win or k in self.prob or k in self.prot
    def access(self, key):
        f = self.freq; f[key] = f.get(key, 0) + 1; self.n += 1
        if self.n >= self.sample:
            self.n //= 2; self.freq = f = {a: b >> 1 for a, b in f.items() if b > 1}
        win, prob, prot = self.win, self.prob, self.prot
        if key in win:
            win.move_to_end(key); return True
        if key in prot:
            prot.move_to_end(key); return True
        if key in prob:
            del prob[key]; prot[key] = None
            if len(prot) > self.pc:
                k, _ = prot.popitem(last=False); prob[k] = None
            return True
        win[key] = None
        if len(win) > self.wc:
            cand, _ = win.popitem(last=False)
            if len(prob) + len(prot) < self.mc:
                prob[cand] = None
            else:
                victim = next(iter(prob)) if prob else next(iter(prot))
                if f.get(cand, 0) > f.get(victim, 0):
                    if victim in prob: del prob[victim]
                    else: del prot[victim]
                    self.ev.append(victim); prob[cand] = None
                else:
                    self.ev.append(cand)
        return False


class PNEXT:
    """Approximate Belady: evict the sampled (or recently inserted) key whose predicted next
    use is furthest; prediction = last use + EWMA reuse gap."""
    def __init__(self, c, ev):
        self.c = c; self.t = 0; self.last = {}; self.ia = {}; self.arr = []; self.pos = {}
        self.first = float(c); self.nn = 0.0; self.nr = 0.0
        self.rng = random.Random(12345); self.ev = ev; self.recent = deque(maxlen=PN_POOL)
    def has(self, k): return k in self.pos
    def access(self, key):
        self.t = now = self.t + 1
        last, ia = self.last, self.ia
        l = last.get(key)
        if l is not None:
            gap = now - l; g = ia.get(key)
            if g is None:
                ia[key] = gap; self.first += 0.05 * (gap - self.first); self.nr += 1.0
            else:
                ia[key] = g + 0.5 * (gap - g)
        else:
            self.nn = self.nn * 0.999 + 1.0; self.nr *= 0.999
        last[key] = now
        pos = self.pos
        if key in pos: return True
        arr = self.arr
        if len(arr) >= self.c:
            pr = self.nr / self.nn if self.nn > 0 else 1.0
            fp = self.first * PN_PRIOR / (pr if pr > 0.05 else 0.05)
            rnd = self.rng.random; n = len(arr); best = -1; bi = 0
            for _ in range(24):
                i = int(rnd() * n); k = arr[i]; l = last[k]; g = ia.get(k)
                p = l + (fp if g is None else g)
                if p < now: p = now + now - l
                if p > best: best = p; bi = i
            for k in self.recent:
                if k in pos:
                    l = last[k]; g = ia.get(k)
                    p = l + (fp if g is None else g)
                    if p < now: p = now + now - l
                    if p > best: best = p; bi = pos[k]
            v = arr[bi]; lk = arr[-1]; arr[bi] = lk; pos[lk] = bi; arr.pop(); del pos[v]; self.ev.append(v)
        pos[key] = len(arr); arr.append(key); self.recent.append(key)
        if len(last) > 16 * self.c:
            cut = sorted(last.values())[len(last) // 2]
            for k in [k for k, v in last.items() if v < cut and k not in pos]:
                del last[k]; ia.pop(k, None)
        return False

class ARC:
    def __init__(self, c, ev):
        self.c = c; self.p = 0; self.ev = ev
        self.t1 = OrderedDict(); self.t2 = OrderedDict(); self.b1 = OrderedDict(); self.b2 = OrderedDict()
    def has(self, k): return k in self.t1 or k in self.t2
    def _rep(self, inb2):
        t1 = self.t1
        if t1 and (len(t1) > self.p or (inb2 and len(t1) == self.p)):
            k, _ = t1.popitem(last=False); self.b1[k] = None
        else:
            k, _ = self.t2.popitem(last=False); self.b2[k] = None
        self.ev.append(k)
    def access(self, key):
        t1, t2, b1, b2, c = self.t1, self.t2, self.b1, self.b2, self.c
        if key in t1:
            del t1[key]; t2[key] = None; return True
        if key in t2:
            t2.move_to_end(key); return True
        if key in b1:
            self.p = min(c, self.p + max(len(b2) // len(b1), 1))
            self._rep(False); del b1[key]; t2[key] = None; return False
        if key in b2:
            self.p = max(0, self.p - max(len(b1) // len(b2), 1))
            self._rep(True); del b2[key]; t2[key] = None; return False
        l1 = len(t1) + len(b1)
        if l1 == c:
            if len(t1) < c:
                b1.popitem(last=False); self._rep(False)
            else:
                k, _ = t1.popitem(last=False); self.ev.append(k)
        elif l1 < c:
            tot = l1 + len(t2) + len(b2)
            if tot >= c:
                if tot == 2 * c: b2.popitem(last=False)
                self._rep(False)
        t1[key] = None; return False


class LRFU:
    def __init__(self, c, ev):
        self.c = c; self.lam = LF_LAM / c; self.t = 0; self.v = {}; self.st = set(); self.h = []; self.ev = ev
    def has(self, k): return k in self.st
    def access(self, key):
        self.t = t = self.t + 1; lt = self.lam * t; v = self.v
        old = v.get(key)
        nv = lt if old is None else lt + math.log2(1.0 + 2.0 ** (old - lt))
        v[key] = nv; st = self.st
        if key in st:
            heapq.heappush(self.h, (nv, key)); return True
        if len(st) >= self.c:
            h = self.h
            while True:
                x, k = heapq.heappop(h)
                if k in st and v[k] == x: st.discard(k); self.ev.append(k); break
        st.add(key); heapq.heappush(self.h, (nv, key))
        if len(self.h) > 8 * self.c:
            self.h = [(v[k], k) for k in st]; heapq.heapify(self.h)
        if len(v) > 8 * self.c:
            cut = sorted(v.values())[len(v) // 2]
            for k in [k for k, x in v.items() if x < cut and k not in st]: del v[k]
        return False

KINDS = {"LRFU": LRFU, "ARC": ARC, "LRU": LRU, "LIRS": LIRS, "TLFU": TLFU, "PNEXT": PNEXT}
EXPERTS = "LIRS,PNEXT,LRFU,TLFU" 
PN_PRIOR = 1.0
PN_POOL = 8
LF_LAM = 0.05
THRESH = 10 
DECAY = 0.999
DW = 20 
KAPPA = 2 
MARGIN = 1.02

class Cache:
    """Shadow-run several policies; the real cache converges to the one with most recent hits."""
    def __init__(self, capacity):
        self.c = capacity
        names = EXPERTS.split(",")
        self.evs = [[] for _ in names]
        self.ex = [KINDS[n](capacity, e) for n, e in zip(names, self.evs)]
        self.sc = [0.0] * len(self.ex); self.lead = 0
        self.store = OrderedDict(); self.pend = deque()
        self.dec = 1.0 - 1.0 / (DW * capacity) if DW else DECAY
        self.t = 0; self.cool = 0

    def access(self, key):
        ex, sc, evs, dec = self.ex, self.sc, self.evs, self.dec
        for i in range(len(ex)):
            sc[i] = sc[i] * dec + ex[i].access(key)
        L = self.lead; le = ex[L]
        best = 0
        for i in range(1, len(ex)):
            if sc[i] > sc[best]: best = i
        self.t += 1
        if best != L and self.t >= self.cool and sc[best] > sc[L] * MARGIN + 1 + THRESH:
            nb = ex[best]; diff = [k for k in self.store if not nb.has(k)]
            # switching costs about one miss per differing key that the new leader would hit
            if sc[best] - sc[L] > KAPPA * len(diff) * sc[L] * (1.0 - self.dec):
                self.lead = L = best; le = nb; self.pend = deque(diff)
            else:
                self.cool = self.t + self.c
        st = self.store
        self.pend.extend(evs[L])
        for e in evs: e.clear()
        if key in st:
            st.move_to_end(key); return True
        st[key] = None
        if not le.has(key): self.pend.append(key)
        if len(st) > self.c:
            pend = self.pend
            while pend:
                k = pend.popleft()
                if k in st and k != key and not le.has(k):
                    del st[k]; break
            else:
                st.popitem(last=False)
        return False
