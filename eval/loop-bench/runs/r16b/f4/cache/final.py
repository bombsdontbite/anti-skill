from collections import OrderedDict, deque
import heapq
import random


from collections import OrderedDict


class Seg:
    """W-TinyLFU: LRU window, SLRU main, admission by shared frequency counts."""

    def __init__(self, cap, wcap, pfrac, k=1):
        self.k = k
        self.cap = cap; self.wcap = wcap; self.pfrac = pfrac
        self.win = OrderedDict(); self.prob = OrderedDict(); self.prot = OrderedDict()
        self.store = {}; self.ev = []
        self.ev = []

    def access(self, key, f):
        store = self.store
        if key in store:
            if key in self.win:
                self.win.move_to_end(key)
            elif key in self.prot:
                self.prot.move_to_end(key)
            else:
                del self.prob[key]
                self.prot[key] = None
                pcap = int((self.cap - self.wcap) * self.pfrac)
                while len(self.prot) > pcap:
                    k, _ = self.prot.popitem(last=False)
                    self.prob[k] = None
            return True
        store[key] = None
        win = self.win; prob = self.prob; prot = self.prot
        win[key] = None
        mcap = self.cap - self.wcap
        while len(win) > self.wcap and len(prob) + len(prot) < mcap:
            k, _ = win.popitem(last=False)
            prob[k] = None
        if len(store) > self.cap:
            if len(win) > self.wcap:
                cand, _ = win.popitem(last=False)
                src = prob if prob else prot
                if self.k == 1:
                    victim = next(iter(src)); vf = f.get(victim, 0)
                else:
                    victim = None; vf = 99
                    for i, v in zip(range(self.k), src):
                        x = f.get(v, 0)
                        if x < vf:
                            victim = v; vf = x
                if f.get(cand, 0) > vf:
                    if victim in prob:
                        del prob[victim]
                    else:
                        del prot[victim]
                    del store[victim]; self.ev.append(victim)
                    prob[cand] = None
                else:
                    del store[cand]; self.ev.append(cand)
            else:
                if prob:
                    k, _ = prob.popitem(last=False)
                else:
                    k, _ = prot.popitem(last=False)
                del store[k]; self.ev.append(k)
        return False



