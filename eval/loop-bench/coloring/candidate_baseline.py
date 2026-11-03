def color(n, edges):
    """Largest degree first: each node takes the smallest colour none of its neighbours has."""
    adj = [[] for _ in range(n)]
    for u, v in edges:
        adj[u].append(v)
        adj[v].append(u)
    colors = [-1] * n
    for u in sorted(range(n), key=lambda u: (-len(adj[u]), u)):
        taken = {colors[v] for v in adj[u]}
        c = 0
        while c in taken:
            c += 1
        colors[u] = c
    return colors
