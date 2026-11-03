import random


class _Core:
    """Resident set evicting the sampled key whose predicted next use is latest."""

    def __init__(self, capacity, new, late, sample, rng):
        self.mix = 1.0; self.c = capacity; self.new = new; self.late = late; self.sample = sample
        self.keys = []; self.pos = {}; self.r = rng.random

    def access(self, key, t, last, gap, dev):
        pos = self.pos
        if key in pos:
            return True
        ks = self.keys
        if len(ks) >= self.c:
            r = self.r; L = len(ks); new = self.new; late = self.late; mix = self.mix
            best = None; bn = -1.0
            for _ in range(self.sample):
                x = ks[int(r() * L)]
                g = gap.get(x, new); lx = last[x]
                # a key with irregular gaps is expected one gap from now, a periodic one a gap after its last use
                e = lx + g
                if mix:
                    d = dev.get(x, 0.0)
                    e += mix * (t - lx) * (d / g if d < g else 1.0)
                if e < t:
                    e = t + (t - e) * late + g
                if e > bn: bn = e; best = x
            # the key itself was just seen: its next use is about one gap away
            if t + gap.get(key, new) >= bn:
                return False
            i = pos.pop(best); lk = ks.pop()
            if lk != best: ks[i] = lk; pos[lk] = i
        pos[key] = len(ks); ks.append(key)
        return False


class Cache:
    """Approximate Belady from per-key reuse gaps; its settings follow the best shadow cache."""

    def __init__(self, capacity, news=(2.0, 12.0), lates=(0.3, 3.0), mixes=(0.0, 1.0), sample=16, hist=30.0,
                 alpha=0.2, period=1.0, decay=0.5, seed=1):
        rng = random.Random(seed)
        self.c = capacity
        self.last = {}; self.gap = {}; self.dev = {}
        self.hmax = int(capacity * hist); self.alpha = alpha; self.t = 0
        cfg = [(capacity * n, l, m) for n in news for l in lates for m in mixes]
        self.shadows = [_Core(capacity, n, l, sample, rng) for n, l, m in cfg]
        for s, c in zip(self.shadows, cfg):
            s.mix = c[2]
        self.score = [0.0] * len(cfg)
        self.real = _Core(capacity, cfg[0][0], cfg[0][1], sample, rng); self.real.mix = cfg[0][2]
        self.store = self.real.pos
        self.period = max(1, int(capacity * period)); self.tick = 0; self.decay = decay

    def access(self, key):
        self.t += 1; t = self.t
        last = self.last; gap = self.gap
        if key in last:
            g = t - last.pop(key); og = gap.get(key)
            if og is None:
                gap[key] = g
            else:
                a = self.alpha; od = self.dev.get(key, 0.0)
                self.dev[key] = od + a * (abs(g - og) - od)
                gap[key] = og + a * (g - og)
        last[key] = t
        if len(last) > self.hmax:
            x = next(iter(last))
            if x in self.store or any(x in s.pos for s in self.shadows):
                last[x] = last.pop(x)
            else:
                del last[x]; gap.pop(x, None); self.dev.pop(x, None)
        sc = self.score
        for i, s in enumerate(self.shadows):
            if s.access(key, t, last, gap, self.dev):
                sc[i] += 1
        self.tick += 1
        if self.tick >= self.period:
            self.tick = 0
            b = self.shadows[max(range(len(sc)), key=lambda i: sc[i])]
            self.real.new, self.real.late, self.real.mix = b.new, b.late, b.mix
            d = self.decay
            self.score = [x * d for x in sc]
        return self.real.access(key, t, last, gap, self.dev)
