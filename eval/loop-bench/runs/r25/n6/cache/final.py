from collections import OrderedDict


class _Lirs:
    def __init__(self, cap, lcap, smax):
        self.cap = cap; self.lcap = lcap; self.smax = cap * smax
        self.S = OrderedDict(); self.SH = OrderedDict(); self.Q = OrderedDict()
        self.lir = set(); self.store = set()

    def _demote(self):
        S, lir = self.S, self.lir
        k = next(iter(S)); del S[k]; lir.discard(k); self.Q[k] = True
        while S:
            b = next(iter(S))
            if b in lir: break
            del S[b]; del self.SH[b]

    def set_lcap(self, lcap):
        self.lcap = lcap
        while len(self.lir) > lcap: self._demote()

    def access(self, key):
        S, SH, Q, lir = self.S, self.SH, self.Q, self.lir
        if key in lir:
            first = next(iter(S)) == key
            S.move_to_end(key)
            if first:
                while S:
                    b = next(iter(S))
                    if b in lir: break
                    del S[b]; del SH[b]
            return True
        hit = key in self.store
        if hit:
            del Q[key]
        else:
            if len(self.store) >= self.cap:
                if Q:
                    k, _ = Q.popitem(last=False)
                else:
                    k = next(iter(S)); self._demote(); del self.Q[k]
                self.store.discard(k)
            self.store.add(key)
        if key in S or len(lir) < self.lcap:
            if key in SH: del SH[key]
            S.pop(key, None); S[key] = True
            lir.add(key)
            if len(lir) > self.lcap: self._demote()
        else:
            S[key] = True; SH[key] = True; Q[key] = True
            if len(S) > self.smax:
                k, _ = SH.popitem(last=False); del S[k]
        return hit


class _Arc:
    def __init__(self, capacity):
        self.c = capacity; self.p = 0
        self.t1 = OrderedDict(); self.t2 = OrderedDict(); self.b1 = OrderedDict(); self.b2 = OrderedDict()
        self.store = set()
    def _replace(self, inb2):
        if self.t1 and (len(self.t1) > self.p or (inb2 and len(self.t1) == self.p)):
            k, _ = self.t1.popitem(last=False); self.b1[k] = True
        else:
            k, _ = self.t2.popitem(last=False); self.b2[k] = True
        self.store.discard(k)
    def access(self, key):
        c = self.c
        if key in self.t1:
            del self.t1[key]; self.t2[key] = True; return True
        if key in self.t2:
            self.t2.move_to_end(key); return True
        if key in self.b1:
            self.p = min(c, self.p + max(len(self.b2) // max(len(self.b1),1), 1))
            self._replace(False); del self.b1[key]; self.t2[key] = True; self.store.add(key); return False
        if key in self.b2:
            self.p = max(0, self.p - max(len(self.b1) // max(len(self.b2),1), 1))
            self._replace(True); del self.b2[key]; self.t2[key] = True; self.store.add(key); return False
        l1 = len(self.t1) + len(self.b1)
        if l1 == c:
            if len(self.t1) < c:
                self.b1.popitem(last=False); self._replace(False)
            else:
                k, _ = self.t1.popitem(last=False); self.store.discard(k)
        elif l1 < c and l1 + len(self.t2) + len(self.b2) >= c:
            if l1 + len(self.t2) + len(self.b2) == 2 * c:
                self.b2.popitem(last=False)
            self._replace(False)
        self.t1[key] = True; self.store.add(key); return False
class _Tlfu:
    """W-TinyLFU: small LRU window, SLRU main, frequency-sketch admission."""
    WIN = 0.01; PROT = 0.8
    def __init__(self, capacity):
        self.cap = capacity
        self.wcap = max(1, int(capacity * self.WIN))
        self.mcap = capacity - self.wcap
        self.pcap = int(self.mcap * self.PROT)
        self.win = OrderedDict(); self.prob = OrderedDict(); self.prot = OrderedDict()
        self.freq = {}; self.n = 0; self.reset = capacity * 10
        self.store = set()
    def _inc(self, k):
        f = self.freq; f[k] = min(f.get(k, 0) + 1, 15); self.n += 1
        if self.n >= self.reset:
            self.n //= 2
            self.freq = {a: b >> 1 for a, b in f.items() if b > 1}
    def access(self, key):
        self._inc(key)
        if key in self.win:
            self.win.move_to_end(key); return True
        if key in self.prot:
            self.prot.move_to_end(key); return True
        if key in self.prob:
            del self.prob[key]; self.prot[key] = True
            if len(self.prot) > self.pcap:
                k, _ = self.prot.popitem(last=False); self.prob[k] = True
            return True
        self.win[key] = True; self.store.add(key)
        if len(self.win) > self.wcap:
            cand, _ = self.win.popitem(last=False)
            if len(self.prob) + len(self.prot) < self.mcap:
                self.prob[cand] = True
            else:
                victim = next(iter(self.prob)) if self.prob else next(iter(self.prot))
                f = self.freq
                if f.get(cand, 0) > f.get(victim, 0):
                    if victim in self.prob: del self.prob[victim]
                    else: del self.prot[victim]
                    self.store.discard(victim); self.prob[cand] = True
                else:
                    self.store.discard(cand)
        return False

class _Lru:
    def __init__(self, capacity):
        self.cap = capacity; self.d = OrderedDict(); self.store = set()
    def access(self, key):
        d = self.d
        if key in d:
            d.move_to_end(key); return True
        if len(d) >= self.cap:
            k, _ = d.popitem(last=False); self.store.discard(k)
        d[key] = True; self.store.add(key); return False


class _Log(set):
    def discard(self, k):
        if k in self:
            set.remove(self, k); self.ev.append(k)


def _logged(c):
    s = _Log(c.store); s.ev = []; c.store = s
    return c


class Cache:
    """Follows whichever shadow policy has the best recent hit rate: on a miss it evicts keys
    the leader no longer holds, so its contents converge to the leader's."""
    FRACS = (0.01, 0.1, 0.3, 0.6, 0.95); SMAX = 3; DECAY = 0.999; MARGIN = 0.0; OTHERS = 0

    def __init__(self, capacity):
        self.cap = capacity
        sh = [_Lirs(capacity, max(1, capacity - max(1, int(capacity * f))), self.SMAX) for f in self.FRACS]
        if self.OTHERS:
            sh += [_Tlfu(capacity), _Arc(capacity), _Lru(capacity)]
        self.shadows = [_logged(s) for s in sh]
        self.sc = [0.0] * len(sh); self.lead = 0
        self.store = set(); self.extra = OrderedDict()

    def access(self, key):
        sc = self.sc; d = self.DECAY; shadows = self.shadows
        for i, s in enumerate(shadows):
            s.store.ev = []
            sc[i] = sc[i] * d + s.access(key)
        m = max(sc); b = sc.index(m)
        store = self.store; extra = self.extra
        if b != self.lead and m > sc[self.lead] + self.MARGIN:
            self.lead = b; ls = shadows[b].store
            self.extra = extra = OrderedDict.fromkeys(k for k in store if k not in ls)
        else:
            for k in shadows[self.lead].store.ev:
                if k in store: extra[k] = True
        extra.pop(key, None)
        if key in store:
            return True
        if len(store) >= self.cap:
            if extra:
                k, _ = extra.popitem(last=False)
            else:
                k = next(iter(store))
            store.discard(k)
        store.add(key)
        return False
