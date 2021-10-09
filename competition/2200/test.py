#!/usr/bin/env python3
#n = input()
#a = list(map(int, input().split()))

a = [i for i in range(50,101)]
ans = 0
sums = []
for i in range(len(a)):
    for j in range(i + 1, len(a)):
        sums.append(a[i] + a[j])

for s in sums:
    ans = ans ^ s
print(ans)
