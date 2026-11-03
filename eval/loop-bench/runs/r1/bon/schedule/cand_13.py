import heapq
import random
import time


def _edf(jobs, m):
    order = sorted(range(len(jobs)), key=lambda j: (jobs[j][0], j))
    free = [(0, k) for k in range(m)]
    ready, out, i = [], [], 0
    while len(out) < len(jobs):
        t, k = heapq.heappop(free)
        if not ready and i < len(order) and jobs[order[i]][0] > t:
            t = jobs[order[i]][0]
        while i < len(order) and jobs[order[i]][0] <= t:
            j = order[i]
            heapq.heappush(ready, (jobs[j][2], j))
            i += 1
        _, j = heapq.heappop(ready)
        t = max(t, jobs[j][0])
        out.append((j, k, t))
        heapq.heappush(free, (t + jobs[j][1], k))
    return out


def _cost(jobs, sched):
    c = 0
    for j, _k, s in sched:
        late = s + jobs[j][1] - jobs[j][2]
        if late > 0:
            c += jobs[j][3] * late
    return c


def _decode(jobs, keys, m, build=False):
    seq = sorted(range(len(jobs)), key=lambda j: keys[j])
    free = [0] * m
    cost = 0
    out = []
    for j in seq:
        r, p, d, w = jobs[j]
        k = min(range(m), key=lambda q: free[q])
        s = free[k] if free[k] > r else r
        free[k] = s + p
        if s + p > d:
            cost += w * (s + p - d)
        if build:
            out.append((j, k, s))
    return cost, out


def schedule(jobs, m):
    t0 = time.perf_counter()
    n = len(jobs)
    if n == 0:
        return []
    base = _edf(jobs, m)
    base_c = _cost(jobs, base)
    if base_c == 0 or n < 2:
        return base

    rng = random.Random(2468)
    pop_size, n_elite, n_mut, bias = 30, 6, 5, 0.7

    def from_order(order):
        keys = [0.0] * n
        for pos, j in enumerate(order):
            keys[j] = (pos + 0.5) / n
        return keys

    seeded = [
        from_order([j for j, _k, _s in sorted(base, key=lambda x: (x[2], x[0]))]),
        from_order(sorted(range(n), key=lambda j: (jobs[j][2], j))),
        from_order(sorted(range(n), key=lambda j: (jobs[j][2] - jobs[j][1], j))),
    ]
    pop = []
    for ks in seeded:
        pop.append((_decode(jobs, ks, m)[0], ks))
    while len(pop) < pop_size:
        src = rng.choice(seeded)
        ks = [x + rng.gauss(0, 0.03) for x in src]
        pop.append((_decode(jobs, ks, m)[0], ks))
    pop.sort(key=lambda x: x[0])

    while time.perf_counter() - t0 < 0.74 and pop[0][0] > 0:
        elite = pop[:n_elite]
        others = pop[n_elite:]
        nxt = list(elite)
        for _ in range(n_mut):
            if time.perf_counter() - t0 > 0.74:
                break
            src = rng.choice(elite)[1]
            ks = [x + rng.gauss(0, 0.05) if rng.random() < 0.1 else x for x in src]
            nxt.append((_decode(jobs, ks, m)[0], ks))
        while len(nxt) < pop_size:
            if time.perf_counter() - t0 > 0.74:
                break
            e = rng.choice(elite)[1]
            o = rng.choice(others)[1] if others else rng.choice(elite)[1]
            ks = [e[i] if rng.random() < bias else o[i] for i in range(n)]
            nxt.append((_decode(jobs, ks, m)[0], ks))
        if len(nxt) < n_elite + 1:
            break
        nxt.sort(key=lambda x: x[0])
        pop = nxt

    c, sch = _decode(jobs, pop[0][1], m, True)
    if c < base_c:
        return sch
    return base
