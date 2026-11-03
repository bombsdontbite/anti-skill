from collections import OrderedDict, deque


class LRU:
    def __init__(self, capacity):
        self.capacity = capacity
        self.store = OrderedDict()
        self.evicted = None

    def access(self, key):
        self.evicted = None
        s = self.store
        if key in s:
            s.move_to_end(key)
            return True
        if len(s) >= self.capacity:
            self.evicted, _ = s.popitem(last=False)
        s[key] = True
        return False


class ARC:
    def __init__(self, capacity):
        self.c = capacity
        self.p = 0
        self.t1 = OrderedDict(); self.t2 = OrderedDict()
        self.b1 = OrderedDict(); self.b2 = OrderedDict()
        self.store = set()
        self.evicted = None

    def _replace(self, in_b2):
        t1, t2 = self.t1, self.t2
        if t1 and (len(t1) > self.p or (in_b2 and len(t1) == self.p)):
            k, _ = t1.popitem(last=False)
            self.b1[k] = True
        else:
            k, _ = t2.popitem(last=False)
            self.b2[k] = True
        self.store.discard(k)
        self.evicted = k

    def access(self, key):
        self.evicted = None
        t1, t2, b1, b2, c = self.t1, self.t2, self.b1, self.b2, self.c
        if key in t1:
            del t1[key]; t2[key] = True
            return True
        if key in t2:
            t2.move_to_end(key)
            return True
        if key in b1:
            self.p = min(c, self.p + max(1, len(b2) // max(1, len(b1))))
            self._replace(False)
            del b1[key]
            t2[key] = True; self.store.add(key)
            return False
        if key in b2:
            self.p = max(0, self.p - max(1, len(b1) // max(1, len(b2))))
            self._replace(True)
            del b2[key]
            t2[key] = True; self.store.add(key)
            return False
        l1 = len(t1) + len(b1)
        if l1 == c:
            if len(t1) < c:
                b1.popitem(last=False)
                self._replace(False)
            else:
                k, _ = t1.popitem(last=False); self.store.discard(k)
                self.evicted = k
        elif l1 < c and l1 + len(t2) + len(b2) >= c:
            if l1 + len(t2) + len(b2) >= 2 * c:
                b2.popitem(last=False)
            self._replace(False)
        t1[key] = True; self.store.add(key)
        return False


class TinyLFU:
    def __init__(self, capacity, wfrac=0.02):
        self.cap = capacity
        self.wmax = max(1, int(capacity * wfrac))
        self.mmax = capacity - self.wmax
        self.pmax = int(0.8 * self.mmax)
        self.window = OrderedDict()
        self.prob = OrderedDict()
        self.prot = OrderedDict()
        self.store = set()
        self.freq = {}
        self.sample = 0
        self.limit = 10 * capacity
        self.evicted = None

    def access(self, key):
        self.evicted = None
        f = self.freq
        f[key] = f.get(key, 0) + 1
        self.sample += 1
        if self.sample >= self.limit:
            self.sample = 0
            self.freq = f = {k: v >> 1 for k, v in f.items() if v > 1}
        window, prob, prot = self.window, self.prob, self.prot
        if key in window:
            window.move_to_end(key)
            return True
        if key in prot:
            prot.move_to_end(key)
            return True
        if key in prob:
            del prob[key]
            prot[key] = True
            if len(prot) > self.pmax:
                k, _ = prot.popitem(last=False)
                prob[k] = True
            return True
        self.store.add(key)
        window[key] = True
        if len(window) > self.wmax:
            cand, _ = window.popitem(last=False)
            if len(prob) + len(prot) < self.mmax:
                prob[cand] = True
            else:
                victim = next(iter(prob)) if prob else next(iter(prot))
                if f.get(cand, 0) > f.get(victim, 0):
                    if victim in prob:
                        del prob[victim]
                    else:
                        del prot[victim]
                    self.store.discard(victim)
                    self.evicted = victim
                    prob[cand] = True
                else:
                    self.store.discard(cand)
                    self.evicted = cand
        return False


class LFU:
    """Decayed LFU with frequency-based admission."""

    def __init__(self, capacity, period=10):
        self.cap = capacity
        self.store = set()
        self.freq = {}
        self.sample = 0
        self.limit = period * capacity
        self.evicted = None

    def access(self, key):
        self.evicted = None
        f = self.freq
        f[key] = f.get(key, 0) + 1
        self.sample += 1
        store = self.store
        if self.sample >= self.limit:
            self.sample = 0
            self.freq = f = {k: v >> 1 for k, v in f.items() if v > 1 or k in store}
        if key in store:
            return True
        if len(store) < self.cap:
            store.add(key)
            return False
        victim = min(store, key=f.get)
        if f.get(key, 0) > f[victim]:
            store.discard(victim)
            self.evicted = victim
            store.add(key)
        else:
            self.evicted = key
        return False


class Cache:
    """Runs several policies as shadows and mirrors the one with the best recent hit rate.
    Switches only when a shadow clearly beats both the current leader and this cache itself,
    and not more often than once per capacity accesses, since each switch costs a transition."""

    DECAY = 0.999
    MARGIN = 1.1

    def __init__(self, capacity):
        self.capacity = capacity
        self.store = OrderedDict()
        self.shadows = [LRU(capacity), ARC(capacity), TinyLFU(capacity), LFU(capacity)]
        self.scores = [0.0] * len(self.shadows)
        self.own = 0.0
        self.leader = 2
        self.since = 0
        self.stale = deque()

    def access(self, key):
        d = self.DECAY
        scores = self.scores
        for i, sh in enumerate(self.shadows):
            scores[i] = scores[i] * d + (1.0 if sh.access(key) else 0.0)
        self.since += 1
        store = self.store
        if key in store:
            store.move_to_end(key)
            self.own = self.own * d + 1.0
            return True
        self.own = self.own * d
        if self.since >= 2 * self.capacity:
            best = scores.index(max(scores))
            if best != self.leader and scores[best] > max(scores[self.leader], self.own) * self.MARGIN + 1.0:
                self.leader = best
                self.since = 0
                self.stale.clear()
                ls = self.shadows[best].store
                self.stale.extend(k for k in store if k not in ls)
        leader = self.shadows[self.leader]
        ev = leader.evicted
        if ev is not None and ev in store:
            self.stale.append(ev)
        if len(store) >= self.capacity:
            ls = leader.store
            stale = self.stale
            victim = None
            while stale:
                k = stale.popleft()
                if k in store and k not in ls:
                    victim = k
                    break
            if victim is None:
                for k in store:
                    if k not in ls:
                        victim = k
                        break
                if victim is None:
                    victim = next(iter(store))
            del store[victim]
        store[key] = True
        return False
