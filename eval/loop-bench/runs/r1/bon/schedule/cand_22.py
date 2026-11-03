"""Max-min ant system over job sequences. Pheromone is kept per (job, position bucket);
the visibility of a job is its modified due date seen from the earliest free machine."""
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


def schedule(jobs, m):
    t0 = time.perf_counter()
    n = len(jobs)
    if n == 0:
        return []
    base = _edf(jobs, m)
    base_c = _cost(jobs, base)
    if base_c == 0 or n < 3:
        return base

    rng = random.Random(22)
    R = [jb[0] for jb in jobs]
    P = [jb[1] for jb in jobs]
    D = [jb[2] for jb in jobs]
    W = [jb[3] for jb in jobs]
    wbar = (sum(W) / n) or 1.0
    edd = sorted(range(n), key=lambda j: (D[j], R[j], j))
    bucket = 10
    nb = n // bucket + 1
    tau_max, tau_min, rho = 1.0, 0.05, 0.1
    tau = [[tau_max] * nb for _ in range(n)]
    cand_len = 10
    q0 = 0.85

    def ant(greedy):
        rem = edd[:]
        free = [0] * m
        cost = 0
        seq = []
        trail = []
        for pos in range(n):
            k = 0
            for q in range(1, m):
                if free[q] < free[k]:
                    k = q
            t = free[k]
            b = pos // bucket
            lim = cand_len if cand_len < len(rem) else len(rem)
            scores = []
            for ci in range(lim):
                j = rem[ci]
                s = R[j] if R[j] > t else t
                mdd = D[j] if D[j] > s + P[j] else s + P[j]
                eta = (0.5 + W[j] / wbar) / (mdd - t + 1.0)
                scores.append(tau[j][b] * eta * eta)
            if greedy or rng.random() < q0:
                ci = max(range(lim), key=lambda x: scores[x])
            else:
                tot = sum(scores)
                u = rng.random() * tot
                ci = lim - 1
                acc = 0.0
                for x in range(lim):
                    acc += scores[x]
                    if acc >= u:
                        ci = x
                        break
            j = rem.pop(ci)
            s = R[j] if R[j] > t else t
            free[k] = s + P[j]
            if s + P[j] > D[j]:
                cost += W[j] * (s + P[j] - D[j])
            seq.append(j)
            trail.append((j, k, s))
        return cost, seq, trail

    best_c, best_seq, best_trail = ant(True)
    while time.perf_counter() - t0 < 0.74 and best_c > 0:
        it_best = None
        for _ in range(6):
            if time.perf_counter() - t0 > 0.74:
                break
            res = ant(False)
            if it_best is None or res[0] < it_best[0]:
                it_best = res
        if it_best is None:
            break
        if it_best[0] < best_c:
            best_c, best_seq, best_trail = it_best
        for row in tau:
            for b in range(nb):
                v = row[b] * (1.0 - rho)
                row[b] = v if v > tau_min else tau_min
        src = best_seq if rng.random() < 0.6 else it_best[1]
        for pos, j in enumerate(src):
            b = pos // bucket
            v = tau[j][b] + rho
            tau[j][b] = v if v < tau_max else tau_max

    if best_c < base_c and _cost(jobs, best_trail) < base_c:
        return best_trail
    return base
