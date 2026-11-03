from collections import OrderedDict


class LIRS:
    HFRAC = 0.05
    NR = 2.0
    def __init__(self, capacity):
        self.c = capacity
        self.hmax = max(1, int(capacity * self.HFRAC))
        self.lmax = capacity - self.hmax
        self.S = OrderedDict()   # key -> 0 LIR, 1 resident HIR, 2 nonresident
        self.Q = OrderedDict()
        self.nlir = 0
        self.nnr = 0
        self.nrq = OrderedDict()
        self.store = set()

    def _prune(self):
        S = self.S
        while S:
            k = next(iter(S))
            st = S[k]
            if st == 0: break
            del S[k]
            if st == 2: self.nnr -= 1

    def _demote_bottom(self):
        S = self.S
        k = next(iter(S))
        del S[k]
        self.nlir -= 1
        self.Q[k] = True
        self.S_hir_add = k
        self._prune()
        return k

    def access(self, x):
        S, Q = self.S, self.Q
        st = S.get(x)
        if st == 0:
            S.move_to_end(x)
            self._prune()
            return True
        if x in Q:
            if st is not None:
                S[x] = 0; self.nlir += 1
                del Q[x]
                S.move_to_end(x)
                self._demote_bottom()
            else:
                S[x] = 1
                Q.move_to_end(x)
            return True
        # miss
        if len(self.store) >= self.c:
            k, _ = Q.popitem(last=False)
            self.store.discard(k)
            if k in S:
                S[k] = 2; self.nnr += 1
                self.nrq.pop(k, None); self.nrq[k] = True
        self.store.add(x)
        if st == 2:
            self.nnr -= 1
            S[x] = 0; self.nlir += 1
            S.move_to_end(x)
            self._demote_bottom()
        elif self.nlir < self.lmax:
            S[x] = 0; self.nlir += 1
        else:
            S[x] = 1
            Q[x] = True
        if self.nnr > self.NR * self.c:
            nrq = self.nrq
            while nrq:
                k, _ = nrq.popitem(last=False)
                if S.get(k) == 2:
                    del S[k]; self.nnr -= 1; break
        if len(self.nrq) > 4 * self.c:
            self.nrq = OrderedDict((k, True) for k in self.nrq if S.get(k) == 2)
        return False


class LIRS2(LIRS):
    HFRAC = 0.02


class LIRS15(LIRS):
    HFRAC = 0.15



class ARC:
    def __init__(self, capacity):
        self.c = capacity
        self.p = 0
        self.t1 = OrderedDict(); self.t2 = OrderedDict()
        self.b1 = OrderedDict(); self.b2 = OrderedDict()
        self.store = set()

    def _replace(self, in_b2):
        t1, t2 = self.t1, self.t2
        if t1 and (len(t1) > self.p or (in_b2 and len(t1) == self.p)):
            k, _ = t1.popitem(last=False); self.b1[k] = True
        else:
            k, _ = t2.popitem(last=False); self.b2[k] = True
        self.store.discard(k)

    def access(self, key):
        c = self.c
        if key in self.t1:
            del self.t1[key]; self.t2[key] = True; return True
        if key in self.t2:
            self.t2.move_to_end(key); return True
        if key in self.b1:
            self.p = min(c, self.p + max(1, len(self.b2) // max(1, len(self.b1))))
            del self.b1[key]
            self._replace(False)
            self.t2[key] = True; self.store.add(key); return False
        if key in self.b2:
            self.p = max(0, self.p - max(1, len(self.b1) // max(1, len(self.b2))))
            del self.b2[key]
            self._replace(True)
            self.t2[key] = True; self.store.add(key); return False
        l1 = len(self.t1) + len(self.b1)
        if l1 == c:
            if len(self.t1) < c:
                self.b1.popitem(last=False); self._replace(False)
            else:
                k, _ = self.t1.popitem(last=False); self.store.discard(k)
        else:
            tot = l1 + len(self.t2) + len(self.b2)
            if tot >= c:
                if tot >= 2 * c: self.b2.popitem(last=False)
                if len(self.t1) + len(self.t2) >= c: self._replace(False)
        self.t1[key] = True; self.store.add(key); return False



class WT:
    WFRAC = 0.01
    PFRAC = 0.8
    AGE = 10
    def __init__(self, capacity):
        self.c = capacity
        self.w = max(1, int(capacity * self.WFRAC))
        self.pmax = int((capacity - self.w) * self.PFRAC)
        self.win = OrderedDict(); self.prob = OrderedDict(); self.prot = OrderedDict()
        self.f = {}
        self.n = 0
        self.lim = self.AGE * capacity
        self.store = set()

    def access(self, key):
        f = self.f
        f[key] = f.get(key, 0) + 1
        self.n += 1
        if self.n >= self.lim:
            self.n = 0
            self.f = f = {k: v >> 1 for k, v in f.items() if v > 1}
        win, prob, prot = self.win, self.prob, self.prot
        if key in prot:
            prot.move_to_end(key); return True
        if key in prob:
            del prob[key]; prot[key] = True
            if len(prot) > self.pmax:
                k, _ = prot.popitem(last=False); prob[k] = True
            return True
        if key in win:
            win.move_to_end(key); return True
        win[key] = True; self.store.add(key)
        if len(win) > self.w:
            cand, _ = win.popitem(last=False)
            if len(prob) + len(prot) < self.c - self.w:
                prob[cand] = True
            else:
                vic_src = prob if prob else prot
                vic = next(iter(vic_src))
                if f.get(cand, 0) > f.get(vic, 0):
                    del vic_src[vic]; self.store.discard(vic)
                    prob[cand] = True
                else:
                    self.store.discard(cand)
        return False


class Cache:
    DECAY = 0.9999

    def __init__(self, capacity):
        self.c = capacity
        self.ex = [LIRS2(capacity), ARC(capacity), WT(capacity)]
        self.sc = [0.0] * len(self.ex)
        self.lead = 0
        self.stamp = {}
        self.t = 0
        self.store = set()

    def access(self, key):
        ex = self.ex
        sc = self.sc
        d = self.DECAY
        for i in range(len(ex)):
            sc[i] = sc[i] * d + (1.0 if ex[i].access(key) else 0.0)
        self.t += 1
        if not self.t & 15:
            best = max(range(len(ex)), key=lambda i: sc[i])
            if sc[best] > sc[self.lead]:
                self.lead = best
        store = self.store
        stamp = self.stamp
        stamp[key] = self.t
        if key in store:
            return True
        store.add(key)
        if len(store) > self.c:
            diff = store - ex[self.lead].store
            k = min(diff, key=stamp.get)
            store.discard(k)
            del stamp[k]
        return False
