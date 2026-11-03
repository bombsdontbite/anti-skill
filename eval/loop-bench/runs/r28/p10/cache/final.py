from collections import OrderedDict, deque


class LogSet(set):
    def discard(self, k):
        if k in self:
            set.discard(self, k)
            self.log.append(k)


class TLFU:
    """W-TinyLFU with a fixed window; optionally the window adapts from ghost hits."""

    def __init__(self, capacity, window_frac, ghost=0.0, gstep=0.3, prot_frac=0.8, reset_mult=10):
        self.capacity = capacity
        self.store = LogSet()
        self.store.log = deque()
        self.wf = max(1.0, capacity * window_frac)
        self.wcap = int(self.wf)
        self.prot_frac = prot_frac
        self.window, self.prob, self.prot = OrderedDict(), OrderedDict(), OrderedDict()
        self.freq = {}
        self.ops = 0
        self.reset_at = reset_mult * capacity
        self.gw, self.gm = OrderedDict(), OrderedDict()
        self.glen = int(capacity * ghost)
        self.gstep = gstep

    def _ghost(self, g, k):
        if self.glen:
            g[k] = True
            if len(g) > self.glen:
                g.popitem(last=False)

    def _resize(self, d):
        cap = self.capacity
        self.wf = min(cap - 1.0, max(1.0, self.wf + d))
        self.wcap = int(self.wf)
        main = cap - self.wcap
        while len(self.window) > self.wcap:
            k, _ = self.window.popitem(last=False)
            self.prob[k] = True
        while len(self.prob) + len(self.prot) > main:
            src = self.prob if self.prob else self.prot
            k, _ = src.popitem(last=False)
            self.window[k] = True
            self.window.move_to_end(k, last=False)
        pcap = int(main * self.prot_frac)
        while len(self.prot) > pcap:
            k, _ = self.prot.popitem(last=False)
            self.prob[k] = True

    def access(self, key):
        f = self.freq
        f[key] = f.get(key, 0) + 1
        self.ops += 1
        if self.ops >= self.reset_at:
            self.ops = 0
            self.freq = f = {k: v >> 1 for k, v in f.items() if v > 1}
        if key in self.window:
            self.window.move_to_end(key)
            return True
        if key in self.prot:
            self.prot.move_to_end(key)
            return True
        if key in self.prob:
            del self.prob[key]
            self.prot[key] = True
            if len(self.prot) > int((self.capacity - self.wcap) * self.prot_frac):
                k, _ = self.prot.popitem(last=False)
                self.prob[k] = True
            return True
        if self.glen:
            if key in self.gw:
                del self.gw[key]
                self._resize(self.gstep * max(1.0, len(self.gm) / max(1, len(self.gw))))
            elif key in self.gm:
                del self.gm[key]
                self._resize(-self.gstep * max(1.0, len(self.gw) / max(1, len(self.gm))))
        self.window[key] = True
        self.store.add(key)
        if len(self.window) > self.wcap:
            cand, _ = self.window.popitem(last=False)
            if len(self.prob) + len(self.prot) < self.capacity - self.wcap:
                self.prob[cand] = True
            else:
                victim = next(iter(self.prob)) if self.prob else next(iter(self.prot))
                if f.get(cand, 0) > f.get(victim, 0):
                    if victim in self.prob:
                        del self.prob[victim]
                    else:
                        del self.prot[victim]
                    self.store.discard(victim)
                    self.prob[cand] = True
                    self._ghost(self.gm, victim)
                else:
                    self.store.discard(cand)
                    self._ghost(self.gw, cand)
        return False


