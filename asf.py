import time
from itertools import combinations as combin
from itertools import permutations


a = [{'A1', 'A2', 'A7'}, {'A3', 'A2', 'A4'}, {'A1', 'A2', 'A7'}, {'A5', 'A6', 'A9'}, {'A1', 'A5', 'A7' 'A6'}, {'A5', 'A6', 'A9'}, {'A1', 'A2', 'A7'}, {'A5', 'A6', 'A9'}]
g = {'A1': {1, 3, 4}, 'A2': {1, 2, 3, 4}}

n = 3
cs = set([])
ds = []
for b in range(1, 5):
    if len(a[b]) == n:
        cs.update(a[b])
        ds.append(b)
#u = set.intersection(*Ns[0])
#y = [b[x] for x in u]
#d = set.intersection()
cs, ds = set([]), []
for i in range(len(a)):
    if 1 < len(a[i]) <= n:
        cs.update(a[i])
        ds.append(i+1)
if len(cs) and len(ds) == n:
    print("2 cells")
else:
    print("multiple cells")
    print(list(combin(ds, n)))
    for comb in combin(ds, n):
        shared = set.intersection(*[a[d - 1] for d in comb])
        if len(shared) == n:
            print(shared, comb)


ok =[[1, 2, 3, 4, 5, 6, 7, 8, 9],
 [2, 3, 4, 5, 6, 7, 8, 9, 1]]



"""
sudoku = Sudoku()
print(sudoku.board[0][0].possibilities)
sudoku.board[0][1].value = 5
sudoku.display(bo=sudoku.board)
sudoku.display(sudoku.getColumns())
sudoku.getColumns()[0][1].value = 9
sudoku.display(bo=sudoku.board)

sudoku.display(bo=sudoku.getBoxes())
units = sudoku.getUnits(5, 5)
bla = set(sum(units, []))
peers = bla - {sudoku.board[5][5]}
print(' '.join(str(p.value) for p in peers))
print()
for comb in combin(sudoku.getBoxes()[4], 8):
    print(' '.join(str(d) for d in [s.value for s in comb]))

"""