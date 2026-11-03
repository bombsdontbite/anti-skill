from collections import OrderedDict




class LIRS:
    """LIRS with a hill-climbed HIR (resident cold) share."""

    def __init__(self, capacity, hfrac=0.01, nonres=5.0, period=10, step=0.03):
        self.cap = capacity
        self.hmax = max(1, int(capacity * hfrac))
        self.S = OrderedDict()
        self.Q = OrderedDict()
        self.lir = set()
        self.store = {}
        self.ev = []
        self.maxs = int(capacity * (1 + nonres))
        self.period = int(period * capacity)
        self.step = max(1, int(capacity * step)) if step else 0
        self.dir = 1
        self.n = self.hits = 0
        self.prev = -1.0

    def _prune(self):
        S, lir = self.S, self.lir
        while S:
            k = next(iter(S))
            if k in lir:
                break
            del S[k]

    def _demote(self):
        lmax = self.cap - self.hmax
        while len(self.lir) > lmax:
            k, _ = self.S.popitem(last=False)
            self.lir.discard(k)
            self.Q[k] = 1
            self._prune()

    def _climb(self):
        rate = self.hits / self.n
        if rate < self.prev:
            self.dir = -self.dir
        self.prev = rate
        self.n = self.hits = 0
        self.hmax = min(self.cap - 1, max(1, self.hmax + self.dir * self.step))
        self._demote()

    def access(self, key):
        hit = self._access(key)
        self.hits += hit
        self.n += 1
        if self.n >= self.period:
            self._climb()
        return hit

    def _access(self, key):
        S, Q, lir = self.S, self.Q, self.lir
        if key in lir:
            first = next(iter(S)) == key
            S.move_to_end(key)
            if first:
                self._prune()
            return True
        if key in self.store:
            if key in S:
                del Q[key]
                S.move_to_end(key)
                lir.add(key)
                self._demote()
            else:
                S[key] = False
                Q.move_to_end(key)
            return True
        if len(lir) < self.cap - self.hmax and not Q:
            lir.add(key)
            S[key] = True
            self.store[key] = 1
            return False
        if len(self.store) >= self.cap:
            if Q:
                k, _ = Q.popitem(last=False)
            else:
                k, _ = S.popitem(last=False)
                lir.discard(k)
                self._prune()
            del self.store[k]
            self.ev.append(k)
        self.store[key] = 1
        if key in S:
            S.move_to_end(key)
            lir.add(key)
            self._demote()
        else:
            S[key] = False
            Q[key] = 1
            if len(S) > self.maxs:
                st = self.store
                for k in S:
                    if k not in lir and k not in st:
                        del S[k]
                        break
        return False




class AWT:
    """W-TinyLFU with a hill-climbed window size."""

    def __init__(self, capacity, wfrac=0.01, period=None, step=0.0625, reset=10, maxf=15, margin=0, sdecay=1.0, restart=0.05):
        self.cap = capacity
        self.maxf = maxf
        self.margin = margin
        self.w = max(1, int(capacity * wfrac))
        self.win = OrderedDict()
        self.prob = OrderedDict()
        self.prot = OrderedDict()
        self.store = {}
        self.ev = []
        self.freq = {}
        self.door = set()
        self.ops = 0
        self.reset = reset * capacity
        self.period = period or 10 * capacity
        self.step = max(1, int(capacity * step)) if step else 0
        self.dir = 1
        self.sdecay = sdecay
        self.restart = restart
        self.step0 = self.fstep = self.step
        self.fw = float(self.w)
        self.n = 0
        self.hits = 0
        self.prev = -1.0

    def _inc(self, k):
        if k in self.door:
            v = self.freq.get(k, 0)
            if v < self.maxf:
                self.freq[k] = v + 1
        else:
            self.door.add(k)
        self.ops += 1
        if self.ops >= self.reset:
            self.ops = 0
            self.door = set()
            self.freq = {k: v >> 1 for k, v in self.freq.items() if v > 1}

    def _est(self, k):
        return self.freq.get(k, 0) + (k in self.door)

    def _climb(self):
        rate = self.hits / self.n
        delta = rate - self.prev
        amt = self.fstep if delta >= 0 else -self.fstep
        if abs(delta) >= self.restart:
            self.fstep = self.step0 * (1 if amt >= 0 else -1)
        else:
            self.fstep = amt * self.sdecay
        self.prev = rate
        self.n = self.hits = 0
        self.fw = min(self.cap - 1.0, max(1.0, self.fw + amt))
        self.w = int(self.fw)
        while len(self.win) > self.w:
            k, _ = self.win.popitem(last=False)
            self.prob[k] = 1
        self._fit_main()

    def _fit_main(self):
        mmax = self.cap - self.w
        while len(self.prob) + len(self.prot) > mmax:
            src = self.prob if self.prob else self.prot
            k, _ = src.popitem(last=False)
            self.store.pop(k); self.ev.append(k)
        pmax = int(mmax * 0.8)
        while len(self.prot) > pmax:
            k, _ = self.prot.popitem(last=False)
            self.prob[k] = 1

    def access(self, key):
        self._inc(key)
        hit = True
        if key in self.win:
            self.win.move_to_end(key)
        elif key in self.prob:
            del self.prob[key]
            self.prot[key] = 1
            if len(self.prot) > int((self.cap - self.w) * 0.8):
                k, _ = self.prot.popitem(last=False)
                self.prob[k] = 1
        elif key in self.prot:
            self.prot.move_to_end(key)
        else:
            hit = False
            self.win[key] = 1
            self.store[key] = 1
            if len(self.win) > self.w:
                cand, _ = self.win.popitem(last=False)
                if len(self.prob) + len(self.prot) < self.cap - self.w:
                    self.prob[cand] = 1
                else:
                    src = self.prob if self.prob else self.prot
                    vic = next(iter(src))
                    if self._est(cand) > self._est(vic) + self.margin:
                        del src[vic]
                        self.store.pop(vic); self.ev.append(vic)
                        self.prob[cand] = 1
                    else:
                        self.store.pop(cand); self.ev.append(cand)
        if hit:
            self.hits += 1
        self.n += 1
        if self.n >= self.period:
            self._climb()
        return hit


