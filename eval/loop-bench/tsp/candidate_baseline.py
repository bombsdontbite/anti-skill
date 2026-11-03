import math


def solve(points):
    """Nearest neighbour from city 0."""
    left = set(range(1, len(points)))
    tour = [0]
    while left:
        cur = points[tour[-1]]
        nxt = min(left, key=lambda j: (math.dist(cur, points[j]), j))
        left.remove(nxt)
        tour.append(nxt)
    return tour
