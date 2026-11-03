from collections import OrderedDict, deque

class LIRS:
    """LIRS with bounded non-resident history."""

    HIR = 0.01

    def __init__(self, capacity):
        self.capacity = capacity
        self.hcap = max(1, int(capacity * self.HIR))
        self.lcap = capacity - self.hcap
        self.S = OrderedDict()   # key -> True if LIR
        self.Q = OrderedDict()   # resident HIR
        self.lir = set()
        self.store = set()
        self.ev = []
        self.maxS = 3 * capacity

    def _prune(self):
        S = self.S
        while S:
            k = next(iter(S))
            if k in self.lir:
                break
            del S[k]

    def _demote(self):
        k, _ = self.S.popitem(last=False)
        self.lir.discard(k)
        self.Q[k] = True
        self._prune()

    def _trim(self):
        S = self.S
        if len(S) > self.maxS + self.capacity:
            for k in list(S)[:len(S) - self.maxS]:
                if k not in self.lir and k not in self.store:
                    del S[k]

    def _ev(self, k):
        self.store.discard(k)
        self.ev.append(k)

    def access(self, key):
        S = self.S
        if key in self.lir:
            first = next(iter(S)) == key
            S.move_to_end(key)
            if first:
                self._prune()
            return True
        if key in self.store:  # resident HIR
            if key in S:
                S.move_to_end(key)
                del self.Q[key]
                self.lir.add(key)
                self._demote()
            else:
                S[key] = True
                self.Q.move_to_end(key)
            return True
        # miss
        if len(self.store) >= self.capacity:
            v, _ = self.Q.popitem(last=False)
            self._ev(v)
        self.store.add(key)
        if len(self.lir) < self.lcap:
            S[key] = True; S.move_to_end(key); self.lir.add(key)
            return False
        if key in S:
            S.move_to_end(key)
            self.lir.add(key)
            self._demote()
        else:
            S[key] = True
            self.Q[key] = True
        self._trim()
        return False


class WTLFU:
    """W-TinyLFU: LRU window, SLRU main, frequency-based admission."""

    WIN = 0.01
    PROT = 0.8

    def __init__(self, capacity, reset=10):
        self.capacity = capacity
        self.store = set()
        self.ev = []
        self.wcap = max(1, int(capacity * self.WIN))
        self.mcap = capacity - self.wcap
        self.pcap = int(self.mcap * self.PROT)
        self.win = OrderedDict()
        self.prob = OrderedDict()
        self.prot = OrderedDict()
        self.freq = {}
        self.ops = 0
        self.reset = reset * capacity

    def _count(self, key):
        f = self.freq
        f[key] = f.get(key, 0) + 1
        self.ops += 1
        if self.ops >= self.reset:
            self.ops = 0
            self.freq = {k: v >> 1 for k, v in f.items() if v > 1}

    def _ev(self, k):
        self.store.discard(k)
        self.ev.append(k)

    def access(self, key):
        self._count(key)
        if key in self.win:
            self.win.move_to_end(key)
            return True
        if key in self.prot:
            self.prot.move_to_end(key)
            return True
        if key in self.prob:
            del self.prob[key]
            self.prot[key] = True
            if len(self.prot) > self.pcap:
                k, _ = self.prot.popitem(last=False)
                self.prob[k] = True
            return True
        self.win[key] = True
        self.store.add(key)
        if len(self.win) > self.wcap:
            cand, _ = self.win.popitem(last=False)
            if len(self.prob) + len(self.prot) < self.mcap:
                self.prob[cand] = True
            else:
                victim = next(iter(self.prob)) if self.prob else next(iter(self.prot))
                f = self.freq
                if f.get(cand, 0) > f.get(victim, 0):
                    if victim in self.prob:
                        del self.prob[victim]
                    else:
                        del self.prot[victim]
                    self._ev(victim)
                    self.prob[cand] = True
                else:
                    self._ev(cand)
        return False


class S3:
    """S3-FIFO: small FIFO, main FIFO with reinsertion, ghost FIFO."""

    SMALL = 0.1

    def __init__(self, capacity):
        self.capacity = capacity
        self.scap = max(1, int(capacity * self.SMALL))
        self.small = deque(); self.main = deque()
        self.freq = {}
        self.ghost = OrderedDict()
        self.store = set()
        self.ev = []

    def _evict_main(self):
        while True:
            k = self.main.popleft()
            f = self.freq[k]
            if f > 0:
                self.freq[k] = f - 1; self.main.append(k)
            else:
                del self.freq[k]; self._ev(k); return

    def _evict(self):
        if len(self.small) >= self.scap or not self.main:
            k = self.small.popleft()
            if self.freq[k] > 0:
                self.freq[k] = 0
                self.main.append(k)
                if len(self.main) > self.capacity - len(self.small):
                    self._evict_main()
                return self._evict() if len(self.store) >= self.capacity else None
            del self.freq[k]; self._ev(k)
            self.ghost[k] = True
            if len(self.ghost) > self.capacity:
                self.ghost.popitem(last=False)
        else:
            self._evict_main()

    def _ev(self, k):
        self.store.discard(k)
        self.ev.append(k)

    def access(self, key):
        if key in self.store:
            self.freq[key] = min(3, self.freq[key] + 1); return True
        while len(self.store) >= self.capacity:
            self._evict()
        self.store.add(key); self.freq[key] = 0
        if key in self.ghost:
            del self.ghost[key]; self.main.append(key)
        else:
            self.small.append(key)
        return False


class LRU:
    def __init__(self, capacity):
        self.capacity = capacity
        self.store = OrderedDict()
        self.ev = []

    def access(self, key):
        s = self.store
        if key in s:
            s.move_to_end(key)
            return True
        if len(s) >= self.capacity:
            k, _ = s.popitem(last=False)
            self.ev.append(k)
        s[key] = True
        return False


class Cache:
    """Follow whichever shadow policy has the most recent hits."""

    DECAY = 0.9998
    MARGIN = 20.0

    def __init__(self, capacity):
        self.capacity = capacity
        self.store = set()
        self.sh = [LIRS(capacity), WTLFU(capacity), S3(capacity), LRU(capacity), WTLFU(capacity, 100)]
        self.sc = [0.0] * len(self.sh)
        self.lead = 0
        self.diff = set()

    def access(self, key):
        hit = key in self.store
        sh = self.sh; sc = self.sc; d = self.DECAY
        for i in range(len(sh)):
            p = sh[i]
            h = p.access(key)
            sc[i] = sc[i] * d + (1.0 if h else 0.0)
        best = self.lead
        for i in range(len(sh)):
            if sc[i] > sc[best] + self.MARGIN:
                best = i
        lead = sh[best]
        if best != self.lead:
            self.lead = best
            self.diff = {k for k in self.store if k not in lead.store}
        else:
            for k in lead.ev:
                if k in self.store:
                    self.diff.add(k)
        for p in sh:
            p.ev.clear()
        self.diff.discard(key)
        if not hit:
            self.store.add(key)
            if len(self.store) > self.capacity:
                self.store.discard(self.diff.pop())
        return hit
