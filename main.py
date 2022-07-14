import collections
import time
from itertools import combinations as combin
from microbench import MicroBench


class MyBench(MicroBench):
    outfile = 'C:\\Users\\Praktikant-Buers\\Documents\\Wohlgenannt\\tests\\trashdump.json' #for testing change to test.json


basic_bench = MyBench()


# region setup
def cross(A, B):
    "Cross product of elements in A and elements in B."
    return [a + b for a in A for b in B]


def setup():
    _digits = '123456789'
    _rows = 'ABCDEFGHI'
    _cols = _digits
    _squares = cross(_rows, _cols)
    _rowunits = [cross(_rows, c) for c in _cols]
    _columnunits = [cross(r, _cols) for r in _rows]
    _boxes = [cross(rs, cs) for rs in ('ABC', 'DEF', 'GHI') for cs in ('123', '456', '789')]
    _unitlist = (_rowunits + _columnunits + _boxes)
    _units = dict((s, [u for u in _unitlist if s in u])
                  for s in _squares)
    _peers = dict((s, set(sum(_units[s], [])) - {s})
                  for s in _squares)
    _possibles = dict((s, {n for n in range(1, 10)}) for s in _squares)

    _sudoku = dict((s, 0) for s in _squares)

    _foundNakedNs = [set([]), set([]), set([])]  # pairs / triples / quads

    return _rows, _cols, _squares, _rowunits, _columnunits, _boxes, _unitlist, _units, _peers, _possibles, _sudoku, _foundNakedNs


# endregion


def printError(code):
    if code == 'c':
        print('Contradiction detected')
    elif code == 'w':
        print('Sudoku has been solved wrongly')
    exit()


# remove digit from possible digits of peers
def removePeersPossibles(cells, possibles, digits):
    removedPossibles = False
    for cell in cells:
        for digit in digits:
            if digit in possibles[cell]:
                possibles[cell].remove(digit)
                removedPossibles = True
    return removedPossibles


def removeCellsPossibles(cells, possibles, digits):
    removedPossibles = False
    for cell in cells:
        for digit in possibles[cell]:
            if digit not in digits:
                possibles[cell].remove(digit)
                removedPossibles = True
    return removedPossibles


# fill cell if digit is valid
def fillCell(board, cell, digit, possibles):
    if digit in possibles[cell]:
        board[cell] = digit
        possibles[cell].clear()
        removePeersPossibles(peers[cell], possibles, [digit])
        global cycleCounter
        cycleCounter = 0
        return
    printError('c')


def checkSolvedCells(board, possibles):
    filledCells = False
    for s in squares:
        if len(possibles[s]) == 1:
            fillCell(board, s, next(iter(possibles[s])), possibles)
            filledCells = True
    return filledCells


def getPossiblesOfUnit(unit, possibles):
    possiblesOfUnit = []
    for s in unit:
        possiblesOfUnit.extend(possibles[s])
    return possiblesOfUnit


def hiddenSingle(board, cell, possibles):
    for unit in units[cell]:
        possiblesOfUnit = getPossiblesOfUnit(unit, possibles)
        for p in possibles[cell]:
            if possiblesOfUnit.count(p) == 1:
                fillCell(board, cell, p, possibles)
                return True
    return False


def hiddenSingles(board, possibles):
    foundSingles = False
    for s in squares:
        if len(possibles[s]) >= 2:
            if hiddenSingle(board, s, possibles): foundSingles = True
    return foundSingles


def hiddenSingles2(board, possibles):
    foundSingles = False
    for unit in unitlist:
        u = [c for c in unit if board[c] == 0]
        if len(u) == 0: continue
        possiblesOfUnit = getPossiblesOfUnit(u, possibles)
        countedPossibles = collections.Counter(possiblesOfUnit).most_common()
        digit, rate = countedPossibles.pop()
        while rate == 1:
            fillCell(board, [cell for cell in u if digit in possibles[cell]].pop(), digit, possibles),
            foundSingles = True
            digit, rate = countedPossibles.pop() if len(countedPossibles) > 0 else 0, 0
    return foundSingles


