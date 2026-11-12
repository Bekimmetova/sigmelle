import sys, heapq, bisect
from collections import deque
MOD = 10**9 + 7

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


print(solve_E(sys.stdin.read()))
