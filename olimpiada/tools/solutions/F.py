import sys, heapq, bisect
from collections import deque
MOD = 10**9 + 7

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


print(solve_F(sys.stdin.read()))
