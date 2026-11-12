"""
Olimpiada testlarini generatsiya qilish skripti.
Ishlatish:  python3 tools/gen_tests.py
Har bir masala uchun problems/<ID>/tests/NN.in va NN.out fayllarini yaratadi.
Javoblar shu fayldagi etalon (to'g'ri) yechimlar bilan hisoblanadi.
"""
import os, random, heapq, sys
from collections import deque

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "problems")
MOD = 10**9 + 7


def write_tests(pid, tests, solve):
    d = os.path.join(ROOT, pid, "tests")
    os.makedirs(d, exist_ok=True)
    for f in os.listdir(d):
        os.remove(os.path.join(d, f))
    for i, inp in enumerate(tests, 1):
        out = solve(inp)
        with open(os.path.join(d, f"{i:02d}.in"), "w") as f:
            f.write(inp)
        with open(os.path.join(d, f"{i:02d}.out"), "w") as f:
            f.write(out + "\n")
    print(f"{pid}: {len(tests)} ta test")


# ---------------- A. Juft sonlar yig'indisi ----------------
def solve_A(inp):
    t = inp.split()
    n = int(t[0]); a = list(map(int, t[1:1 + n]))
    return str(sum(x for x in a if x % 2 == 0))

def gen_A(r):
    tests = ["5\n1 2 3 4 5\n", "4\n-4 7 -3 10\n"]
    for n, lo, hi in [(1, 1, 1), (1, -6, -6), (10, -20, 20), (100, -1000, 1000),
                      (1000, -10**9, 10**9), (100000, 1, 10**9), (100000, -10**9, 10**9),
                      (100000, -10**9, -1)]:
        a = [r.randint(lo, hi) for _ in range(n)]
        tests.append(f"{n}\n{' '.join(map(str, a))}\n")
    a = [10**9] * 100000  # katta yig'indi: long long kerak
    tests.append(f"100000\n{' '.join(map(str, a))}\n")
    a = [-(10**9)] * 100000
    tests.append(f"100000\n{' '.join(map(str, a))}\n")
    return tests


