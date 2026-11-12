import sys, heapq, bisect
from collections import deque
MOD = 10**9 + 7

def solve_G(inp):
    lines = inp.split("\n")
    n, m = map(int, lines[0].split())
    g = lines[1:1 + n]
    for i in range(n):
        j = g[i].find("S")
        if j >= 0: s = (i, j)
        j = g[i].find("F")
        if j >= 0: f = (i, j)
    dist = [[-1] * m for _ in range(n)]
    dist[s[0]][s[1]] = 0
    dq = deque([s])
    while dq:
        x, y = dq.popleft()
        if (x, y) == f: break
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < n and 0 <= ny < m and g[nx][ny] != "#" and dist[nx][ny] < 0:
                dist[nx][ny] = dist[x][y] + 1
                dq.append((nx, ny))
    return str(dist[f[0]][f[1]])


print(solve_G(sys.stdin.read()))
