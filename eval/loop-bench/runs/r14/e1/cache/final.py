import heapq
from collections import OrderedDict, deque




class LIRS:
    def __init__(self, capacity, hir, ghost):
        self.cap = capacity
        self.S = OrderedDict()   # 0 LIR, 1 resident HIR, 2 non-resident HIR
        self.Q = OrderedDict()
        self.lir = 0
        self.nonres = 0
        self.gmax = int(ghost * capacity)
        self.store = set(); self.ev = deque(maxlen=2 * capacity)
        self.resize(hir)

    def resize(self, hir):
        self.hcap = max(1, int(self.cap * hir))
        self.lcap = self.cap - self.hcap

    def _prune(self):
        S = self.S
        while S:
            k = next(iter(S))
            st = S[k]
            if st == 0: break
            del S[k]
            if st == 2: self.nonres -= 1

    def _demote(self):
        k, _ = self.S.popitem(last=False)
        self.lir -= 1
        self.Q[k] = True
        self._prune()

    def access(self, k):
        S = self.S; Q = self.Q
        if k in self.store:
            if S.get(k) == 0:
                S.move_to_end(k); self._prune(); return True
            if k in S:
                del S[k]; S[k] = 0; self.lir += 1; del Q[k]
                self._demote()
            else:
                S[k] = 1; Q.move_to_end(k)
            while self.lir > self.lcap: self._demote()
            return True
        if len(self.store) >= self.cap:
            v, _ = Q.popitem(last=False)
            self.store.discard(v); self.ev.append(v)
            if v in S: S[v] = 2; self.nonres += 1
        self.store.add(k)
        if self.lir < self.lcap:
            if S.pop(k, None) == 2: self.nonres -= 1
            S[k] = 0; self.lir += 1
        elif S.get(k) == 2:
            del S[k]; self.nonres -= 1; S[k] = 0; self.lir += 1
            self._demote()
        else:
            S[k] = 1; Q[k] = True
        while self.lir > self.lcap: self._demote()
        if self.nonres > self.gmax:
            for g in list(S):
                if S[g] == 2:
                    del S[g]; self.nonres -= 1
                    if self.nonres <= self.gmax // 2: break
        return False



class TinyLFU:
    """W-TinyLFU: 1% LRU window, SLRU main, frequency sketch admission."""

    def __init__(self, capacity, win=0.01, prot=0.8, reset=10, fmax=15):
        self.cap = capacity; self.fmax = fmax
        self.wcap = max(1, int(capacity * win))
        self.mcap = capacity - self.wcap
        self.pcap = int(self.mcap * prot)
        self.win = OrderedDict(); self.prob = OrderedDict(); self.prot = OrderedDict()
        self.freq = {}
        self.ops = 0; self.reset = reset * capacity
        self.store = set(); self.ev = deque(maxlen=2 * capacity)

    def _inc(self, k):
        f = self.freq
        f[k] = min(f.get(k, 0) + 1, self.fmax)
        self.ops += 1
        if self.ops >= self.reset:
            self.ops = 0
            self.freq = {a: b >> 1 for a, b in f.items() if b > 1}

    def access(self, k):
        self._inc(k)
        if k in self.win:
            self.win.move_to_end(k); return True
        if k in self.prot:
            self.prot.move_to_end(k); return True
        if k in self.prob:
            del self.prob[k]; self.prot[k] = True
            if len(self.prot) > self.pcap:
                d, _ = self.prot.popitem(last=False); self.prob[d] = True
            return True
        self.store.add(k); self.win[k] = True
        if len(self.win) > self.wcap:
            cand, _ = self.win.popitem(last=False)
            if len(self.prob) + len(self.prot) < self.mcap:
                self.prob[cand] = True
            else:
                vic = next(iter(self.prob)) if self.prob else next(iter(self.prot))
                f = self.freq
                if f.get(cand, 0) > f.get(vic, 0):
                    if vic in self.prob: del self.prob[vic]
                    else: del self.prot[vic]
                    self.store.discard(vic); self.ev.append(vic); self.prob[cand] = True
                else:
                    self.store.discard(cand); self.ev.append(cand)
        return False