class ARC:
    def __init__(self, capacity):
        self.c = capacity
        self.p = 0
        self.t1, self.t2, self.b1, self.b2 = OrderedDict(), OrderedDict(), OrderedDict(), OrderedDict()
        self.store = LogSet()
        self.store.log = deque()

    def _replace(self, in_b2):
        if self.t1 and (len(self.t1) > self.p or (in_b2 and len(self.t1) == self.p)):
            k, _ = self.t1.popitem(last=False)
            self.b1[k] = True
        else:
            k, _ = self.t2.popitem(last=False)
            self.b2[k] = True
        self.store.discard(k)

    def access(self, key):
        c = self.c
        if key in self.t1:
            del self.t1[key]
            self.t2[key] = True
            return True
        if key in self.t2:
            self.t2.move_to_end(key)
            return True
        if key in self.b1:
            self.p = min(c, self.p + max(len(self.b2) // len(self.b1), 1))
            self._replace(False)
            del self.b1[key]
            self.t2[key] = True
            self.store.add(key)
            return False
        if key in self.b2:
            self.p = max(0, self.p - max(len(self.b1) // len(self.b2), 1))
            self._replace(True)
            del self.b2[key]
            self.t2[key] = True
            self.store.add(key)
            return False
        l1 = len(self.t1) + len(self.b1)
        if l1 == c:
            if len(self.t1) < c:
                self.b1.popitem(last=False)
                self._replace(False)
            else:
                k, _ = self.t1.popitem(last=False)
                self.store.discard(k)
        elif l1 < c and l1 + len(self.t2) + len(self.b2) >= c:
            if l1 + len(self.t2) + len(self.b2) == 2 * c:
                self.b2.popitem(last=False)
            self._replace(False)
        self.t1[key] = True
        self.store.add(key)
        return False


class LIRS:
    def __init__(self, capacity, hir_frac=0.01, nonres_mult=2):
        self.cap = capacity
        self.lhirs = max(1, int(capacity * hir_frac))
        self.llirs = capacity - self.lhirs
        self.S = OrderedDict()
        self.Q = OrderedDict()
        self.lir = set()
        self.store = LogSet()
        self.store.log = deque()
        self.nonres = 0
        self.nmax = nonres_mult * capacity

    def _prune(self):
        S = self.S
        while S:
            k = next(iter(S))
            if k in self.lir:
                return
            del S[k]
            if k not in self.store:
                self.nonres -= 1

    def _demote_bottom(self):
        k, _ = self.S.popitem(last=False)
        self.lir.discard(k)
        self.Q[k] = True
        self._prune()

    def _bound(self):
        if self.nonres > self.nmax:
            for k in list(self.S):
                if k not in self.store and k not in self.lir:
                    del self.S[k]
                    self.nonres -= 1
                    if self.nonres <= self.nmax // 2:
                        break

    def access(self, key):
        S = self.S
        st = self.store
        if key in self.lir:
            S.move_to_end(key)
            self._prune()
            return True
        if key in st:
            if key in S:
                S.move_to_end(key)
                del self.Q[key]
                self.lir.add(key)
                self._demote_bottom()
            else:
                S[key] = True
                self.Q.move_to_end(key)
            return True
        if len(st) >= self.cap:
            k, _ = self.Q.popitem(last=False)
            st.discard(k)
            if k in S:
                self.nonres += 1
        st.add(key)
        if len(self.lir) < self.llirs:
            if key in S:
                self.nonres -= 1
            S[key] = True
            S.move_to_end(key)
            self.lir.add(key)
        elif key in S:
            self.nonres -= 1
            S.move_to_end(key)
            self.lir.add(key)
            self._demote_bottom()
        else:
            S[key] = True
            self.Q[key] = True
        self._bound()
        return False


class Cache:
    """Runs several policies as shadows and evicts what the recently best one has evicted."""

    def __init__(self, capacity, horizon=4.0, margin=0.1):
        self.capacity = capacity
        self.store = OrderedDict()
        self.experts = [TLFU(capacity, 0.01), TLFU(capacity, 0.01, 0.1), ARC(capacity),
                        TLFU(capacity, 0.01, reset_mult=100), LIRS(capacity, 0.01, 10)]
        self.score = [0.0] * len(self.experts)
        self.decay = 1.0 - 1.0 / (horizon * capacity)
        self.margin = margin
        self.lead = 0

    def access(self, key):
        if self.capacity < 16:
            st = self.store
            if key in st:
                st.move_to_end(key)
                return True
            if len(st) >= self.capacity:
                st.popitem(last=False)
            st[key] = True
            return False
        d = self.decay
        sc = self.score
        for i, e in enumerate(self.experts):
            sc[i] = sc[i] * d + (1.0 if e.access(key) else 0.0)
            if len(e.store.log) > 4 * self.capacity:
                for _ in range(2 * self.capacity):
                    e.store.log.popleft()
        best = self.lead
        for i in range(len(sc)):
            if sc[i] > sc[best] * (1.0 + self.margin) + 1.0:
                best = i
        self.lead = best
        st = self.store
        if key in st:
            st.move_to_end(key)
            return True
        if len(st) >= self.capacity:
            ls = self.experts[best].store
            log = ls.log
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
            del st[victim]
        st[key] = True
        return False
