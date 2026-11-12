import sys, heapq, bisect
from collections import deque
MOD = 10**9 + 7

def solve_H(inp):
    t = list(map(int, inp.split()))
    n, m = t[0], t[1]
    adj = [[] for _ in range(n + 1)]
    p = 2
    for _ in range(m):
        u, v, w = t[p], t[p + 1], t[p + 2]; p += 3
        adj[u].append((v, w)); adj[v].append((u, w))
    INF = float("inf")
    d = [INF] * (n + 1); d[1] = 0
    pq = [(0, 1)]
    while pq:
        du, u = heapq.heappop(pq)
        if du > d[u]: continue
        for v, w in adj[u]:
            if du + w < d[v]:
                d[v] = du + w; heapq.heappush(pq, (d[v], v))
    return str(d[n]) if d[n] < INF else "-1"


print(solve_H(sys.stdin.read()))