class ARC:
    """ARC."""

    def __init__(self, capacity):
        self.c = capacity
        self.p = 0
        self.t1 = OrderedDict(); self.t2 = OrderedDict()
        self.b1 = OrderedDict(); self.b2 = OrderedDict()
        self.store = set(); self.ev = deque(maxlen=2 * capacity)

    def _replace(self, in_b2):
        if self.t1 and (len(self.t1) > self.p or (in_b2 and len(self.t1) == self.p)):
            k, _ = self.t1.popitem(last=False); self.b1[k] = True
        else:
            k, _ = self.t2.popitem(last=False); self.b2[k] = True
        self.store.discard(k); self.ev.append(k)

    def access(self, x):
        c = self.c
        if x in self.t1:
            del self.t1[x]; self.t2[x] = True; return True
        if x in self.t2:
            self.t2.move_to_end(x); return True
        if x in self.b1:
            self.p = min(c, self.p + max(len(self.b2) // len(self.b1), 1))
            self._replace(False); del self.b1[x]; self.t2[x] = True; self.store.add(x); return False
        if x in self.b2:
            self.p = max(0, self.p - max(len(self.b1) // len(self.b2), 1))
            self._replace(True); del self.b2[x]; self.t2[x] = True; self.store.add(x); return False
        l1 = len(self.t1) + len(self.b1)
        if l1 == c:
            if len(self.t1) < c:
                self.b1.popitem(last=False); self._replace(False)
            else:
                k, _ = self.t1.popitem(last=False); self.store.discard(k); self.ev.append(k)
        elif l1 < c:
            tot = l1 + len(self.t2) + len(self.b2)
            if tot >= c:
                if tot == 2 * c: self.b2.popitem(last=False)
                self._replace(False)
        self.t1[x] = True; self.store.add(x); return False


class PNA:
    """Evict the key whose predicted next access is furthest; keys far overdue go first."""

    def __init__(self, capacity, alpha=0.5, prior=4.0, overdue=3.0, hist=8.0):
        self.cap = capacity
        self.alpha = alpha; self.prior = prior * capacity; self.overdue = overdue
        self.last = OrderedDict()  # key -> last access time, recency order, includes ghosts
        self.est = {}
        self.hmax = int(hist * capacity)
        self.heap = []
        self.pri = {}
        self.t = 0
        self.store = OrderedDict(); self.ev = deque(maxlen=2 * capacity)

    def access(self, k):
        t = self.t = self.t + 1
        last = self.last; est = self.est
        lt = last.pop(k, None)
        if lt is not None:
            iv = t - lt
            e = est.get(k)
            est[k] = iv if e is None else e + self.alpha * (iv - e)
        last[k] = t
        if len(last) > self.hmax:
            g, _ = last.popitem(last=False)
            est.pop(g, None)
        e = est.get(k)
        p = t + (e if e is not None else self.prior)
        st = self.store
        if k in st:
            st[k] = t; st.move_to_end(k)
            self.pri[k] = p; heapq.heappush(self.heap, (-p, k)); return True
        if len(st) >= self.cap:
            v = None
            for x, lx in st.items():
                if t - lx > self.overdue * est.get(x, self.prior): v = x
                break
            if v is None:
                h = self.heap; pri = self.pri
                while True:
                    np_, x = h[0]
                    if pri.get(x) == -np_ and x in st: break
                    heapq.heappop(h)
                if -h[0][0] <= p: return False
                v = x
            del st[v]; del self.pri[v]; self.ev.append(v)
        st[k] = t; self.pri[k] = p; heapq.heappush(self.heap, (-p, k))
        return False


class Cache:
    """Runs several policies as shadows and copies the evictions of whichever has the most recent hits."""

    def __init__(self, capacity, decay=0.9999, margin=1.005):
        self.sh = [LIRS(capacity, h, 4.0) for h in (0.01, 0.1, 0.4)]
        self.sh += [TinyLFU(capacity), ARC(capacity), PNA(capacity)]
        self.cap = capacity
        self.sc = [0.0] * len(self.sh)
        self.decay = decay; self.margin = margin
        self.every = max(1, capacity // 4); self.n = 0
        self.cur = 0
        self.store = OrderedDict()

    def access(self, k):
        sc = self.sc; d = self.decay
        for i, s in enumerate(self.sh):
            sc[i] = sc[i] * d + s.access(k)
        self.n += 1
        if self.n >= self.every:
            self.n = 0
            b = self.cur
            for i, v in enumerate(sc):
                if v > sc[b] * self.margin: b = i
            self.cur = b
        st = self.store
        if k in st:
            return True
        lead = self.sh[self.cur]
        if len(st) >= self.cap:
            if k not in lead.store: return False
            ev = lead.ev; ls = lead.store
            v = None
            while ev:
                x = ev.popleft()
                if x in st and x not in ls: v = x; break
            if v is None:
                for x in st:
                    if x not in ls: v = x; break
            if v is None: v = next(iter(st))
            del st[v]
        st[k] = True
        return False
