from collections import OrderedDict


class _ARC:
    def __init__(self, capacity, ev):
        self.capacity = capacity
        self.ev = ev
        self.p = 0
        self.t1 = OrderedDict()
        self.t2 = OrderedDict()
        self.b1 = OrderedDict()
        self.b2 = OrderedDict()
        self.store = {}

    def _replace(self, in_b2):
        t1 = self.t1
        if t1 and (len(t1) > self.p or (in_b2 and len(t1) == self.p)):
            k, _ = t1.popitem(last=False)
            self.b1[k] = True
        else:
            k, _ = self.t2.popitem(last=False)
            self.b2[k] = True
        del self.store[k]
        self.ev.append(k)

    def access(self, key):
        store = self.store
        w = store.get(key)
        if w is not None:
            if w == 1:
                del self.t1[key]
                store[key] = 2
            else:
                del self.t2[key]
            self.t2[key] = True
            return True
        c = self.capacity
        b1, b2 = self.b1, self.b2
        if key in b1:
            self.p = min(c, self.p + max(1, len(b2) // len(b1)))
            self._replace(False)
            del b1[key]
            self.t2[key] = True
            store[key] = 2
            return False
        if key in b2:
            self.p = max(0, self.p - max(1, len(b1) // len(b2)))
            self._replace(True)
            del b2[key]
            self.t2[key] = True
            store[key] = 2
            return False
        l1 = len(self.t1) + len(b1)
        if l1 == c:
            if len(self.t1) < c:
                b1.popitem(last=False)
                self._replace(False)
            else:
                k, _ = self.t1.popitem(last=False)
                del store[k]
                self.ev.append(k)
        else:
            total = l1 + len(self.t2) + len(b2)
            if total >= c:
                if total == 2 * c:
                    b2.popitem(last=False)
                self._replace(False)
        self.t1[key] = True
        store[key] = 1
        return False


class _LIRS:
    def __init__(self, capacity, ev):
        self.capacity = capacity
        self.ev = ev
        self.hirs = max(1, capacity // 100)
        self.lirs = max(1, capacity - self.hirs)
        self.S = OrderedDict()
        self.Q = OrderedDict()
        self.status = {}
        self.store = {}
        self.nlir = 0
        self.slimit = capacity * 3

    def _prune(self):
        S, st = self.S, self.status
        while S:
            k = next(iter(S))
            if st.get(k) == 'L':
                break
            del S[k]
            if k not in self.store:
                st.pop(k, None)

    def _demote_bottom(self):
        S = self.S
        self._prune()
        if not S:
            return
        k = next(iter(S))
        del S[k]
        self.status[k] = 'H'
        self.nlir -= 1
        self.Q[k] = True
        self._prune()

    def _evict_hir(self):
        if self.Q:
            k, _ = self.Q.popitem(last=False)
            del self.store[k]
            self.ev.append(k)
            if k not in self.S:
                self.status.pop(k, None)

    def access(self, key):
        S, Q, st, store = self.S, self.Q, self.status, self.store
        s = st.get(key)
        if key in store:
            if s == 'L':
                was_bottom = next(iter(S)) == key
                del S[key]
                S[key] = True
                if was_bottom:
                    self._prune()
            else:
                if key in S:
                    del S[key]
                    S[key] = True
                    st[key] = 'L'
                    self.nlir += 1
                    del Q[key]
                    if self.nlir > self.lirs:
                        self._demote_bottom()
                else:
                    S[key] = True
                    Q.move_to_end(key)
            return True
        if len(store) >= self.capacity:
            if Q:
                self._evict_hir()
            else:
                self._demote_bottom()
                self._evict_hir()
            if len(store) >= self.capacity:
                k = next(iter(store))
                del store[k]
                self.ev.append(k)
                S.pop(k, None)
                Q.pop(k, None)
                st.pop(k, None)
                self.nlir = sum(1 for v in st.values() if v == 'L')
        if self.nlir < self.lirs and s != 'H':
            st[key] = 'L'
            self.nlir += 1
            S[key] = True
            store[key] = True
            return False
        if s == 'H' and key in S:
            del S[key]
            S[key] = True
            st[key] = 'L'
            self.nlir += 1
            store[key] = True
            if self.nlir > self.lirs:
                self._demote_bottom()
            if len(store) > self.capacity:
                self._evict_hir()
        else:
            st[key] = 'H'
            S[key] = True
            Q[key] = True
            store[key] = True
        if len(S) > 2 * self.slimit:
            # amortised trim: drop the oldest non-LIR stack entries
            drop = len(S) - self.slimit
            for k in list(S):
                if drop <= 0:
                    break
                if st.get(k) != 'L':
                    del S[k]
                    drop -= 1
                    if k not in store:
                        st.pop(k, None)
        return False




class _TLFU:
    """W-TinyLFU: small LRU window feeds an SLRU main cache through a frequency
    admission filter (exact counts with periodic halving)."""

    def __init__(self, capacity, ev):
        self.capacity = capacity
        self.ev = ev
        self.wsize = max(1, capacity // 100)
        msize = capacity - self.wsize
        self.prot_size = max(1, int(msize * 0.8))
        self.window = OrderedDict()
        self.prob = OrderedDict()
        self.prot = OrderedDict()
        self.store = {}  # key -> 0 window, 1 probation, 2 protected
        self.freq = {}
        self.samples = 0
        self.period = max(10 * capacity, 1000)

    def _count(self, key):
        f = self.freq
        f[key] = f.get(key, 0) + 1
        self.samples += 1
        if self.samples >= self.period:
            self.samples = 0
            for k in list(f):
                v = f[k] >> 1
                if v:
                    f[k] = v
                else:
                    del f[k]

    def _promote(self, key):
        prot = self.prot
        prot[key] = True
        self.store[key] = 2
        if len(prot) > self.prot_size:
            k, _ = prot.popitem(last=False)
            self.prob[k] = True
            self.store[k] = 1

    def access(self, key):
        self._count(key)
        store = self.store
        w = store.get(key)
        if w is not None:
            if w == 0:
                self.window.move_to_end(key)
            elif w == 1:
                del self.prob[key]
                self._promote(key)
            else:
                self.prot.move_to_end(key)
            return True
        window = self.window
        window[key] = True
        store[key] = 0
        if len(window) <= self.wsize:
            return False
        cand, _ = window.popitem(last=False)
        prob = self.prob
        msize = self.capacity - self.wsize
        if len(prob) + len(self.prot) < msize:
            prob[cand] = True
            store[cand] = 1
            return False
        victim = next(iter(prob)) if prob else next(iter(self.prot))
        f = self.freq
        if f.get(cand, 0) > f.get(victim, 0):
            if prob:
                prob.popitem(last=False)
            else:
                self.prot.popitem(last=False)
            del store[victim]
            self.ev.append(victim)
            prob[cand] = True
            store[cand] = 1
        else:
            del store[cand]
            self.ev.append(cand)
        return False


class Cache:
    """Runs several replacement policies as shadow simulations; the real store
    follows whichever has the best recent hit rate, evicting first the keys that
    no shadow holds, then keys the leader has dropped."""

    POLICIES = (_LIRS, _ARC)

    def __init__(self, capacity):
        self.capacity = capacity
        self.store = {}
        self.ev = []
        self.pols = [P(capacity, self.ev) for P in self.POLICIES]
        self.scores = [0.0] * len(self.pols)
        self.leader = 0
        self.none = set()    # in store, in no shadow
        self.other = set()   # in store, not in leader but in some other shadow
        self.decay = 1.0 - 1.0 / (2 * capacity)

    def _held_elsewhere(self, k, lead):
        for i, p in enumerate(self.pols):
            if i != lead and k in p.store:
                return True
        return False

    def access(self, key):
        store = self.store
        ev = self.ev
        pols, scores = self.pols, self.scores
        d = self.decay
        none, other = self.none, self.other
        lead = self.leader
        for i, p in enumerate(pols):
            del ev[:]
            h = p.access(key)
            scores[i] = scores[i] * d + (1.0 if h else 0.0)
            if i == lead:
                for k in ev:
                    if k in store:
                        if self._held_elsewhere(k, lead):
                            other.add(k)
                        else:
                            none.add(k)
            else:
                for k in ev:
                    if k in other and not self._held_elsewhere(k, lead):
                        other.discard(k)
                        none.add(k)
        best = 0
        for i in range(1, len(scores)):
            if scores[i] > scores[best]:
                best = i
        if best != lead and scores[best] > scores[lead] * 1.02 + 1.0:
            self.leader = lead = best
            ls = pols[lead].store
            none.clear()
            other.clear()
            for k in store:
                if k not in ls:
                    if self._held_elsewhere(k, lead):
                        other.add(k)
                    else:
                        none.add(k)
        if key in store:
            none.discard(key)
            other.discard(key)
            return True
        if len(store) >= self.capacity:
            if none:
                v = none.pop()
            elif other:
                v = other.pop()
            else:
                v = next(iter(store))
            del store[v]
        store[key] = True
        none.discard(key)
        other.discard(key)
        return False
