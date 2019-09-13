'''
Simple array implementation of TetrisField.

Can check if a given tetrisPiece can fit.
'''

import TetrisPiece
import numpy as np
from enum import Enum

class PerfectFit(Enum):
    PERFECT = 0
    EXIT = 1
    CONTINUE = 2

EMPTY = '.'
LIMIT = 'X'
EMPTY_INT = TetrisPiece.typeStringToInt[EMPTY]
LIMIT_INT = TetrisPiece.typeStringToInt[LIMIT]
    
class TetrisField(object):
    def __init__(self, width=0, height=0):
        self.data = np.zeros(shape=(height,width),dtype=np.uint8)
        self.width = width
        self.height = height
        self.columnHeights = np.zeros(shape=(width,),dtype=np.uint8)

    # TODO: store column heights so we don't have to recalc.    
    def getColumnHeight(self, columnIndex, recalc=False):
        if recalc:
            height = 0
            for y in range(self.height - 1, -1, -1):
                if self.data[y,columnIndex] == EMPTY_INT:                    
                    break
                else:
                    height += 1
            self.columnHeights[columnIndex] = height
            
        return self.columnHeights[columnIndex]
    
    def getColumnHeights(self, startIndex=None, endIndex=None):
        if startIndex is None:
            startIndex = 0
        if endIndex is None:
            endIndex = self.width - 1            
        return self.columnHeights[startIndex:endIndex]
    
    def copy(self):
        result = TetrisField()  # create empty field       
        result.data = np.copy(self.data)
        result.width = self.width  # post-set width/height
        result.height = self.height
        result.columnHeights = np.copy(self.columnHeights)
        
        return result
    
    def findDrop(self, piece):
        # modifies the piece's position by only changing y value.
        # returns null if dropping it creates a gap. (e.g. s/z in neutral on the floor)
        currentResult = self.isPerfectFit(piece)
        while (currentResult == PerfectFit.CONTINUE):
            piece.topLeftCorner[0] += 1
            currentResult = self.isPerfectFit(piece)
        if currentResult == PerfectFit.EXIT:
            return None
        else:        
            return piece
    
    # returns if the current piece placement is happy
    def isPerfectFit(self, piece):        
        # first, check if we collide.
        finalPositions = []
        piecePosition = piece.topLeftCorner
                
        for offset in piece.currentOrientation:
            finalY = offset[0] + piece.topLeftCorner[0]
            finalX = offset[1] + piece.topLeftCorner[1]
            finalPositions.append((finalY, finalX))
        
        if self.collides(finalPositions):
            return PerfectFit.EXIT
        else:
            # place the piece then check under the piece to make sure it conforms perfectly
            self.placePiece(piece)
            allCellsHappy = True
            for cellPosition in finalPositions:
                y, x = cellPosition
                positionBelow = (y+1, x)          
                positionLeft =  (y,   x-1)
                positionRight = (y,   x+1)
                
                # place values of cells into variables...
                cellDown = self.getCellValue(positionBelow[0], positionBelow[1])
                cellLeft = self.getCellValue(positionLeft[0], positionLeft[1])
                cellRight = self.getCellValue(positionRight[0], positionRight[1]) 
                
                # (position, cellVal, cellCanBeEmpty)
                comparisons = ((positionBelow, cellDown, False), 
                               (positionLeft, cellLeft, True), 
                               (positionRight, cellRight, True))
                
                for comparison in comparisons:
                    (pos, cellVal, emptyOK) = comparison
                    if pos in finalPositions:  # ok
                        continue
                    elif cellVal == LIMIT_INT:  # ok
                        continue
                    elif cellVal == piece.typeString:
                        allCellsHappy = False
                        break
                    elif (cellVal == EMPTY_INT and not emptyOK):
                        allCellsHappy = False
                        break 

            self.unplacePiece(piece)
            if allCellsHappy:
                return PerfectFit.PERFECT
            else:
                return PerfectFit.CONTINUE
    
    # safe get cell value. returns LIMIT_INT if outside bounds
    def getCellValue(self, y, x):
        if 0 <= y < self.height and 0 <= x < self.width:
            return self.data[y,x]
        return LIMIT_INT
    
    def cellHappy(self, typeString1, typeString2):
        return typeString1 != typeString2
            
    # returns true if any of the positions given collide with the matrix        
    def collides(self, positions):    
        for position in positions:
            (y, x) = position
            try:
                if self.data[y, x] != EMPTY_INT:
                    return True
            except IndexError:
                return True
                
        return False
    
    def placePiece(self, piece):
        (posOffsetY, posOffsetX) = piece.topLeftCorner
        for offset in piece.currentOrientation:
            (y, x) = offset
            (y, x) = y+posOffsetY, x+posOffsetX
            self.data[y, x] = piece.typeInt
            self.columnHeights[x] = max(self.columnHeights[x], self.height - y)
            
    def unplacePiece(self, piece):
        (posOffsetY, posOffsetX) = piece.topLeftCorner
        s = set()
        for offset in piece.currentOrientation:
            (y, x) = offset
            (y, x) = y+posOffsetY, x+posOffsetX
            self.data[y, x] = EMPTY_INT  
            s.add(x)
        
        for x in s:
            self.getColumnHeight(x,True)
            
    def __str__(self):
        resultRows = []        
        for row in self.data:
            resultRows.append(''.join(TetrisPiece.typeIntToString[x] for x in row))        
        return '\n'.join(resultRows)
        
    def copySubFields(self, x_range):            
        result = TetrisField()  # create empty field
        startX,endX = x_range       
        result.data = self.data[:,startX:endX]
        result.width = endX-startX  # post-set width/height
        result.height = self.height
        result.columnHeights = self.columnHeights[startX:endX]
        return result
        

if __name__ == '__main__':
    import time
    t = time.time()    
    x = 0
    fieldWidth = 10
    fieldHeight = 100
    field = TetrisField(fieldWidth, fieldHeight)
    fields = []

    # put each piece in each orientation in 4x4 empty grid things
    for piece in TetrisPiece.getBag():
        for i in range(len(piece.offsets)):
            piece.SetCurrentOrientation(i)
            for j in range(fieldWidth):
                piece.SetPosition(j, 0)
                result = field.findDrop(piece)
                if result is not None:
                    field.placePiece(result)
                    fields.append(field.copy())
                    field.unplacePiece(result)                    
    
    #for field in fields:
    #    print(field , '\n')
    

    print (time.time() - t)