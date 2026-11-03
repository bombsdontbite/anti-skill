import time
import random
from collections import OrderedDict, deque

class WTinyLFU:
    """W-TinyLFU: LRU window, SLRU main, frequency-gated admission, hill-climbed window size."""

    def __init__(self, capacity, window_frac=0.01, adapt=True, reset_mult=10, fcap=1 << 30):
        self.fcap = fcap
        self.capacity = capacity
        self.store = {}
        self.ev = []
        self.window = OrderedDict()
        self.probation = OrderedDict()
        self.protected = OrderedDict()
        self.wmax = max(1, int(capacity * window_frac))
        self.freq = {}
        self.ops = 0
        self.reset_at = reset_mult * capacity
        self.adapt = adapt
        self.sample = 0
        self.hits = 0
        self.period = 10 * capacity
        self.prev_rate = 0.0
        self.step = max(1, capacity // 16)

    def _inc(self, key):
        f = self.freq
        v = f.get(key, 0)
        if v < self.fcap:
            f[key] = v + 1
        self.ops += 1
        if self.ops >= self.reset_at:
            self.ops = 0
            self.freq = {k: v >> 1 for k, v in f.items() if v > 1}

    def _climb(self, hit):
        self.sample += 1
        self.hits += hit
        if self.sample < self.period:
            return
        rate = self.hits / self.sample
        if rate < self.prev_rate - 0.001 or rate > self.prev_rate + 0.001:
            if rate < self.prev_rate:
                self.step = -self.step
        self.prev_rate = rate
        self.sample = self.hits = 0
        w = self.wmax + self.step
        self.wmax = min(self.capacity - 1, max(1, w))

    def access(self, key):
        self._inc(key)
        hit = self._access(key)
        if self.adapt:
            self._climb(hit)
        return hit

    def _access(self, key):
        if key in self.store:
            if key in self.window:
                self.window.move_to_end(key)
            elif key in self.protected:
                self.protected.move_to_end(key)
            else:
                del self.probation[key]
                self.protected[key] = True
                pmax = (self.capacity - self.wmax) * 4 // 5
                while len(self.protected) > pmax:
                    k, _ = self.protected.popitem(last=False)
                    self.probation[k] = True
            return True
        self.store[key] = True
        self.window[key] = True
        while len(self.window) > self.wmax:
            cand, _ = self.window.popitem(last=False)
            self.probation[cand] = True
        self._evict()
        return False

    def _evict(self):
        while len(self.store) > self.capacity:
            if not self.probation:
                k, _ = self.protected.popitem(last=False)
                self.probation[k] = True
                continue
            if len(self.probation) == 1 or not self.window and False:
                pass
            # candidate is most recent in probation (just moved from window); victim is oldest
            victim = next(iter(self.probation))
            cand = next(reversed(self.probation))
            if victim == cand:
                k = victim
            else:
                f = self.freq
                k = cand if f.get(cand, 0) <= f.get(victim, 0) else victim
            del self.probation[k]
            del self.store[k]
            self.ev.append(k)


class Pred:
    """Evicts the sampled key whose predicted next use (last use + estimated reuse gap) is farthest."""

    def __init__(self, capacity, nsamp=16, prior=4.0, hist=32, w=1.0, mix=0.5, umax=200.0, dmult=4.0, pexp=0.5):
        c = capacity
        self.capacity = c
        self.store = {}
        self.ev = []
        self.keys = []
        self.pos = {}
        self.meta = OrderedDict()
        self.t = 0
        self.nsamp = nsamp
        self.prior = prior * c
        self.pexp = pexp
        self.unk = prior * c
        self.umax = umax * c
        self.hmax = hist * c
        self.w = w
        self.mix = mix
        self.n1 = 1.0
        self.n2 = 0.1
        self.g2 = 0.1 * prior * c
        self.dec = 1 - 1 / (dmult * c)
        self.rng = random.Random(12345)

    def access(self, key):
        self.t += 1
        now = self.t
        m = self.meta
        e = m.get(key)
        d = self.dec
        self.n1 *= d
        self.n2 *= d
        self.g2 *= d
        if e is None:
            self.n1 += 1
            m[key] = (now, now, 1, 0.0)
            if len(m) > self.hmax:
                st = self.store
                while len(m) > self.hmax:
                    k = next(iter(m))
                    if k in st:
                        m.move_to_end(k)
                    else:
                        del m[k]
        else:
            g = now - e[1]
            if e[2] == 1:
                self.n2 += 1
                self.g2 += g
                ew = g
            else:
                ew = 0.5 * (e[3] + g)
            m[key] = (e[0], now, e[2] + 1, ew)
            m.move_to_end(key)
        st = self.store
        if key in st:
            return True
        u = (self.g2 / self.n2) * (self.n1 / self.n2)
        unk = self.unk = u if u < self.umax else self.umax
        if len(st) >= self.capacity:
            w = self.w
            mix = self.mix
            wp = w * self.prior ** (1 - self.pexp) * unk ** self.pexp
            keys = self.keys
            n = len(keys)
            r = self.rng.random
            best = None
            bp = -1
            for _ in range(self.nsamp):
                k = keys[int(r() * n)]
                first, last, c, ew = m[k]
                if c == 1:
                    p = last + unk
                else:
                    p = last + (1 - mix) * (last - first + wp) / (c - 1 + w) + mix * ew
                if p < now:
                    p = 2 * now - last
                if p > bp:
                    bp = p
                    best = k
            first, last, c, ew = m[key]
            if c == 1:
                p = now + unk
            else:
                p = now + (1 - mix) * (last - first + wp) / (c - 1 + w) + mix * ew
            if p >= bp:
                return False
            i = self.pos.pop(best)
            last = keys.pop()
            if last is not best:
                keys[i] = last
                self.pos[last] = i
            del st[best]
            self.ev.append(best)
        st[key] = True
        self.pos[key] = len(self.keys)
        self.keys.append(key)
        return False


class Cache:
    """Runs several policies in shadow and steers the real store toward the recent best one."""

    def __init__(self, capacity, decay_mult=10.0, names=(("pred", 16, 4.0, 32, 1.0, 0.5, 200.0, 4.0, 1.0), ("pred", 16, 4.0, 32, 1.0, 0.5, 200.0, 4.0, 0.0), ("wtlfu", 0.01, False, 30)), hyst=1.05, budget=0.8):
        self.hyst = hyst
        self.capacity = capacity
        mk = {"wtlfu": WTinyLFU, "pred": Pred}
        self.pols = [mk[n[0]](capacity, *n[1:]) for n in names]
        self.score = [0.0] * len(self.pols)
        self.decay = 1.0 - 1.0 / (decay_mult * capacity)
        self.lead = 0
        self.store = {}
        self.extra = deque()
        self.n = 0
        self.t0 = time.perf_counter()
        self.budget = budget

    def access(self, key):
        self.n += 1
        if self.n & 255 == 0 and len(self.pols) > 1 and time.perf_counter() - self.t0 > self.budget:
            # Out of time: keep only the current leader.
            self.pols = [self.pols[self.lead]]
            self.score = [self.score[self.lead]]
            self.lead = 0
        d = self.decay
        sc = self.score
        for i, p in enumerate(self.pols):
            sc[i] = sc[i] * d + p.access(key)
        best = self.lead
        for i in range(len(sc)):
            if sc[i] > sc[best]:
                best = i
        if best != self.lead and sc[best] > sc[self.lead] * self.hyst + 1e-9:
            self.lead = best
            ls = self.pols[best].store
            self.extra = deque(k for k in self.store if k not in ls)
        lead = self.pols[self.lead]
        if lead.ev:
            for k in lead.ev:
                if k in self.store:
                    self.extra.append(k)
        for p in self.pols:
            p.ev.clear()
        st = self.store
        if key in st:
            return True
        if len(st) < self.capacity:
            st[key] = True
            return False
        if key not in lead.store:
            return False
        ls = lead.store
        ex = self.extra
        while ex:
            k = ex.popleft()
            if k in st and k not in ls:
                del st[k]
                st[key] = True
                return False
        return False
