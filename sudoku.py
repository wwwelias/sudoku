import collections
import time
import pyads
import atexit
from itertools import combinations as combin
from copy import deepcopy
from microbench import MicroBench


class MyBench(MicroBench):
    outfile = 'C:\\Users\\Praktikant-Buers\\Documents\\Wohlgenannt\\tests\\trashdump.json' #for testing change to test.json


basic_bench = MyBench()

global plc


class Sudoku:
    boxCombinations = []
    for rows in ([0, 1, 2], [3, 4, 5], [6, 7, 8]):
        for columns in ([0, 1, 2], [3, 4, 5], [6, 7, 8]):
            boxCombinations.append((rows, columns))

    def __init__(self, n=9):
        self.board = [[Square(r, c) for c in range(n)] for r in range(n)]
        self.n = n
        self.filledSquares = 0
        self.columns = [[self.board[r][c] for r in range(self.n)] for c in range(self.n)]
        self.pairs = set([])
        boxes = []
        for i in range(self.n):
            rs, cs = self.boxCombinations[i]
            boxes.append([])
            for r in rs:
                for c in cs:
                    boxes[i].append(self.board[r][c])
        self.boxes = boxes

    def getRows(self):
        return self.board

    def getColumns(self):
        return self.columns

    def getBoxes(self):
        return self.boxes

    def getUnitList(self):
        return self.board + self.columns + self.boxes

    def getUnits(self, square):
        box = int(square.row / 3) * 3 + int(square.column / 3)
        return [self.board[square.row], self.columns[square.column], self.boxes[box]]

    def getPeers(self, square):
        units = self.getUnits(square)
        return set(sum(units, [])) - {self.board[square.row][square.column]}

    def display(self, bo):
        width = 3
        line = '+'.join(['-' * 3 * width]*3)
        for r in range(self.n):
            nums = []
            for c in range(self.n):
                num = str(bo[r][c].value).center(width)
                if c in [2, 5]:
                    num += '|'
                nums.append(num)
            numline = ''.join(nums)
            print(numline)
            if r in [2, 5]:
                print(line)
        print()

    def displayPossibles(self):
        width = 2 + max([len(self.board[r][c].possibles) for c in range(9) for r in range(9)])
        line = '+'.join(['-' * 3 * width]*3)
        for r in range(self.n):
            nums = []
            for c in range(self.n):
                num = str(''.join(str(d) for d in self.board[r][c].possibles)).center(width)
                if c in [2, 5]:
                    num += '|'
                nums.append(num)
            numline = ''.join(nums)
            print(numline)
            if r in [2, 5]:
                print(line)
        print()


class Square:
    def __init__(self, row, column):
        self.row = row
        self.column = column
        self.possibles = {i for i in range(1, 10)}
        self.value = 0
        self.connectedSquares = {}


def printError(code):
    if code == 'c':
        print("Contradiction detected!")
        raise Exception('Contradiction detected!')
        #exit()
    if code == 'w':
        print("Sudoku has been solved wrongly!")
        raise Exception('Sudoku has been solved wrongly!')
        #exit()
    if code == 'i':
        print("Input is incorrect!")
        raise Exception('Input is incorrect!')

        #exit()


def removePeersPossibles(peers, digits):
    removedDigits = False
    for peer in peers:
        for digit in digits:
            if digit in peer.possibles:
                peer.possibles.remove(digit)
                removedDigits = True
        if len(peer.possibles) == 0 and peer.value == 0:
            raise ValueError('removed too much')
    return removedDigits


def removeSquaresPossibles(squares, keptDigits):
    removedDigits = False
    for square in squares:
        for digit in square.possibles - set(keptDigits):
            if digit in square.possibles:
                square.possibles.remove(digit)
                removedDigits = True
        if len(square.possibles) == 0 and square.value == 0:
            raise ValueError('removed too much')
    return removedDigits


def fillSquare(sudoku, square, digit):
    # if the digit is possible on this square, fill it in, remove the other possible digits and
    # remove the inserted digit from the possible digits of the square's neighbors
    if digit in square.possibles:
        square.value = digit
        square.possibles.clear()
        sudoku.filledSquares += 1
        removePeersPossibles(sudoku.getPeers(square), [digit])
        # if digit in square.connectedSquares:
        #     removedPossibles = fillSquare(sudoku, square.connectedSquares[digit], digit) or removedPossibles
        return True
    raise ValueError('digit not in possibles')


def findSolvedSquare(sudoku):
    foundSquares = False
    for r in range(sudoku.n):
        for c in range(sudoku.n):
            # if there is only one possible digit left write the digit inside the square
            if len(sudoku.board[r][c].possibles) == 1:
                if fillSquare(sudoku, sudoku.board[r][c], next(iter(sudoku.board[r][c].possibles))):
                    foundSquares = True
    return foundSquares


def getPossiblesOfUnit(unit):
    possibles = []
    # add all possible digits of a unit to a list
    for square in unit:
        possibles += list(square.possibles)
    return possibles


