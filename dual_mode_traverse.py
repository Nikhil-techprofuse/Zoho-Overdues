"""
Dual-Mode Traverse
------------------
You operate an energy harvester along array a[1..n] (left to right).
Start at position 1 in Collect mode (Heat = 0).

At each position i, perform your current mode's action:
  - Collect mode : gain a[i], Heat += 1
  - Skip mode    : gain 0,    Heat  = 0

Before moving to i+1 you MAY switch modes (Collect↔Skip), costing s each time.
If Heat reaches k after collecting at position i you are FORCED to switch to
Skip for position i+1 (still paying s).

Find the maximum net profit (total gain - total switch cost) modulo 10^9+7.

Input
-----
Line 1 : n   (size of array,  1 ≤ n ≤ 10^5)
Line 2 : k   (max consecutive collect positions, 1 ≤ k ≤ 10^2)
Line 3 : s   (switch cost,    1 ≤ s ≤ 10^9)
Line 4 : n space-separated integers  a[1..n]  (-10^9 ≤ a[i] ≤ 10^9)

Output
------
Single integer: maximum net profit modulo 10^9+7.
"""

import sys

def solve():
    data = sys.stdin.read().split()
    idx = 0
    n = int(data[idx]); idx += 1
    k = int(data[idx]); idx += 1
    s = int(data[idx]); idx += 1
    a = [int(data[idx + i]) for i in range(n)]

    MOD = 10**9 + 7
    NEG_INF = float('-inf')

    # DP states after processing each position:
    #   C[h]  = max profit, currently in Collect mode, Heat counter = h  (1..k)
    #   S     = max profit, currently in Skip mode,    Heat counter = 0
    C = [NEG_INF] * (k + 2)
    S = NEG_INF

    # Position 1: always start in Collect mode → gain a[0], Heat becomes 1
    C[1] = a[0]

    for i in range(1, n):          # transition into position i+1 (0-indexed a[i])
        new_C = [NEG_INF] * (k + 2)
        new_S = NEG_INF

        # ── transitions from Collect states ──────────────────────────────────
        for h in range(1, k + 1):
            if C[h] == NEG_INF:
                continue

            if h < k:
                # Voluntary: stay in Collect → gain a[i], Heat = h+1
                val = C[h] + a[i]
                if val > new_C[h + 1]:
                    new_C[h + 1] = val

                # Voluntary: switch to Skip → pay s, gain 0, Heat = 0
                val = C[h] - s
                if val > new_S:
                    new_S = val

            else:  # h == k: FORCED switch to Skip
                val = C[h] - s
                if val > new_S:
                    new_S = val

        # ── transitions from Skip state ───────────────────────────────────────
        if S != NEG_INF:
            # Stay in Skip → gain 0, Heat stays 0
            if S > new_S:
                new_S = S

            # Voluntary: switch to Collect → pay s, gain a[i], Heat = 1
            val = S - s + a[i]
            if val > new_C[1]:
                new_C[1] = val

        C = new_C
        S = new_S

    # Best answer across all final states
    ans = S if S != NEG_INF else NEG_INF
    for h in range(1, k + 1):
        if C[h] != NEG_INF and C[h] > ans:
            ans = C[h]

    print(ans % MOD)


solve()
