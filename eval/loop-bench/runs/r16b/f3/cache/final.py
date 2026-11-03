import heapq
import random
from collections import OrderedDict, deque



class TinyLFU:
    """W-TinyLFU whose window is sized ARC-style by ghost hits."""

    def __init__(self, capacity, win_frac=0.01, prot_frac=0.5, reset_mul=10, gmul=0.5, delta=3.0, thr=2, fcap=3):
        self.c = capacity
        self.wc = max(1.0, capacity * win_frac)
        self.prot_frac = prot_frac
        self.win = OrderedDict(); self.prob = OrderedDict(); self.prot = OrderedDict()
        self.gw = OrderedDict(); self.gm = OrderedDict()
        self.gcap = max(1, int(capacity * gmul))
        self.delta = delta
        self.thr = thr
        self.fcap = fcap
        self.f = {}
        self.ops = 0
        self.reset = reset_mul * capacity
        self.store = set()
        self.ev = deque()

    def _ghost(self, g, k):
        g[k] = True
        if len(g) > self.gcap:
            g.popitem(last=False)

    def _evict(self, k):
        self.store.discard(k)
        self.ev.append(k)

    def access(self, key):
        f = self.f
        v = f.get(key, 0)
        if v < self.fcap:
            f[key] = v + 1
        self.ops += 1
        if self.ops >= self.reset:
            self.ops = 0
            self.f = f = {a: b >> 1 for a, b in f.items() if b > 1}
        if key in self.win:
            self.win.move_to_end(key); return True
        if key in self.prot:
            self.prot.move_to_end(key); return True
        if key in self.prob:
            del self.prob[key]; self.prot[key] = True
            pc = max(1, int((self.c - self.wc) * self.prot_frac))
            while len(self.prot) > pc:
                k, _ = self.prot.popitem(last=False); self.prob[k] = True
            return True
        c = self.c
        if key in self.gw:
            del self.gw[key]
            if f.get(key, 0) <= self.thr:
                    self.wc = min(c - 1.0, self.wc + self.delta * max(1.0, len(self.gm) / max(1, len(self.gw) + 1)))
        elif key in self.gm:
            del self.gm[key]
            self.wc = max(1.0, self.wc - self.delta * max(1.0, len(self.gw) / max(1, len(self.gm) + 1)))
        win = self.win; prob = self.prob; prot = self.prot
        win[key] = True; self.store.add(key)
        wc = int(self.wc); mc = c - wc
        if len(win) + len(prob) + len(prot) > c:
            if len(win) > wc or not (prob or prot):
                cand, _ = win.popitem(last=False)
                if prob:
                    victim = next(iter(prob)); vq = prob
                elif prot:
                    victim = next(iter(prot)); vq = prot
                else:
                    vq = None
                if vq is not None and f.get(cand, 0) > f.get(victim, 0):
                    del vq[victim]; self._evict(victim); prob[cand] = True
                    self._ghost(self.gm, victim)
                else:
                    self._evict(cand); self._ghost(self.gw, cand)
            else:
                if prob:
                    victim, _ = prob.popitem(last=False)
                else:
                    victim, _ = prot.popitem(last=False)
                self._evict(victim); self._ghost(self.gm, victim)
        while len(win) > wc and len(prob) + len(prot) < mc:
            k, _ = win.popitem(last=False); prob[k] = True
        return False



class LIRS:
    """LIRS."""

    def __init__(self, capacity, hir_frac=0.05, smul=4):
        self.c = capacity
        self.lh = max(1, int(capacity * hir_frac))
        if capacity > 1:
            self.lh = min(self.lh, capacity - 1)
        self.ll = capacity - self.lh
        self.S = OrderedDict()  # key -> True; recency stack, oldest first
        self.Q = OrderedDict()  # resident HIR
        self.lir = set()
        self.nr = OrderedDict()  # non-resident HIR still in S
        self.smax = smul * capacity
        self.store = set()
        self.ev = deque()

    def _prune(self):
        S = self.S; lir = self.lir
        while S:
            k = next(iter(S))
            if k in lir:
                break
            del S[k]
            self.nr.pop(k, None)

    def _demote(self):
        S = self.S
        k = next(iter(S))
        del S[k]
        self.lir.discard(k)
        self.Q[k] = True
        self._prune()

    def _evict(self, k):
        self.store.discard(k)
        self.ev.append(k)

    def access(self, key):
        S = self.S; Q = self.Q; lir = self.lir
        if key in lir:
            bottom = next(iter(S)) == key
            S.move_to_end(key)
            if bottom:
                self._prune()
            return True
        if key in Q:
            if key in S:
                del Q[key]; lir.add(key); S.move_to_end(key)
                self._demote()
            else:
                S[key] = True; Q.move_to_end(key)
            self._trim()
            return True
        if len(lir) < self.ll:
            lir.add(key); S[key] = True; S.move_to_end(key); self.store.add(key)
            return False
        if len(Q) >= self.lh or len(self.store) >= self.c:
            k, _ = Q.popitem(last=False); self._evict(k)
            if k in S:
                self.nr[k] = True
        self.store.add(key)
        if key in S:
            self.nr.pop(key, None)
            lir.add(key); S.move_to_end(key)
            self._demote()
        else:
            S[key] = True; Q[key] = True
        self._trim()
        return False

    def _trim(self):
        S = self.S; nr = self.nr
        while len(S) > self.smax and nr:
            k, _ = nr.popitem(last=False)
            del S[k]