def getPossibleAppearanceOfUnit(n, unit):
    digits = [set([]) for i in range(n)]
    for square in unit:
        for digit in square.possibles:
            digits[digit - 1].add(square)
    return digits


def hiddenSingles(sudoku):
    foundSingles = False
    # for every unit on the board
    for u in sudoku.getUnitList():
        # check if there are still unsolved squares in the unit
        unit = [s for s in u if s.value == 0]
        if len(unit) == 0: continue
        # count how often the digits appear inside the unit and look at the lowest amount
        countedPossibles = collections.Counter(getPossiblesOfUnit(unit)).most_common()
        digit, rate = countedPossibles.pop()
        while rate == 1:
            # get the one square where digit is possible and write the digit inside it
            square = [s for s in u if digit in s.possibles].pop()
            fillSquare(sudoku, square, digit)
            foundSingles = True
            digit, rate = countedPossibles.pop() if len(countedPossibles) > 0 else 0, 0
    return foundSingles


def nakedNs(sudoku, n):
    foundNakedNs = False
    sharedPossibles = set([])
    for unit in sudoku.getUnitList():
        for comb in combin([s for s in unit if 1 < len(s.possibles) <= n], n):
            sharedPossibles.clear()
            sharedPossibles = set(sum([list(square.possibles) for square in comb], []))
            if len(sharedPossibles) == n:
                if removePeersPossibles(set(unit) - set(comb), sharedPossibles):
                    sudoku.pairs.add(comb)
                    foundNakedNs = True
                    break
    return foundNakedNs


def hiddenNs(sudoku, n):
    foundHiddenNs = False
    for unit in sudoku.getUnitList():
        digits = getPossibleAppearanceOfUnit(sudoku.n, unit)
        cs, ds = set([]), []
        for i in range(sudoku.n):
            if 1 < len(digits[i]) <= n:
                cs.update(digits[i])
                ds.append(i + 1)
        if len(cs) == n and len(ds) == n:
            if removeSquaresPossibles(cs, ds): foundHiddenNs = True
            continue
        if len(cs) % n == 0 and len(ds) % n == 0:
            for comb in combin(ds, n):
                shared = set.intersection(*[digits[d - 1] for d in comb])
                if len(shared) == n:
                    if removeSquaresPossibles(shared, comb): foundHiddenNs = True
    return foundHiddenNs


def intersectionRemoval(values, peers, digit):
    if all(x == values[0] for x in values):
        return removePeersPossibles(peers, digit)


def pointingNs(sudoku):
    foundPointingNs = False
    for box in sudoku.getBoxes():
        digits = getPossibleAppearanceOfUnit(sudoku.n, box)
        for i in range(sudoku.n):
            if len(digits[i]) < 2 or 3 < len(digits[i]): continue  # if digit doesnt appear 2-3 times -> continue
            # check if in same row
            rowValues = [square.row for square in digits[i]]
            if intersectionRemoval(rowValues, set(sudoku.getRows()[rowValues[0]]) - set(digits[i]), [i+1]):
                foundPointingNs = True
                continue

            # check if in same column
            columnValues = [square.column for square in digits[i]]
            if intersectionRemoval(columnValues, set(sudoku.getColumns()[columnValues[0]]) - set(digits[i]), [i+1]):
                foundPointingNs = True
    return foundPointingNs


def boxLineReduction(sudoku):
    foundReduction = False
    for unit in sudoku.getRows() + sudoku.getColumns():
        digits = getPossibleAppearanceOfUnit(sudoku.n, unit)
        for i in range(sudoku.n):
            if len(digits[i]) < 2 or 3 < len(digits[i]): continue  # if digit doesnt appear 2-3 times -> continue
            boxValues = [int(square.row / 3) * 3 + int(square.column / 3) for square in digits[i]]
            if intersectionRemoval(boxValues, set(sudoku.getBoxes()[boxValues[0]]) - set(digits[i]), [i+1]):
                foundReduction = True
    return foundReduction


def getPairs(sudoku, units):
    pairs = {}
    for unit in units:
        digits = getPossibleAppearanceOfUnit(sudoku.n, unit)
        for i in range(len(digits)):
            if len(digits[i]) == 2:
                if i in pairs:
                    pairs[i].append(digits[i])
                else:
                    pairs[i] = [digits[i]]
    return pairs


def findXWing(pairs, units, startAreRows):
    removedPossibles = False
    for key in pairs:
        if len(pairs[key]) >= 2:
            for comb in combin(pairs[key], 2):
                cPairs = []
                for s1 in comb[0]:
                    for s2 in comb[1]:
                        if (startAreRows and s1.column == s2.column) or (not startAreRows and s1.row == s2.row):
                            cPairs.append((s1, s2))
                            break
                    if len(cPairs) == 0:
                        break
                if len(cPairs) == 2:
                    for cPair in cPairs:
                        if removePeersPossibles(set(units[cPair[0].column if startAreRows else cPair[0].row]) - set(cPair), [key+1]):
                            removedPossibles = True
    return removedPossibles


