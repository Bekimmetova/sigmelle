import sys, heapq, bisect
from collections import deque
MOD = 10**9 + 7

def solve_D(inp):
    t = list(map(int, inp.split()))
    n = t[0]; a = t[1:1 + n]
    best = cur = a[0]
    for x in a[1:]:
        cur = max(x, cur + x)
        best = max(best, cur)
    return str(best)


print(solve_D(sys.stdin.read()))
