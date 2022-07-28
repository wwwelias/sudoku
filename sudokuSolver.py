import collections
import time

import pyads
import atexit
from itertools import combinations as combin
from copy import deepcopy

global plc


class Sudoku:
    # creating combinations for Sudoku-boxes
    boxCombinations = []
    for rows in ([0, 1, 2], [3, 4, 5], [6, 7, 8]):
        for columns in ([0, 1, 2], [3, 4, 5], [6, 7, 8]):
            boxCombinations.append((rows, columns))

    def __init__(self, n=9):
        # creating the board itself and the class variables
        # board: array of sudoku-rows
        self.board = [[Square(r, c) for c in range(n)] for r in range(n)]
        self.n = n
        self.filledSquares = 0
        # columns: array of sudoku-columns
        self.columns = [[self.board[r][c] for r in range(self.n)] for c in range(self.n)]

        # creating the array of boxes
        boxes = []
        for i in range(self.n):
            rs, cs = self.boxCombinations[i]
            boxes.append([])
            for r in rs:
                for c in cs:
                    boxes[i].append(self.board[r][c])
        # boxes: array of sudoku-boxes
        self.boxes = boxes

    def getRows(self):
        return self.board

    def getColumns(self):
        return self.columns

    def getBoxes(self):
        return self.boxes

    def getUnitList(self):
        return self.board + self.columns + self.boxes

    # returns row, column and box of square
    def getUnits(self, square):
        # calculate in which box the square is located
        box = int(square.row / 3) * 3 + int(square.column / 3)
        return [self.board[square.row], self.columns[square.column], self.boxes[box]]

    def getPeers(self, square):
        # get all neighbors of the square (row, column and box)
        units = self.getUnits(square)
        return set(sum(units, [])) - {self.board[square.row][square.column]}

    # display a given board in the console
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

    # display the possible digits for the squares on the board
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


# creating own Errors
def printError(code):
    if code == 'c':
        print("Contradiction detected!")
        raise Exception('Contradiction detected!')
        # exit()
    if code == 'w':
        print("Sudoku has been solved wrongly!")
        raise Exception('Sudoku has been solved wrongly!')
        # exit()
    if code == 'i':
        print("Input is incorrect!")
        raise Exception('Input is incorrect!')
        # exit()


# remove digits at given squares (peers)
def removePeersPossibles(peers, digits):
    removedDigits = False
    for peer in peers:
        for digit in digits:
            if digit in peer.possibles:
                # remove the digits from possibles for every square in given peers
                peer.possibles.remove(digit)
                removedDigits = True
        if len(peer.possibles) == 0 and peer.value == 0:
            # unsolved square without any possible digits appeared (algorithm guessed a wrong number)
            raise ValueError('removed too much')
    return removedDigits  # return true if method was able to remove possible digits


# keep given digits and remove the others from given squares
def removeSquaresPossibles(squares, keptDigits):
    removedDigits = False
    for square in squares:
        for digit in square.possibles - set(keptDigits):
            if digit in square.possibles:
                # remove the digits from possibles for every square in given squares
                square.possibles.remove(digit)
                removedDigits = True
        if len(square.possibles) == 0 and square.value == 0:
            # unsolved square without any possible digits appeared (algorithm guessed a wrong number)
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
        return True
    raise ValueError('digit not in possibles')


# find squares with only one possible digit
def findSolvedSquare(sudoku):
    foundSquares = False
    for r in range(sudoku.n):
        for c in range(sudoku.n):
            # if there is only one possible digit left write the digit inside the square
            if len(sudoku.board[r][c].possibles) == 1:
                if fillSquare(sudoku, sudoku.board[r][c], next(iter(sudoku.board[r][c].possibles))):
                    foundSquares = True
    return foundSquares


# method to get the possible digits of the squares inside a unit
def getPossiblesOfUnit(unit):
    possibles = []
    # add all possible digits of a unit to a list
    for square in unit:
        possibles += list(square.possibles)
    return possibles


# returns where which digit appears in the possible digits of a unit
def getPossibleAppearanceOfUnit(n, unit):
    digits = [set([]) for i in range(n)]
    for square in unit:
        for digit in square.possibles:
            digits[digit - 1].add(square)
    return digits


# find digits that only appear once in the possible digits of a unit
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


# find naked Ns (pairs/triplets): n boxes that share n possible digits
def nakedNs(sudoku, n):
    foundNakedNs = False
    sharedPossibles = set([])
    for unit in sudoku.getUnitList():
        # get combinations of the squares with 2 to n possibles left
        for comb in combin([s for s in unit if 1 < len(s.possibles) <= n], n):
            sharedPossibles.clear()
            sharedPossibles = set(sum([list(square.possibles) for square in comb], []))
            if len(sharedPossibles) == n:  # if n boxes share n same digits -> pair / triplet
                # remove the n shared digits from the other squares of unit
                if removePeersPossibles(set(unit) - set(comb), sharedPossibles):
                    foundNakedNs = True
                    break
    return foundNakedNs


