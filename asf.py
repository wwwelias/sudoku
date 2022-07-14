from itertools import combinations as combin
from itertools import permutations


a = [{'A1', 'A2'}, {'A3', 'A2', 'A4'}, {'A1', 'A2'}, {'A5', 'A6'}, {'A1', 'A5', 'A6'}, {'A5', 'A6'}]
g = {'A1': {1, 3, 4}, 'A2': {1, 2, 3, 4}}

n = 2
cs = set([])
ds = []
for b in range(1, 5):
    if len(a[b]) == n:
        cs.update(a[b])
        ds.append(b)
#u = set.intersection(*Ns[0])
#y = [b[x] for x in u]
#d = set.intersection()
print(cs)
print(ds)
cs, ds = set([]), []
for i in range(len(a)):
    if 1 < len(a[i]) <= n:
        cs.update(a[i])
        ds.append(i+1)
if len(cs) and len(ds) == n:
    print("2 cells")
else:
    print("multiple cells")
    combs = list(combin(ds, n))
    for comb in combs:
        combs.pop()
        if len(set.intersection(*[a[d] for d in comb])) == n:
            print(comb)

#print(u)