# ---------------- B. Palindrom ----------------
def solve_B(inp):
    s = inp.split()[0]
    return str(sum(1 for i in range(len(s) // 2) if s[i] != s[-1 - i]))

def gen_B(r):
    tests = ["abca\n", "kiyik\n"]
    def rnd(n, k): return "".join(r.choice("abcdefghijklmnopqrstuvwxyz"[:k]) for _ in range(n))
    tests += ["a\n", "ab\n", rnd(10, 2) + "\n", rnd(100, 3) + "\n", rnd(1000, 26) + "\n"]
    h = rnd(50000, 26); tests.append(h + h[::-1] + "\n")
    h = rnd(50000, 26); tests.append(h + "x" + h[::-1] + "\n")
    tests.append(rnd(100000, 26) + "\n")
    tests.append(rnd(99999, 2) + "\n")
    tests.append("a" * 50000 + "b" * 50000 + "\n")
    return tests


# ---------------- C. Kitob do'koni (binar qidiruv) ----------------
def solve_C(inp):
    import bisect
    t = list(map(int, inp.split()))
    n = t[0]; a = sorted(t[1:1 + n]); q = t[1 + n]
    return "\n".join(str(bisect.bisect_right(a, x)) for x in t[2 + n:2 + n + q])

def gen_C(r):
    tests = ["5\n30 10 50 20 40\n4\n25 5 50 100\n", "3\n7 7 7\n3\n6 7 8\n"]
    for n, q, hi in [(1, 1, 10), (10, 10, 20), (100, 100, 1000), (1000, 1000, 10**9),
                     (200000, 200000, 10**9), (200000, 200000, 100), (200000, 200000, 10**9)]:
        a = [r.randint(1, hi) for _ in range(n)]
        x = [r.randint(1, hi) for _ in range(q)]
        tests.append(f"{n}\n{' '.join(map(str, a))}\n{q}\n{' '.join(map(str, x))}\n")
    n = 200000; a = [10**9] * n; x = [10**9 - 1, 10**9] * (n // 2)
    tests.append(f"{n}\n{' '.join(map(str, a))}\n{n}\n{' '.join(map(str, x))}\n")
    return tests


# ---------------- D. Eng foydali davr (Kadane) ----------------
def solve_D(inp):
    t = list(map(int, inp.split()))
    n = t[0]; a = t[1:1 + n]
    best = cur = a[0]
    for x in a[1:]:
        cur = max(x, cur + x)
        best = max(best, cur)
    return str(best)

def gen_D(r):
    tests = ["8\n-2 1 -3 4 -1 2 1 -5\n", "3\n-5 -2 -7\n"]
    for n, lo, hi in [(1, -10, 10), (5, -10, 10), (50, -100, 100), (1000, -10**6, 10**6),
                      (5000, -10**9, 10**9), (200000, -10**9, 10**9), (200000, -10**9, -1),
                      (200000, -10**9, 10**9)]:
        a = [r.randint(lo, hi) for _ in range(n)]
        tests.append(f"{n}\n{' '.join(map(str, a))}\n")
    a = [10**9] * 200000
    tests.append(f"200000\n{' '.join(map(str, a))}\n")
    return tests


# ---------------- E. Zinapoya (DP) ----------------
def solve_E(inp):
    t = list(map(int, inp.split()))
    n, k = t[0], t[1]
    broken = set(t[2:2 + k])
    dp = [0] * (n + 1); dp[0] = 1
    for i in range(1, n + 1):
        if i in broken: continue
        v = dp[i - 1]
        if i >= 2: v += dp[i - 2]
        if i >= 3: v += dp[i - 3]
        dp[i] = v % MOD
    return str(dp[n])

def gen_E(r):
    tests = ["4 0\n\n", "5 1\n3\n"]
    def mk(n, k):
        b = sorted(r.sample(range(1, n), min(k, n - 1))) if n > 1 else []
        return f"{n} {len(b)}\n{' '.join(map(str, b))}\n"
    tests += ["1 0\n\n", mk(10, 2), mk(30, 0), mk(40, 5), "6 3\n2 3 4\n",
              mk(1000, 50), mk(100000, 1000), mk(1000000, 0), mk(1000000, 100000),
              mk(1000000, 10)]
    return tests


# ---------------- F. Ryukzak (0/1 knapsack) ----------------
def solve_F(inp):
    t = list(map(int, inp.split()))
    n, W = t[0], t[1]
    dp = [0] * (W + 1)
    for i in range(n):
        w, v = t[2 + 2 * i], t[3 + 2 * i]
        for c in range(W, w - 1, -1):
            if dp[c - w] + v > dp[c]:
                dp[c] = dp[c - w] + v
    return str(dp[W])

def gen_F(r):
    tests = ["3 50\n10 60\n20 100\n30 120\n", "2 5\n6 100\n5 7\n"]
    for n, W, wmax, vmax in [(1, 10, 20, 100), (5, 20, 10, 50), (15, 100, 40, 1000),
                             (20, 1000, 300, 10**6), (100, 20000, 20000, 10**9),
                             (100, 20000, 1000, 10**9), (100, 20000, 400, 10**9),
                             (100, 1, 2, 10)]:
        lines = [f"{n} {W}"] + [f"{r.randint(1, wmax)} {r.randint(1, vmax)}" for _ in range(n)]
        tests.append("\n".join(lines) + "\n")
    return tests


# ---------------- G. Labirint (BFS) ----------------
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

def gen_G(r):
    tests = ["4 5\nS..#.\n.#...\n.#.#.\n...#F\n", "3 3\nS#.\n##.\n..F\n"]
    def rnd(n, m, p):
        g = [["#" if r.random() < p else "." for _ in range(m)] for _ in range(n)]
        cells = r.sample(range(n * m), 2)
        g[cells[0] // m][cells[0] % m] = "S"; g[cells[1] // m][cells[1] % m] = "F"
        return f"{n} {m}\n" + "\n".join("".join(row) for row in g) + "\n"
    def snake(n, m):  # ilon shaklidagi uzun yo'l
        g = [["." for _ in range(m)] for _ in range(n)]
        for i in range(1, n, 2):
            for j in range(m): g[i][j] = "#"
            g[i][m - 1 if (i // 2) % 2 == 0 else 0] = "."
        g[0][0] = "S"; g[n - 1][m - 1 if ((n - 1) // 2) % 2 == 0 else 0] = "F"
        return f"{n} {m}\n" + "\n".join("".join(row) for row in g) + "\n"
    tests += ["1 2\nSF\n", rnd(5, 5, 0.2), rnd(20, 30, 0.3), rnd(100, 100, 0.3),
              rnd(1000, 1000, 0.2), rnd(1000, 1000, 0.45), rnd(1000, 1000, 0.0),
              snake(999, 1000), snake(1000, 3)]
    return tests


# ---------------- H. Shaharlar (Dijkstra) ----------------
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

def gen_H(r):
    tests = ["4 4\n1 2 5\n2 4 3\n1 3 2\n3 4 10\n", "3 1\n1 2 7\n"]
    def rnd(n, m, wmax, connected=True):
        edges = []
        if connected:
            perm = list(range(2, n + 1)); r.shuffle(perm); perm = [1] + perm
            for i in range(1, n):
                edges.append((perm[r.randint(max(0, i - 5), i - 1)], perm[i], r.randint(1, wmax)))
        while len(edges) < m:
            u, v = r.randint(1, n), r.randint(1, n)
            if u != v: edges.append((u, v, r.randint(1, wmax)))
        r.shuffle(edges)
        return f"{n} {len(edges)}\n" + "\n".join(f"{u} {v} {w}" for u, v, w in edges) + "\n"
    def chain(n):  # uzun zanjir + "aldamchi" qisqa, lekin og'ir yo'llar
        edges = [(i, i + 1, 1) for i in range(1, n)]
        edges += [(1, r.randint(2, n), 10**9) for _ in range(n)]
        return f"{n} {len(edges)}\n" + "\n".join(f"{u} {v} {w}" for u, v, w in edges) + "\n"
    def chain_rev(n):  # Bellman-Ford'ga qarshi: qirralar teskari tartibda
        perm = list(range(2, n)); r.shuffle(perm); order = [1] + perm + [n]
        edges = [(order[i + 1], order[i], r.randint(1, 10)) for i in range(n - 2, -1, -1)]
        edges += [(r.randint(1, n), r.randint(1, n), 10**9) for _ in range(n)]
        edges = [e for e in edges if e[0] != e[1]]
        return f"{n} {len(edges)}\n" + "\n".join(f"{u} {v} {w}" for u, v, w in edges) + "\n"
    tests += ["1 0\n", "2 1\n1 2 1000000000\n", rnd(10, 15, 20), rnd(100, 300, 1000),
              rnd(1000, 5000, 10**9), rnd(100000, 200000, 10**9), rnd(100000, 200000, 10),
              chain(100000), chain_rev(100000), chain_rev(99999), rnd(100000, 199999, 10**9, connected=False)]
    return tests


if __name__ == "__main__":
    sys.setrecursionlimit(10000)
    r = random.Random(2026)
    for pid, gen, sol in [("A", gen_A, solve_A), ("B", gen_B, solve_B), ("C", gen_C, solve_C),
                          ("D", gen_D, solve_D), ("E", gen_E, solve_E), ("F", gen_F, solve_F),
                          ("G", gen_G, solve_G), ("H", gen_H, solve_H)]:
        write_tests(pid, gen(r), sol)