def xWing(sudoku):
    removedPossibles = False
    rowPairs = getPairs(sudoku, sudoku.getRows())
    columnPairs = getPairs(sudoku, sudoku.getColumns())
    removedPossibles = findXWing(rowPairs, sudoku.getColumns(), startAreRows=True) or removedPossibles
    removedPossibles = findXWing(columnPairs, sudoku.getRows(), startAreRows=False) or removedPossibles
    return removedPossibles


def getSquareMinPossibles(sudoku):
    squares = sum(sudoku.board, [])
    square = min(squares, key=lambda s: len(s.possibles) if len(s.possibles) > 0 else 10)
    return square


def importSudoku(sudoku, puzzle):
    if len(puzzle) != 81: printError('i')
    i = 0
    for r in range(9):
        for c in range(9):
            if str(puzzle[i]) not in '0123456789': printError('i')
            if int(puzzle[i]) != 0:
                try:
                    fillSquare(sudoku, sudoku.board[r][c], int(puzzle[i]))
                except ValueError as err:
                    printError('c')
            i += 1


def checkSudoku(sudoku):
    for unit in sudoku.getUnitList():
        if sum(square.value for square in unit) != 45: return False
    return True


def solve(sudoku):
    foundStuff = True
    while foundStuff:
        if sudoku.filledSquares == sudoku.n * sudoku.n: return sudoku
        #sudoku.display(sudoku.board)
        #sudoku.displayPossibles()
        try:
            if findSolvedSquare(sudoku): continue
            if hiddenSingles(sudoku): continue
            if nakedNs(sudoku, 2): continue
            if nakedNs(sudoku, 3): continue
            if hiddenNs(sudoku, 2): continue
            if hiddenNs(sudoku, 3): continue
            if pointingNs(sudoku): continue
            if boxLineReduction(sudoku): continue
            if xWing(sudoku): continue
        except ValueError as err:
            print(err)
            return None
        foundStuff = False

    square = getSquareMinPossibles(sudoku)
    if len(square.possibles) == 0: return sudoku
    for digit in square.possibles:
        print("guess")
        sudoku_copy = deepcopy(sudoku)
        new_square = sudoku_copy.board[square.row][square.column]
        fillSquare(sudoku_copy, new_square, digit)
        solved_sudoku = solve(sudoku_copy)
        if solved_sudoku is not None:
            return solved_sudoku
    return None


def getPuzzleString(sudoku):
    sudokuString = ""
    for c in range(sudoku.n):
        for r in range(sudoku.n):
            sudokuString += str(sudoku[r][c].value)
    return sudokuString


def boardToIntArray(sudoku):
    arr = []
    for r in range(sudoku.n):
        for c in range(sudoku.n):
            arr.append(sudoku.board[r][c].value)
    return arr


def main():
    sudokuString = '030000010801006070050080000000007009402060500080000000000200050106040020003000000'
    sudoku = Sudoku()
    importSudoku(sudoku, sudokuString)
    sudoku.display(sudoku.board)
    sudoku.displayPossibles()
    start = time.time()
    sudoku = solve(sudoku)
    print(time.time() - start)
    if not checkSudoku(sudoku): printError('w')
    sudoku.display(sudoku.board)


@basic_bench
def solveOne(puzzleString):
    sudoku = Sudoku()
    importSudoku(sudoku, puzzleString)
    sudoku.display(sudoku.board)
    sudoku = solve(sudoku)
    if sudoku is not None:
        if not checkSudoku(sudoku):
            printError('w')
    else:
        raise Exception('Sudoku is none!')
    return boardToIntArray(sudoku)


def ads():
    global plc
    #AmsNetId = '10.15.96.76.1.1'
    AmsNetId = '127.0.0.1.1.1'
    # connect to plc and open connection
    plc = pyads.Connection(AmsNetId, pyads.PORT_TC3PLC1)
    plc.open()
    lastInput = ""
    while True:
        try:
            inputArr = plc.read_by_name("GVL.bSudoku", pyads.PLCTYPE_BYTE * 81)
            if lastInput != inputArr:
                if max(inputArr) == 0:
                    result = inputArr
                else:
                    try:
                        result = solveOne(inputArr)
                        print('Solved sudoku!')
                    except Exception as err:
                        result = [1 for i in range(81)]
                        print(err)
                plc.write_by_name("GVL.bResult", result, pyads.PLCTYPE_BYTE * 81)
                lastInput = inputArr
        except pyads.ADSError as err:
            print(err)


def testing():
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
    testCount = 1
    for i in range(len(inputStrings)):
        print("Running sudoku nr. {0}...".format(i + 1))
        inputString = inputStrings[i]
        for j in range(testCount):
            solveOne(inputString)


def exit_handler():
    print("connection closed")
    plc.close()


#atexit.register(exit_handler)


if __name__ == "__main__":
    main()
    #ads()
    #testing()