class ARC:
    def __init__(self, capacity):
        self.c=capacity; self.p=0
        self.t1=OrderedDict(); self.t2=OrderedDict(); self.b1=OrderedDict(); self.b2=OrderedDict()
        self.store={}; self.ev=[]
    def _rep(self, inb2):
        if self.t1 and (len(self.t1)>self.p or (inb2 and len(self.t1)==self.p)):
            k,_=self.t1.popitem(last=False); self.b1[k]=1
        else:
            k,_=self.t2.popitem(last=False); self.b2[k]=1
        self.store.pop(k); self.ev.append(k)
    def access(self, key):
        c=self.c
        if key in self.t1:
            del self.t1[key]; self.t2[key]=1; return True
        if key in self.t2:
            self.t2.move_to_end(key); return True
        if key in self.b1:
            self.p=min(c,self.p+max(1,len(self.b2)//len(self.b1)))
            self._rep(False); del self.b1[key]; self.t2[key]=1; self.store[key]=1; return False
        if key in self.b2:
            self.p=max(0,self.p-max(1,len(self.b1)//len(self.b2)))
            self._rep(True); del self.b2[key]; self.t2[key]=1; self.store[key]=1; return False
        l1=len(self.t1)+len(self.b1)
        if l1==c:
            if len(self.t1)<c:
                self.b1.popitem(last=False); self._rep(False)
            else:
                k,_=self.t1.popitem(last=False); self.store.pop(k); self.ev.append(k)
        elif l1<c and l1+len(self.t2)+len(self.b2)>=c:
            if l1+len(self.t2)+len(self.b2)==2*c: self.b2.popitem(last=False)
            self._rep(False)
        self.t1[key]=1; self.store[key]=1; return False




class LRU:
    def __init__(self, capacity):
        self.cap = capacity
        self.store = OrderedDict()
        self.ev = []

    def access(self, key):
        if key in self.store:
            self.store.move_to_end(key)
            return True
        if len(self.store) >= self.cap:
            k, _ = self.store.popitem(last=False)
            self.ev.append(k)
        self.store[key] = 1
        return False


class Cache:
    def __init__(self, capacity, decay=None, cfg=None, hyst=1.01):
        self.cap = capacity
        cfg = cfg or [('l', dict(step=0)), ('r', {}), ('u', {})]
        self.ex = [{'a': AWT, 'r': ARC, 'l': LIRS, 'u': LRU}[t](capacity, **kw) for t, kw in cfg]
        self.sc = [0.0] * len(self.ex)
        self.decay = decay or (1 - 1 / (2 * capacity))
        self.lead = 0
        self.hyst = hyst
        self.store = OrderedDict()
        self.diff = {}

    def access(self, key):
        store = self.store
        hit = key in store
        d = self.decay
        sc = self.sc
        for i, e in enumerate(self.ex):
            e.ev = []
            sc[i] = sc[i] * d + e.access(key)
        best = max(range(len(sc)), key=lambda i: sc[i])
        if sc[best] > sc[self.lead] * self.hyst:
            self.lead = best
            ls = self.ex[best].store
            self.diff = {k: 1 for k in store if k not in ls}
        lead = self.ex[self.lead]
        diff = self.diff
        for k in lead.ev:
            if k in store:
                diff[k] = 1
        if hit:
            store.move_to_end(key)
            if key in lead.store:
                diff.pop(key, None)
            return True
        store[key] = 1
        if key not in lead.store:
            diff[key] = 1
        if len(store) > self.cap:
            ls = lead.store
            vic = None
            while diff:
                k = next(iter(diff))
                del diff[k]
                if k in store and k not in ls and k != key:
                    vic = k
                    break
            if vic is None:
                for k in store:
                    if k != key:
                        vic = k
                        break
            del store[vic]
        return False