class Pred:
    """Sampled eviction of the key predicted to return last (EWMA reuse interval)."""

    def __init__(self, capacity, K=16, alpha=0.5, d0=1.0, hist=4, beta=0.01):
        self.c = capacity
        self.K = K; self.a = alpha; self.d0 = d0 * capacity
        self.hmax = hist * capacity
        self.last = OrderedDict(); self.d = {}
        self.arr = []; self.pos = {}
        self.t = 0
        self.beta = beta
        self.nnew = 1.0; self.nret = 1.0; self.fi = float(capacity)
        self.rng = random.Random(12345)
        self.store = self.pos
        self.ev = deque()

    def _pn(self, k, now):
        last = self.last[k]; d = self.d.get(k)
        if d is None:
            return last + self.fi * self.nnew / self.nret + max(0, now - last) * self.d0
        p = last + d
        if p < now:
            return now + (now - last)
        return p

    def access(self, key):
        self.t += 1; now = self.t
        last = self.last; dd = self.d
        lt = last.get(key)
        if lt is not None:
            iv = now - lt
            od = dd.get(key)
            if od is None:
                b = self.beta
                self.nret = self.nret * (1 - b) + b
                self.fi = self.fi * (1 - b) + b * iv
            dd[key] = iv if od is None else self.a * iv + (1 - self.a) * od
            last.move_to_end(key)
        else:
            b = self.beta
            self.nnew = self.nnew * (1 - b) + b
        last[key] = now
        n = 0
        while len(last) > self.hmax and n < 4:
            n += 1
            k = next(iter(last))
            if k in self.pos:
                last.move_to_end(k)
            else:
                del last[k]; dd.pop(k, None)
        if key in self.pos:
            return True
        arr = self.arr; pos = self.pos
        if len(arr) < self.c:
            pos[key] = len(arr); arr.append(key); return False
        # key itself is a candidate: refusing admission is allowed
        best = key; bp = self._pn(key, now)
        rng = self.rng; n = len(arr)
        for _ in range(self.K):
            k = arr[int(rng.random() * n)]
            p = self._pn(k, now)
            if p > bp:
                bp = p; best = k
        if best is key:
            return False
        i = pos.pop(best); arr[i] = key; pos[key] = i
        self.ev.append(best)
        return False


class LFU:
    """LFU over full history with periodic halving; refuses keys not more frequent than the minimum."""

    def __init__(self, capacity, age=50):
        self.c = capacity
        self.cnt = {}
        self.h = []
        self.t = 0
        self.age = age * capacity if age else 0
        self.store = set()
        self.ev = deque()

    def _rebuild(self):
        self.cnt = {k: v >> 1 for k, v in self.cnt.items() if v > 1 or k in self.store}
        cnt = self.cnt
        self.h = [(cnt[k], 0, k) for k in self.store]
        heapq.heapify(self.h)

    def access(self, key):
        self.t += 1
        if self.age and self.t % self.age == 0:
            self._rebuild()
        cnt = self.cnt
        v = cnt.get(key, 0) + 1
        cnt[key] = v
        store = self.store; h = self.h
        if key in store:
            heapq.heappush(h, (v, self.t, key))
            return True
        if len(store) < self.c:
            store.add(key); heapq.heappush(h, (v, self.t, key)); return False
        while True:
            c0, t0, k0 = h[0]
            if k0 in store and cnt[k0] == c0:
                break
            heapq.heappop(h)
        if v > c0:
            heapq.heappop(h); store.discard(k0); self.ev.append(k0)
            store.add(key); heapq.heappush(h, (v, self.t, key))
        return False


class Cache:
    """Simulates five policies; the real cache lazily follows whichever has hit most lately."""

    def __init__(self, capacity, half=10.0, M=16, rb=0.85):
        self.c = capacity
        self.sh = [TinyLFU(capacity, win_frac=0.05), LIRS(capacity),
                   TinyLFU(capacity, prot_frac=0.8, reset_mul=20, fcap=1000),
                   Pred(capacity, K=16, hist=10, alpha=0.3), LFU(capacity, age=0)]
        self.cand = deque()
        for s in self.sh:
            s.ev = self.cand
        self.sc = [0.0] * len(self.sh)
        self.keep = 0.5 ** (1.0 / max(1.0, half * capacity))
        self.M = M
        self.rb = rb
        self.lead = 0
        self.store = set()

    def access(self, key):
        store = self.store
        hit = key in store
        sc = self.sc; keep = self.keep
        # hits on keys the real cache lacks count less, which damps switching
        inc = 1.0 if hit else self.rb
        for i, s in enumerate(self.sh):
            h = s.access(key)
            sc[i] = sc[i] * keep + (inc if h else 0.0)
        other = self.lead
        for i in range(len(sc)):
            if sc[i] > sc[other]:
                other = i
        if other != self.lead:
            self.lead = other
            ls = self.sh[other].store
            self.cand.extendleft([k for k in store if k not in ls])
        if hit:
            return True
        ls = self.sh[self.lead].store
        if key not in ls:
            return False
        store.add(key)
        if len(store) > self.c:
            # evict a key the leader lacks, preferring one few other policies keep
            cand = self.cand
            best = None; bv = 1e300; seen = []
            while cand and len(seen) < self.M:
                k = cand.popleft()
                if k in store and k not in ls and k != key:
                    seen.append(k)
                    v = 0.0
                    for i, t in enumerate(self.sh):
                        if k in t.store:
                            v += sc[i]
                    if v < bv:
                        bv = v; best = k
                        if v == 0.0:
                            break
            if best is not None:
                seen.remove(best)
                cand.extendleft(seen)
                store.discard(best)
                return False
            for k in store:
                if k not in ls and k != key:
                    store.discard(k)
                    return False
            for k in store:
                if k != key:
                    store.discard(k)
                    return False
        return False
