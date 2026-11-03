from collections import OrderedDict


class LRU:
    def __init__(self, capacity):
        self.c = capacity
        self.store = OrderedDict()
        self.ev = []

    def access(self, key):
        s = self.store
        if key in s:
            s.move_to_end(key)
            return True
        if len(s) >= self.c:
            self.ev.append(s.popitem(last=False)[0])
        s[key] = None
        return False


class LIRS:
    def __init__(self, capacity, hir_frac=0.01, smax=8):
        self.c = capacity
        self.lc = capacity - max(1, int(capacity * hir_frac))
        self.S = OrderedDict()
        self.Q = OrderedDict()
        self.lir = set()
        self.store = set()
        self.smax = smax * capacity
        self.ev = []

    def _prune(self):
        S, lir = self.S, self.lir
        while S:
            k = next(iter(S))
            if k in lir:
                break
            del S[k]

    def access(self, key):
        S, lir = self.S, self.lir
        if key in lir:
            S.move_to_end(key)
            self._prune()
            return True
        hit = key in self.store
        if not hit:
            if len(lir) < self.lc:
                lir.add(key)
                S[key] = None
                self.store.add(key)
                return False
            if len(self.store) >= self.c:
                v = self.Q.popitem(last=False)[0]
                self.store.discard(v)
                self.ev.append(v)
            self.store.add(key)
        if key in S:
            S.move_to_end(key)
            lir.add(key)
            self.Q.pop(key, None)
            b = next(iter(S))
            lir.discard(b)
            del S[b]
            self.Q[b] = None
            self._prune()
        else:
            S[key] = None
            if key in self.Q:
                self.Q.move_to_end(key)
            else:
                self.Q[key] = None
        if len(S) > self.smax:
            st, tgt = self.store, self.smax * 3 // 4
            for k in list(S):
                if len(S) <= tgt:
                    break
                if k not in st:
                    del S[k]
        return hit


class TinyLFU:
    def __init__(self, capacity, wfrac=0.01, reset=10):
        self.c = capacity
        self.wc = max(1, int(capacity * wfrac))
        self.mc = capacity - self.wc
        self.pc = int(self.mc * 0.8)
        self.W = OrderedDict()
        self.P = OrderedDict()
        self.Pr = OrderedDict()
        self.f = {}
        self.n = 0
        self.reset = reset * capacity
        self.store = set()
        self.ev = []

    def access(self, key):
        f = self.f
        f[key] = f.get(key, 0) + 1
        self.n += 1
        if self.n >= self.reset:
            self.n //= 2
            self.f = f = {a: b // 2 for a, b in f.items() if b > 1}
        if key in self.W:
            self.W.move_to_end(key)
            return True
        if key in self.Pr:
            self.Pr.move_to_end(key)
            return True
        if key in self.P:
            del self.P[key]
            self.Pr[key] = None
            if len(self.Pr) > self.pc:
                self.P[self.Pr.popitem(last=False)[0]] = None
            return True
        self.W[key] = None
        self.store.add(key)
        if len(self.W) > self.wc:
            k = self.W.popitem(last=False)[0]
            if len(self.P) + len(self.Pr) < self.mc:
                self.P[k] = None
            else:
                vq = self.P if self.P else self.Pr
                v = next(iter(vq))
                if f.get(k, 0) > f.get(v, 0):
                    del vq[v]
                    self.store.discard(v)
                    self.P[k] = None
                    self.ev.append(v)
                else:
                    self.store.discard(k)
                    self.ev.append(k)
        return False


class DLIRS:
    def __init__(self, capacity, hir_frac=0.01, smax=8, dead=2):
        self.c=capacity; self.lc=capacity-max(1,int(capacity*hir_frac))
        self.S=OrderedDict(); self.Q=OrderedDict(); self.lir=set(); self.store=set()
        self.smax=smax*capacity; self.ev=[]; self.t=0; self.last={}; self.T=dead*capacity
    def _prune(self):
        S,lir=self.S,self.lir
        while S:
            k=next(iter(S))
            if k in lir: break
            del S[k]
    def access(self, key):
        S,lir=self.S,self.lir; self.t+=1; t=self.t
        if key in lir:
            S.move_to_end(key); self.last[key]=t; self._prune(); return True
        hit=key in self.store
        if not hit:
            if len(lir)<self.lc:
                lir.add(key); S[key]=None; self.store.add(key); self.last[key]=t; return False
            b=next(iter(S))
            if t-self.last[b]>self.T:
                lir.discard(b); del S[b]; del self.last[b]; self.store.discard(b); self.ev.append(b)
                self._prune()
                S.pop(key,None); lir.add(key); S[key]=None; self.store.add(key); self.last[key]=t
                return False
            if len(self.store)>=self.c:
                v=self.Q.popitem(last=False)[0]; self.store.discard(v); self.ev.append(v)
            self.store.add(key)
        if key in S:
            S.move_to_end(key); lir.add(key); self.last[key]=t; self.Q.pop(key,None)
            b=next(iter(S)); lir.discard(b); del S[b]; del self.last[b]; self.Q[b]=None
            self._prune()
        else:
            S[key]=None
            if key in self.Q: self.Q.move_to_end(key)
            else: self.Q[key]=None
        if len(S)>self.smax:
            st,tgt=self.store,self.smax*3//4
            for k in list(S):
                if len(S)<=tgt: break
                if k not in st: del S[k]
        return hit


class Cache:
    """Follow whichever shadow policy has had the most recent hits."""

    def __init__(self, capacity, decay=0.99997):
        self.capacity = capacity
        self.experts = [LRU(capacity), LIRS(capacity), TinyLFU(capacity, reset=100), DLIRS(capacity)]
        self.score = [0.0] * len(self.experts)
        # per expert: real keys that expert does not hold, oldest-evicted first
        self.extra = [OrderedDict() for _ in self.experts]
        self.decay = decay
        self.lead = 1
        self.margin = 1.02
        self.store = set()

    def access(self, key):
        store = self.store
        hit = key in store
        d = self.decay
        sc = self.score
        for i, e in enumerate(self.experts):
            sc[i] = sc[i] * d + e.access(key)
            ex = self.extra[i]
            for v in e.ev:
                if v in store:
                    ex[v] = None
            e.ev.clear()
            ex.pop(key, None)
        if hit:
            return True
        if len(store) >= self.capacity:
            best = max(range(len(sc)), key=lambda i: sc[i])
            if sc[best] > sc[self.lead] * self.margin + 1:
                self.lead = best
            lead = self.lead
            ex = self.extra[lead]
            v = next(iter(ex)) if ex else next(iter(store))
            store.discard(v)
            for x in self.extra:
                x.pop(v, None)
        store.add(key)
        return False