def nakedN1(possibles, n):
    foundShared = False
    # alreadyFound = [c for c in [foundNakedNs[m] for m in range(n - 1)]]
    for s in squares:
        if 1 < len(possibles[s]) <= n and s not in foundNakedNs[n - 2]:
            for unit in units[s]:
                sharedPossibles = possibles[s].copy()
                sharedCells = {s}
                for cell in unit:
                    if cell != s and (possibles[cell] & sharedPossibles):
                        if len(possibles[cell].union(sharedPossibles)) > n: continue
                        sharedPossibles.update(possibles[cell])
                        sharedCells.add(cell)
                        if len(sharedPossibles) == n and len(sharedCells) == n:
                            foundNakedNs[n - 2].update(sharedCells)
                            if removePeersPossibles(set(unit) - sharedCells, possibles, sharedPossibles):
                                foundShared = True
                            break
    return foundShared


def nakedN2(possibles, n):
    foundShared = False
    sharedPossibles = set([])
    for unit in unitlist:
        for comb in combin([c for c in unit if 1 < len(possibles[c]) <= n and c not in foundNakedNs[n - 2]], n):
            sharedPossibles.clear()
            sharedPossibles = set(sum([list(possibles[c]) for c in comb], []))
            if len(sharedPossibles) == n:
                if removePeersPossibles(set(unit) - set(comb), possibles, sharedPossibles):
                    foundNakedNs[n - 2].update(sharedPossibles)
                    foundShared = True
                    break
    return foundShared


def hiddenN(possibles, n):
    foundHiddenN = False
    digits = range(9)
    for unit in unitlist:
        values = [set([]) for i in digits]
        for cell in unit:
            for digit in possibles[cell]:
                values[digit-1].update(cell)
        cs, ds = set([]), []
        for i in digits:
            if 1 < len(values[i]) <= n:
                cs.update(values[i])
                ds.append(i+1)
        if len(cs) and len(ds) == n:
            if removeCellsPossibles(cs, possibles, ds): foundHiddenN = True
        else
    return foundHiddenN


# region BACKTRACKING
def find_empty_square(board):
    for s in squares:
        if board[s] == 0:
            return s  # square
    return None


def backTrack(board, possibles):
    s = find_empty_square(board)
    if not s:
        return True

    for i in possibles[s]:
        if valid(board, i, s):
            board[s] = i

            if backTrack(board, possibles):
                return True

            board[s] = 0
    return False


def valid(board, num, pos):
    for p in peers[pos]:
        if board[p] == num:
            return False
    return True


# endregion


# region checking if sudoku got solved correctly
def checkUnit(unit, board):
    unitCorrect = True
    sumunit = 0
    for s in unit:
        sumunit += board[s]
    if sumunit != 45: unitCorrect = False
    return unitCorrect


def checkSudoku(board):
    if all(checkUnit(row, board) for row in rowunits) and all(
            checkUnit(column, board) for column in columnunits) and all(
        checkUnit(box, board) for box in boxes):
        return True
    return False


# endregion


def displaySudoku(board):
    "Display these values as a 2-D grid."
    width = 2
    line = '+'.join(['-' * (width * 3)] * 3)
    for r in rows:
        nums = []
        for c in cols:
            num = ''.join(str(board[r + c])).center(width)
            if c in '36':
                num += '|'
            nums.append(num)
        numline = ''.join(nums)
        print(numline)
        if r in 'CF':
            print(line)
    print()


def displayPossibles(possibles):
    "Display these values as a 2-D grid."
    width = 1 + max(len(possibles[s]) for s in squares)
    line = '+'.join(['-' * (width * 3)] * 3)
    for r in rows:
        nums = []
        for c in cols:
            num = ''.join(map(str, possibles[r + c])).center(width)
            if c in '36':
                num += '|'
            nums.append(num)
        numline = ''.join(nums)
        print(numline)
        if r in 'CF':
            print(line)
    print()


