import sys, heapq, bisect
from collections import deque
MOD = 10**9 + 7

def solve_A(inp):
    t = inp.split()
    n = int(t[0]); a = list(map(int, t[1:1 + n]))
    return str(sum(x for x in a if x % 2 == 0))


print(solve_A(sys.stdin.read()))