# find hidden Ns (pairs/triplets): n digits that only appear in shared n boxes
def hiddenNs(sudoku, n):
    foundHiddenNs = False
    for unit in sudoku.getUnitList():
        digits = getPossibleAppearanceOfUnit(sudoku.n, unit)
        cs, ds = set([]), []
        for i in range(sudoku.n):
            if 1 < len(digits[i]) <= n:
                # find digits that appear 2 to n times in units to ds and the squares they appear in
                cs.update(digits[i])
                ds.append(i + 1)
        # if the amount of squares and digits and are the same -> n digits share the same n squares -> pair/triplet
        if len(cs) == n and len(ds) == n:
            if removeSquaresPossibles(cs, ds): foundHiddenNs = True
            continue
        # if the amount of squares and digits are multiple of n -> multiple pairs/triplets have been found
        if len(cs) % n == 0 and len(ds) % n == 0:
            # identify the pairs/triplets because we don't know which squares and digits belong together
            for comb in combin(ds, n):
                # if the amount of shared squares is n --> pair/triplet found
                shared = set.intersection(*[digits[d - 1] for d in comb])
                if len(shared) == n:
                    if removeSquaresPossibles(shared, comb): foundHiddenNs = True
    return foundHiddenNs


# if all peers are in the same row/column/box -> remove possible digits of peers
# values: list of row/column/box-attributes of peers
def intersectionRemoval(values, peers, digit):
    if all(x == values[0] for x in values):
        return removePeersPossibles(peers, digit)


# pointing Ns: if pair or triplet is inside the same box and row/column
# -> digits of pair/triplet can't appear in the squares of row/column outside the box
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


# pointing Ns: if pair or triplet is inside the same row/column and box
# -> digits of pair/triplet can't appear in the squares of box (and don't belong to the pair/triplet)
def boxLineReduction(sudoku):
    foundReduction = False
    for unit in sudoku.getRows() + sudoku.getColumns():
        digits = getPossibleAppearanceOfUnit(sudoku.n, unit)
        for i in range(sudoku.n):
            if len(digits[i]) < 2 or 3 < len(digits[i]): continue  # if digit doesnt appear 2-3 times -> continue

            # check if in same box
            boxValues = [int(square.row / 3) * 3 + int(square.column / 3) for square in digits[i]]
            if intersectionRemoval(boxValues, set(sudoku.getBoxes()[boxValues[0]]) - set(digits[i]), [i+1]):
                foundReduction = True
    return foundReduction


# get the digits that appear 2 times in a unit
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
    return pairs  # returns dictionary: key=digit value=list of pairs


def findXWing(pairs, units, startAreRows):
    removedPossibles = False
    # for the keys that have more than 2 pairs: make combinations of pairs
    for key in pairs:
        if len(pairs[key]) >= 2:
            for comb in combin(pairs[key], 2):
                cPairs = []
                for s1 in comb[0]:
                    for s2 in comb[1]:
                        # compare the squares of the pairs with each other to check if...
                        # ...they are in the same column as well (pairs are from the same row)
                        # ...they are in the same row as well (pairs are from the same column)
                        if (startAreRows and s1.column == s2.column) or (not startAreRows and s1.row == s2.row):
                            cPairs.append((s1, s2))
                            break
                    if len(cPairs) == 0:
                        break
                if len(cPairs) == 2:  # the digit of the pairs were also in the same columns/rows
                    for cPair in cPairs:
                        # remove possible digits of the peers in the columns / rows
                        if removePeersPossibles(set(units[cPair[0].column if startAreRows else cPair[0].row]) - set(cPair), [key+1]):
                            removedPossibles = True
    return removedPossibles


# XWing:
# if a pair of a digit in 2 different rows and those digits also lie in 2 columns
# then the digits can be removed from the other squares in the 2 columns
# works for rows and columns reversed as well
# therefore there are 2 combinations:
# 1: Starting from 2 rows and eliminating in 2 columns
# 2: Starting from 2 columns and eliminating in 2 rows
# better explanation: https://www.sudokuwiki.org/X_Wing_Strategy
def xWing(sudoku):
    removedPossibles = False
    rowPairs = getPairs(sudoku, sudoku.getRows())
    columnPairs = getPairs(sudoku, sudoku.getColumns())
    # combination 1:
    removedPossibles = findXWing(rowPairs, sudoku.getColumns(), startAreRows=True) or removedPossibles
    # combination 2:
    removedPossibles = findXWing(columnPairs, sudoku.getRows(), startAreRows=False) or removedPossibles
    return removedPossibles


