import collections
import time
from itertools import combinations as combin
from copy import deepcopy

class Sudoku:
    boxCombinations = []
    for rows in ([0, 1, 2], [3, 4, 5], [6, 7, 8]):
        for columns in ([0, 1, 2], [3, 4, 5], [6, 7, 8]):
            boxCombinations.append((rows, columns))

    def __init__(self, board=None, n=9):
        self.board = [[Square(r, c) for c in range(n)] for r in range(n)] if board is None else board
        self.n = n

        self.columns = [[self.board[r][c] for r in range(self.n)] for c in range(self.n)]

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


def printError(code):
    if code == 'c':
        print("Contradiction detected!")
        exit()
    if code == 'w':
        print("Sudoku has been solved wrongly!")
        exit()
    if code == 'i':
        print("Input is incorrect!")
        exit()


def removePeersPossibles(peers, digits):
    removedDigits = False
    # remove the digits from possible digits of peers
    for peer in peers:
        for digit in digits:
            if digit in peer.possibles:
                peer.possibles.remove(digit)
                removedDigits = True
        if len(peer.possibles) == 0 and peer.value == 0:
            raise ValueError('removed too much')
    return removedDigits


def fillSquare(sudoku, square, digit):
    # if the digit is possible on this square, fill it in, remove the other possible digits and
    # remove the inserted digit from the possible digits of the square's neighbors
    if digit in square.possibles:
        square.value = digit
        square.possibles.clear()
        return removePeersPossibles(sudoku.getPeers(square), [digit])
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
                    foundNakedNs = True
                    break
    return foundNakedNs


def getSquareMinPossibles(sudoku):
    squares = sum(sudoku.board, [])
    square = min(squares, key=lambda s: len(s.possibles) if len(s.possibles) > 0 else 10)
    return square


def importSudoku(sudoku, puzzle):
    if type(puzzle) is not str:
        puzzle = sum(puzzle, [])
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
        #sudoku.display(sudoku.board)
        #sudoku.displayPossibles()
        try:
            if findSolvedSquare(sudoku): continue
            if hiddenSingles(sudoku): continue
            if nakedNs(sudoku, 2): continue
            if nakedNs(sudoku, 3): continue
        except ValueError as err:
            print(err)
            return None
        foundStuff = False

    square = getSquareMinPossibles(sudoku)
    for digit in square.possibles:
        sudoku_copy = deepcopy(sudoku)
        new_square = sudoku_copy.board[square.row][square.column]
        fillSquare(sudoku_copy, new_square, digit)
        solved_sudoku = solve(sudoku_copy)
        if solved_sudoku is not None:
            return solved_sudoku
    return sudoku


def main():
    sudokuString = '634200000002300007000900005000000736000023000048000000590000000000005410000031000'
    sudoku = Sudoku()
    importSudoku(sudoku, sudokuString)
    sudoku.display(sudoku.board)
    sudoku.displayPossibles()
    start = time.time()
    sudoku = solve(sudoku)
    print(time.time() - start)
    if not checkSudoku(sudoku): printError('w')
    sudoku.display(sudoku.board)


if __name__ == "__main__":
    main()
