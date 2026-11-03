import heapq
import random
import time

POP = 26
TIME_CAP = 0.74


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


def _fitness(jobs, perm, m):
    free = [0] * m
    tot = 0
    for j in perm:
        r, p, d, w = jobs[j]
        k = free.index(min(free))
        s = free[k]
        if s < r:
            s = r
        e = s + p
        free[k] = e
        if e > d:
            tot += w * (e - d)
    return tot


def _realise(jobs, perm, m):
    free = [0] * m
    out = []
    for j in perm:
        k = free.index(min(free))
        s = max(free[k], jobs[j][0])
        free[k] = s + jobs[j][1]
        out.append((j, k, s))
    return out


def _lox(a, b, rng):
    n = len(a)
    i = rng.randrange(n)
    j = rng.randrange(n)
    if i > j:
        i, j = j, i
    seg = a[i:j + 1]
    inseg = set(seg)
    rest = [x for x in b if x not in inseg]
    return rest[:i] + seg + rest[i:]


def _mutate(perm, rng):
    n = len(perm)
    i = rng.randrange(n)
    j = min(n - 1, max(0, i + rng.randint(-15, 15)))
    if rng.random() < 0.5:
        perm[i], perm[j] = perm[j], perm[i]
    else:
        perm.insert(j, perm.pop(i))


def schedule(jobs, m):
    t0 = time.perf_counter()
    n = len(jobs)
    if n == 0:
        return []
    base = _edf(jobs, m)
    base_c = _cost(jobs, base)
    if base_c == 0 or n < 4:
        return base

    rng = random.Random(1234567)
    seeds = [
        [j for j, _k, _s in sorted(base, key=lambda x: (x[2], x[0]))],
        sorted(range(n), key=lambda j: (jobs[j][2], j)),
        sorted(range(n), key=lambda j: (jobs[j][2] - jobs[j][1], j)),
        sorted(range(n), key=lambda j: (jobs[j][0], jobs[j][2])),
        sorted(range(n), key=lambda j: (jobs[j][2] - 0.5 * jobs[j][1] * jobs[j][3] / (1 + jobs[j][3]), j)),
    ]
    pop = []
    for s in seeds:
        pop.append((_fitness(jobs, s, m), s))
    while len(pop) < POP:
        s = list(rng.choice(seeds))
        for _ in range(rng.randint(3, 12)):
            _mutate(s, rng)
        pop.append((_fitness(jobs, s, m), s))
    pop.sort(key=lambda x: x[0])

    def pick():
        a = pop[rng.randrange(len(pop))]
        b = pop[rng.randrange(len(pop))]
        return a if a[0] <= b[0] else b

    while time.perf_counter() - t0 < TIME_CAP:
        pa = pick()[1]
        pb = pick()[1]
        child = _lox(pa, pb, rng) if rng.random() < 0.8 else pa[:]
        for _ in range(rng.choice((0, 1, 1, 2))):
            _mutate(child, rng)
        f = _fitness(jobs, child, m)
        if f < pop[-1][0] and all(f != q[0] for q in pop):
            pop[-1] = (f, child)
            pop.sort(key=lambda x: x[0])
            if f == 0:
                break

    sch = _realise(jobs, pop[0][1], m)
    if _cost(jobs, sch) < base_c:
        return sch
    return base
