def solve(values, weights, capacities):
    """Greedy by value per unit of capacity-scaled weight; take every item that still fits."""
    d = len(capacities)

    def density(i):
        load = sum(weights[i][k] / capacities[k] for k in range(d))
        return values[i] / load if load > 0 else float("inf")

    order = sorted(range(len(values)), key=lambda i: (-density(i), i))
    left = list(capacities)
    chosen = []
    for i in order:
        if all(weights[i][k] <= left[k] for k in range(d)):
            for k in range(d):
                left[k] -= weights[i][k]
            chosen.append(i)
    return chosen