# import sudoku as string or 2D-Array
def importSudoku(board, input, possibles):
    if type(input) is not str:
        input = sum(input, [])
    # fill in sudoku
    for s, d in zip(squares, input):
        if int(d) != 0:
            fillCell(board, s, int(d), possibles)


# region testing
@basic_bench
def strategies1(sudoku, possibles):
    sudokuSolved = False
    cycleCounter = 0
    while not sudokuSolved and cycleCounter <= 5:
        if checkSolvedCells(sudoku, possibles): continue
        if hiddenSingles(sudoku, possibles): continue
        if nakedN1(possibles, 2): continue
        if nakedN1(possibles, 3): continue
        cycleCounter += 1
        sudokuSolved = max(len(possibles[s]) for s in squares) <= 1

    if not sudokuSolved: backTrack(sudoku, possibles)

    if not checkSudoku(sudoku):
        printError('w')


@basic_bench
def strategies2(sudoku, possibles):
    sudokuSolved = False
    cycleCounter = 0
    while not sudokuSolved and cycleCounter <= 5:
        if checkSolvedCells(sudoku, possibles): continue
        if hiddenSingles2(sudoku, possibles): continue
        if nakedN2(possibles, 2): continue
        if nakedN2(possibles, 3): continue
        cycleCounter += 1
        sudokuSolved = max(len(possibles[s]) for s in squares) <= 1

    if not sudokuSolved: backTrack(sudoku, possibles)

    if not checkSudoku(sudoku):
        printError('w')


@basic_bench
def backtracking(sudoku, possibles):
    backTrack(sudoku, possibles)

    if not checkSudoku(sudoku):
        printError('w')
# endregion

def solveOnce(inputString):
    rows, cols, squares, rowunits, columnunits, boxes, unitlist, units, peers, possibles, sudoku, \
    foundNakedNs = setup()

    importSudoku(sudoku, inputString, possibles)
    strategies1(sudoku, possibles)
    strategies2(sudoku, possibles)
    backtracking(sudoku, possibles)


def testing(puzzleStrings, count):
    for i in range(len(puzzleStrings)):
        print("Running sudoku nr. {0}...".format(i + 1))
        inputString = puzzleStrings[i]
        for i in range(count):
            rows, cols, squares, rowunits, columnunits, boxes, unitlist, units, peers, possibles, sudoku, \
            foundNakedNs = setup()

            importSudoku(sudoku, inputString, possibles)
            strategies1(sudoku, possibles)

        for i in range(count):
            rows, cols, squares, rowunits, columnunits, boxes, unitlist, units, peers, possibles, sudoku, \
            foundNakedNs = setup()

            importSudoku(sudoku, inputString, possibles)
            strategies2(sudoku, possibles)

        for i in range(count):
            rows, cols, squares, rowunits, columnunits, boxes, unitlist, units, peers, possibles, sudoku, \
            foundNakedNs = setup()

            importSudoku(sudoku, inputString, possibles)
            backtracking(sudoku, possibles)
    print("done.")


