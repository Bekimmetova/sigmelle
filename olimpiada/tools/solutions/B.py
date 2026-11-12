import sys, heapq, bisect
from collections import deque
MOD = 10**9 + 7

def solve_B(inp):
    s = inp.split()[0]
    return str(sum(1 for i in range(len(s) // 2) if s[i] != s[-1 - i]))


print(solve_B(sys.stdin.read()))
