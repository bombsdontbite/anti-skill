import heapq
import math
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


def _grasp_run(jobs, m, by_release, logwp, scale, rng, rcl, bound):
    """One randomized ATC construction; aborts early once its cost passes `bound`."""
    n = len(jobs)
    free = [(0, k) for k in range(m)]
    ready, out, i, cost = [], [], 0, 0
    while len(out) < n:
        t, k = heapq.heappop(free)
        if not ready and jobs[by_release[i]][0] > t:
            t = jobs[by_release[i]][0]
        while i < n and jobs[by_release[i]][0] <= t:
            ready.append(by_release[i])
            i += 1
        top = []
        for idx in range(len(ready)):
            j = ready[idx]
            s = jobs[j][2] - jobs[j][1] - t
            v = logwp[j] - (s / scale if s > 0 else 0.0)
            if len(top) < rcl:
                top.append((v, idx))
                top.sort(reverse=True)
            elif v > top[-1][0]:
                top[-1] = (v, idx)
                top.sort(reverse=True)
        if rcl == 1 or len(top) == 1:
            pick = top[0][1]
        else:
            u = rng.random()
            if u < 0.7:
                pick = top[0][1]
            elif u < 0.9:
                pick = top[1][1]
            else:
                pick = top[rng.randrange(len(top))][1]
        j = ready[pick]
        ready[pick] = ready[-1]
        ready.pop()
        out.append((j, k, t))
        end = t + jobs[j][1]
        if end > jobs[j][2]:
            cost += jobs[j][3] * (end - jobs[j][2])
            if bound is not None and cost >= bound:
                return None, cost
        heapq.heappush(free, (end, k))
    return out, cost


def schedule(jobs, m):
    t0 = time.perf_counter()
    n = len(jobs)
    if n == 0:
        return []
    best = _edf(jobs, m)
    best_c = _cost(jobs, best)
    if best_c == 0:
        return best

    rng = random.Random(99)
    pbar = (sum(jb[1] for jb in jobs) / n) or 1.0
    logwp = [math.log(max(w, 1e-6) / (p if p > 0 else 0.5)) for r, p, d, w in jobs]
    by_release = sorted(range(n), key=lambda j: (jobs[j][0], j))
    ks = [0.25, 0.5, 1.0, 1.5, 2.0, 3.0, 4.5]
    score = {kk: 0.0 for kk in ks}

    for kk in ks:
        sch, c = _grasp_run(jobs, m, by_release, logwp, kk * pbar, rng, 1, None)
        score[kk] = c
        if c < best_c:
            best, best_c = sch, c
            if best_c == 0:
                return best
    ranked = sorted(ks, key=lambda kk: score[kk])
    favoured = ranked[:3]

    while time.perf_counter() - t0 < 0.72:
        if rng.random() < 0.75:
            kk = rng.choice(favoured) * math.exp(rng.uniform(-0.3, 0.3))
        else:
            kk = rng.uniform(0.1, 5.0)
        rcl = rng.choice((2, 3, 3, 4))
        sch, c = _grasp_run(jobs, m, by_release, logwp, kk * pbar, rng, rcl, best_c)
        if sch is not None and c < best_c:
            best, best_c = sch, c
            if best_c == 0:
                break
    return best
