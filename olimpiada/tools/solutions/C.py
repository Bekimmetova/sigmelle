import sys, heapq, bisect
from collections import deque
MOD = 10**9 + 7

def solve_C(inp):
    import bisect
    t = list(map(int, inp.split()))
    n = t[0]; a = sorted(t[1:1 + n]); q = t[1 + n]
    return "\n".join(str(bisect.bisect_right(a, x)) for x in t[2 + n:2 + n + q])


print(solve_C(sys.stdin.read()))