class ARC:
    """ARC."""

    def __init__(self, capacity):
        self.c = capacity
        self.p = 0
        self.t1 = OrderedDict(); self.t2 = OrderedDict()
        self.b1 = OrderedDict(); self.b2 = OrderedDict()
        self.store = {}; self.ev = []

    def _replace(self, in_b2):
        if self.t1 and (len(self.t1) > self.p or (in_b2 and len(self.t1) == self.p)):
            k, _ = self.t1.popitem(last=False); self.b1[k] = None
        else:
            k, _ = self.t2.popitem(last=False); self.b2[k] = None
        del self.store[k]; self.ev.append(k)

    def access(self, key):
        c = self.c
        if key in self.store:
            if key in self.t1:
                del self.t1[key]
            else:
                del self.t2[key]
            self.t2[key] = None
            return True
        if key in self.b1:
            self.p = min(c, self.p + max(1, len(self.b2) // len(self.b1)))
            self._replace(False)
            del self.b1[key]; self.t2[key] = None
        elif key in self.b2:
            self.p = max(0, self.p - max(1, len(self.b1) // len(self.b2)))
            self._replace(True)
            del self.b2[key]; self.t2[key] = None
        else:
            l1 = len(self.t1) + len(self.b1)
            if l1 == c:
                if len(self.t1) < c:
                    self.b1.popitem(last=False); self._replace(False)
                else:
                    k, _ = self.t1.popitem(last=False); del self.store[k]; self.ev.append(k)
            else:
                tot = l1 + len(self.t2) + len(self.b2)
                if tot >= c:
                    if tot == 2 * c:
                        self.b2.popitem(last=False)
                    if len(self.store) >= c:
                        self._replace(False)
            self.t1[key] = None
        self.store[key] = None
        return False



class S3:
    """S3-FIFO."""

    def __init__(self, capacity, sfrac=0.1):
        self.cap = capacity
        self.scap = max(1, int(capacity * sfrac))
        self.S = deque(); self.M = deque(); self.G = {}
        self.ghost = deque()
        self.store = {}; self.ev = []
        self.ns = 0; self.nm = 0

    def _evict(self):
        store = self.store
        while True:
            if self.ns >= self.scap or self.nm == 0:
                k = self.S.popleft()
                if store[k] > 0:
                    store[k] = 0; self.M.append(k); self.ns -= 1; self.nm += 1
                    if self.nm > self.cap - self.scap and self.nm > 0:
                        self._evict_m()
                        return
                else:
                    del store[k]; self.ev.append(k); self.ns -= 1
                    self.G[k] = None; self.ghost.append(k)
                    if len(self.ghost) > self.cap:
                        g = self.ghost.popleft(); self.G.pop(g, None)
                    return
            else:
                self._evict_m(); return

    def _evict_m(self):
        store = self.store
        while True:
            k = self.M.popleft()
            if store[k] > 0:
                store[k] -= 1; self.M.append(k)
            else:
                del store[k]; self.ev.append(k); self.nm -= 1; return

    def access(self, key):
        store = self.store
        if key in store:
            if store[key] < 3:
                store[key] += 1
            return True
        if len(store) >= self.cap:
            self._evict()
        store[key] = 0
        if key in self.G:
            del self.G[key]; self.M.append(key); self.nm += 1
        else:
            self.S.append(key); self.ns += 1
        return False



class LFUDA:
    """LFU with dynamic aging (heap, lazy deletion), freq remembered for ghosts."""

    def __init__(self, capacity):
        self.cap = capacity; self.store = {}; self.ev = []; self.h = []; self.L = 0.0; self.t = 0; self.cnt = {}

    def access(self, key):
        self.t += 1
        c = self.cnt.get(key, 0) + 1
        self.cnt[key] = c
        if key in self.store:
            pr = self.L + c
            self.store[key] = pr
            heapq.heappush(self.h, (pr, self.t, key))
            return True
        if len(self.store) >= self.cap:
            while True:
                pr, t, k = heapq.heappop(self.h)
                if self.store.get(k) == pr:
                    break
            del self.store[k]; self.ev.append(k); self.L = pr
        pr = self.L + c
        self.store[key] = pr
        heapq.heappush(self.h, (pr, self.t, key))
        if len(self.h) > 8 * self.cap:
            self.h = [(p, 0, k) for k, p in self.store.items()]; heapq.heapify(self.h)
        if len(self.cnt) > 20 * self.cap:
            self.cnt = {k: v >> 1 for k, v in self.cnt.items() if v > 1}
        return False


class Pred:
    """Approximate Belady: evict the sampled key whose predicted next use is farthest."""

    def __init__(self, capacity, newc=2.0, alpha=0.5, samples=24, over=1.0, seed=1):
        self.cap = capacity
        self.store = {}; self.ev = []
        self.keys = []
        self.last = {}
        self.est = {}
        self.t = 0
        self.samples = samples; self.alpha = alpha; self.newc = newc * capacity; self.over = over
        self.rng = random.Random(seed)

    def _pred(self, k, now):
        e = self.est.get(k)
        last = self.last[k]
        if e is None:
            e = self.newc
        age = now - last
        if age > e:
            return now + age * self.over
        return last + e

    def access(self, key):
        self.t += 1; now = self.t
        last = self.last.get(key)
        if last is not None:
            iv = now - last
            e = self.est.get(key)
            self.est[key] = iv if e is None else e + self.alpha * (iv - e)
        self.last[key] = now
        store = self.store
        if key in store:
            return True
        if len(store) < self.cap:
            store[key] = len(self.keys); self.keys.append(key)
            return False
        keys = self.keys; n = len(keys); rnd = self.rng.random; pred = self._pred
        worst = None; wp = -1
        for _ in range(self.samples):
            k = keys[int(rnd() * n)]
            p = pred(k, now)
            if p > wp:
                wp = p; worst = k
        e = self.est.get(key, self.newc)
        if now + e >= wp:
            return False
        i = store.pop(worst); self.ev.append(worst)
        keys[i] = key; store[key] = i
        return False


class TL:
    def __init__(self, cap, frac, shared, k):
        self.seg = Seg(cap, max(1, min(cap - 1, int(cap * frac))), 0.8, k)
        self.store = self.seg.store; self.ev = self.seg.ev; self.sh = shared

    def access(self, key):
        return self.seg.access(key, self.sh[0])


class Cache:
    """Holds what the recently best of several policies holds."""

    def __init__(self, capacity, fracs=(0.01, 0.1, 0.3, 0.6, 0.95), extra=("arc", "s3", "lfu"), preds=((2, 0.5, 12, 4), (20, 0.5, 12, 4)),
                 slow=(), horizon=30.0, reset=10, k=8, sreset=0, smax=255):
        self.cap = capacity
        self.sh = [{}]; self.sl = [{}]
        self.ops = 0; self.reset = reset * capacity
        self.sops = 0; self.sreset = sreset * capacity; self.smax = smax
        ex = [TL(capacity, x, self.sh, k) for x in fracs]
        ex += [TL(capacity, x, self.sl, k) for x in slow]
        for e in extra:
            ex.append({"arc": ARC, "s3": S3, "lfu": LFUDA}[e](capacity))
        for c in preds:
            ex.append(Pred(capacity, *c))
        self.ex = ex
        self.sc = [0.0] * len(ex)
        self.decay = 1.0 - 1.0 / (horizon * capacity)
        self.lead = 0
        self.store = {}
        self.extra = {}

    def access(self, key):
        f = self.sh[0]
        f[key] = min(15, f.get(key, 0) + 1)
        self.ops += 1
        if self.ops >= self.reset:
            self.ops = 0
            self.sh[0] = {k: v >> 1 for k, v in f.items() if v > 1}
        if self.sreset:
            f = self.sl[0]
            f[key] = min(self.smax, f.get(key, 0) + 1)
            self.sops += 1
            if self.sops >= self.sreset:
                self.sops = 0
                self.sl[0] = {k: v >> 1 for k, v in f.items() if v > 1}
        d = self.decay; sc = self.sc
        best = self.lead
        for i, e in enumerate(self.ex):
            sc[i] = sc[i] * d + e.access(key)
            if sc[i] > sc[best]:
                best = i
        store = self.store; extra = self.extra
        ls = self.ex[best].store
        if best != self.lead:
            self.lead = best
            self.extra = extra = {k: None for k in store if k not in ls}
            for e in self.ex:
                e.ev.clear()
        else:
            for e in self.ex:
                if e.ev:
                    if e.store is ls:
                        for k in e.ev:
                            if k in store:
                                extra[k] = None
                    e.ev.clear()
            extra.pop(key, None)
        if key in store:
            if key not in ls:
                extra[key] = None
            return True
        if key in ls:
            if len(store) >= self.cap:
                v = next(iter(extra))
                del extra[v]; del store[v]
            store[key] = None
        elif len(store) < self.cap:
            store[key] = None; extra[key] = None
        return False