# get the square with the fewest possible digits
def getSquareMinPossibles(sudoku):
    squares = sum(sudoku.board, [])
    square = min(squares, key=lambda s: len(s.possibles) if len(s.possibles) > 0 else 10)
    return square


# import the unsolved sudoku from a string or array
def importSudoku(sudoku, puzzle):
    if len(puzzle) != 81: printError('i')  # check input
    i = 0
    for r in range(9):
        for c in range(9):
            if str(puzzle[i]) not in '0123456789': printError('i')  # check input
            if int(puzzle[i]) != 0:
                try:
                    fillSquare(sudoku, sudoku.board[r][c], int(puzzle[i]))
                except ValueError as err:  # Contradiction in the input-string/-array
                    printError('c')
            i += 1


# check if the sudoku has been solved correctly
def checkSudoku(sudoku):
    for unit in sudoku.getUnitList():
        if sum(square.value for square in unit) != 45: return False
    return True


# main function that tries to solve the sudoku step by step
def solve(sudoku):
    foundStuff = True
    # trying to solve the sudoku with simple strategies as long as squares can be solved or possible digits removed
    while foundStuff:
        # if all squares have been filled already -> sudoku is solved
        if sudoku.filledSquares == sudoku.n * sudoku.n: return sudoku
        # for more information about the strategies: https://www.sudokuwiki.org/sudoku.htm
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
            # ValueError signifies that a wrong digit has been guessed
            # therefore we have to go one step and guess another digit
            # print(err)
            return None
        # strategy's didn't find anything
        foundStuff = False
    # strategy's can't find anything anymore -> a digit has to be guessed
    # get the square with the fewest possible digits (to increase our chances of guessing the right digit)
    square = getSquareMinPossibles(sudoku)
    if len(square.possibles) == 0: return sudoku
    for digit in square.possibles:
        # copy the board and try solving it by guessing a digit
        sudoku_copy = deepcopy(sudoku)
        new_square = sudoku_copy.board[square.row][square.column]
        fillSquare(sudoku_copy, new_square, digit)
        # try to solve the board with the guessed digit with the help of the strategies
        solved_sudoku = solve(sudoku_copy)
        # sudoku is not None --> guess was correct and the sudoku has been solved
        # sudoku is None --> guess was incorrect
        if solved_sudoku is not None:
            return solved_sudoku
    # sudoku couldn't be solved
    return None


# turn sudoku into string
def getPuzzleString(sudoku):
    sudokuString = ""
    for c in range(sudoku.n):
        for r in range(sudoku.n):
            sudokuString += str(sudoku[r][c].value)
    return sudokuString


# turn sudoku into array
def boardToIntArray(sudoku):
    arr = []
    for r in range(sudoku.n):
        for c in range(sudoku.n):
            arr.append(sudoku.board[r][c].value)
    return arr


# solve a sudoku from input-string/-array
def solveOne(puzzleInput):
    # create sudoku board
    sudoku = Sudoku()
    importSudoku(sudoku, puzzleInput)
    # solve sudoku
    sudoku = solve(sudoku)
    if sudoku is not None:
        if not checkSudoku(sudoku):
            printError('w')
    else:
        raise Exception('Sudoku is none!')
    return boardToIntArray(sudoku)


def ads():
    global plc
    AmsNetId = '127.0.0.1.1.1'
    # connect to plc and open connection
    print("Connecting to plc ...")
    plc = pyads.Connection(AmsNetId, pyads.PORT_TC3PLC1)
    plc.open()
    lastInput = ""
    while True:
        try:
            # read unsolved sudoku via ADS
            inputArr = plc.read_by_name("GVL.bSudoku", pyads.PLCTYPE_BYTE * 81)
            # if input-array has changed:
            if lastInput != inputArr:
                if max(inputArr) == 0:
                    # input is empty sudoku -> return empty sudoku
                    result = inputArr
                else:
                    try:
                        result = solveOne(inputArr)
                        print('Solved sudoku!')
                    except Exception as err:
                        # sudoku wasn't solvable
                        result = [1 for i in range(81)]
                        print(err)
                # write back the result
                plc.write_by_name("GVL.bResult", result, pyads.PLCTYPE_BYTE * 81)
                lastInput = inputArr
        except pyads.ADSError as err:
            # ADS-Server not started
            print(err)
            time.sleep(1)


def exit_handler():
    # close connection on exit
    print("connection closed")
    plc.close()


atexit.register(exit_handler)


if __name__ == "__main__":
    ads()