def main():
    global rows, cols, squares, rowunits, columnunits, boxes, unitlist, units, peers, foundNakedNs

    field = [[6, 3, 4, 2, 0, 0, 0, 0, 0],  # ------> 1, 2, 3
             [0, 0, 2, 3, 0, 0, 0, 0, 7],  # | A
             [0, 0, 0, 9, 0, 0, 0, 0, 5],  # | B
             [0, 0, 0, 0, 0, 0, 7, 3, 6],  # v C
             [0, 0, 0, 0, 2, 3, 0, 0, 0],
             [0, 4, 8, 0, 0, 0, 0, 0, 0],
             [5, 9, 0, 0, 0, 0, 0, 0, 0],
             [0, 0, 0, 0, 0, 5, 4, 1, 0],
             [0, 0, 0, 0, 3, 1, 0, 0, 0]]

    inputStrings = ["634200000002300007000900005000000736000023000048000000590000000000005410000031000",
                    "020000400060280050704000010048002030000030600600009800000060005007015002000008000",
                    "040800000501000004800009060000000000200006405090007080000010700000060200304900001",
                    "096002007100000090300060000000800003029040080010000000600000000000007500084020030",
                    "010020300004005060070000008006900070000100002030048000500006040000800106008000000",
                    "010020300002003040050000006004700050000100003070068000300004090000600104006000000",
                    "010020300002003040080000006004700030000600008070098000300004090000800104006000000",
                    "010020300002003040050000006004200050000100007020087000300004080000600105006000000",
                    "010020300002003040050000006004700050000100008070098000300004090000900804006000000",
                    "010020300004003020050000006002700050000100008070098000300007090000600102007000000",
                    "010020300002003040050000006004700050000100008070038000300005090000600104006000000",
                    "010020300004001050060000007005400060000100002080092000300005090000700106007000000",
                    "010020300003004050060000007005800060000100009080092000400005090000700106007000000",
                    "010020300004003050050000006005700040000100002070082000300005090000600105006000000",
                    "010020300002003040050000006004700050000100008070068000300004060000500104009000000",
                    "010020300002003040050000006004700050000100008070095000300004090000900104006000000",
                    "010020300004005060070000008006300070000100002030092000900006040000800106008000000",
                    "080070100003002090060000004009500060000700005020041000100005020000200901004000000",
                    "010020300002003040040000006004700050000600008070098000300005080000800104009000000",
                    "020010700003008060010000003008600050000900004030021000400009080000500901007000000",
                    "010020300003004050060000007005800060000100002080072000400005090000700104007000000",
                    "010020300002003040050000006007800050000100004080094000300007090000400105006000000",
                    "010020300004003020050000006007600050000100002060072000300008070000900108009000000",
                    "010020300004003050060000007005800060000900001080012000300005010000700506002000000",
                    "010020300004003050020000006005700020000100008070098000300005090000900205006000000",
                    "010020300004003020050000006007800050000100002080042000300007040000600807006000000",
                    "070050800005008020010000009008100050000200001090034000900002030000600107006000000",
                    "010020300004005060070000004006800070000900002050017000400006050000400906008000000",
                    "010020300004005060070000008006900080000100002090032000200006030000800105008000000",
                    "010020300002003040050000006004700050000100008070098000200004090000600704006000000",
                    "010020300002003040050000006004700050000100008070068000300004090000800104006000000",
                    "010020300004001050060000007005800070000900002080014000300005010000700905007000000",
                    "010020300004003020050000006002700050000800009070019000300002010000600805006000000",
                    "010020300003004050060000007008900070000100002090082000200005080000700105007000000",
                    "010020300004003050020000006007800040000100005080095000300007090000600107006000000",
                    "010020300002003040050000006004700080000100003070068000300004090000600104006000000",
                    "090020500004005010060000003001800060000900002080072000500001070000300901003000000",
                    "010020300004001050060000007005800060000100003080092000300005090000700102007000000",
                    "010020300002003040050000006004700050000100008020098000700004090000600104006000000",
                    "010020300003004050060000004005700060000100002070032000400005080000900105009000000",
                    "010020300004003050060000007005800040000100002080092000600005090000700105002000000",
                    "010020300004003050060000007005100060000800002080092000300006090000700205007000000",
                    "010020300004005060070000008006900030000100002090042000500006040000800106008000000",
                    "010020300004003050060000007005200060000100008020048000300005090000700205009000000",
                    "070040800009005060060000003004100070000200006020034000100008090000600401007000000",
                    "010020300004001050060000007005200060000800009020019000300005010000700805007000000",
                    "010020300004003050060000007005200040000800001020091000300005090000700805007000000",
                    "010020300004001050060000007005800060000900002080014000300005010000700905007000000",
                    "010020300004003050060000007005800060000100002070092000400005090000700105007000000",
                    "010020300004005060050000004006700040000100002070082000300006080000900106009000000",
                    "010020300004003050020000006005700080000100002070098000800005090000600105006000000",
                    "010020300004003050060000007005800040000100008080092000300005090000700605007000000",
                    "010020300004005060070000008006900040000100002090032000500006030000800906008000000",
                    "010020300004003050060000007005800060000100002070092000300005090000700105007000000",
                    "010020300002003040050000006004700050000600008070098000300004090000800104006000000",
                    "010020300004003050060000007005800060000100009080042000300005040000700908001000000",
                    "070060900006002030020000006003100040000200008050034000900003020000700105008000000",
                    "010020300004003050060000001005700060000800002070012000400005090000400805007000000",
                    "000943000060010050000000000800000003750060014100000009000000000020050080000374000",
                    "000123000040050060000000000700000003860040092900000001000000000050060080000392000",
                    "000123000040050060000000000700000003860040072500000001000000000070060050000382000",
                    "000123000040050060000000000500000007360040052700000001000000000080060040000732000",
                    "000123000040050060000000000100000003760040082500000009000000000090060040000378000",
                    "000123000040050060000000000700000003460080052500000001000000000090060040000392000",
                    "000427000060090080000000000900000008120030045500000007000000000040060030000715000",
                    "000123000040050060000000000200000003760040082400000001000000000080060030000372000",
                    "000123000040050060000000000100000003360040052200000007000000000080060040000972000",
                    "000123000040050060000000000800000007460080052200000001000000000050060040000731000",
                    "000123000040050060000000000100000003760080052800000009000000000080060040000372000",
                    "000651000040020080000000000700000009120030045800000001000000000030040020000719000",
                    "000398000050010060000000000800000009120030045700000008000000000040020010000769000",
                    "000123000040050060000000000200000003570040082100000006000000000060070040000392000",
                    "000123000040050060000000000700000008810040027500000003000000000090060040000387000",
                    "000123000040050060000000000400000003560040072700000001000000000080060040000372000",
                    "000123000040050060000000000700000003460080052500000001000000000070060040000394000",
                    "000123000040050060000000000200000007760040082300000001000000000090080040000376000",
                    "000123000040050060000000000100000003560040072800000009000000000070060040000382000",
                    "000427000010090080000000000700000005120030046800000002000000000040060090000715000",
                    "000398000050020060000000000800000009620050041700000008000000000040060020000419000",
                    "000123000040050060000000000500000003760040052400000001000000000080060040000372000",
                    "000758000040060010000000000700000008120030045600000009000000000030010090000826000",
                    "000123000040050060000000000100000003760080041800000009000000000080060090000372000",
                    "000123000040050060000000000200000007360040052400000001000000000080060040000712000",
                    "000123000040050060000000000100000003260070081900000002000000000080060040000294000",
                    "000123000040050060000000000700000006360040082200000001000000000080060040000732000",
                    "000123000040050010000000000200000006670040052800000003000000000050010040000862000",
                    "000123000040050010000000000200000006630040072800000003000000000050010040000862000",
                    "000123000040050060000000000500000003360040057700000001000000000080060040000237000",
                    "000123000040050060000000000400000003760040052500000008000000000070090040000312000",
                    "000123000040050060000000000200000007760040082500000001000000000090080040000372000",
                    "000123000040050060000000000200000007760080092500000001000000000080060040000372000",
                    "000123000040050060000000000200000007780040092500000001000000000050090040000372000",
                    "000716000030050020000000000700000006120030045500000001000000000090040080000182000"]
    inputString = ''
    testCount = 5

    solveOnce(inputString)
    #testing(inputStrings, testCount)
    exit()


if __name__ == "__main__":
    main()
