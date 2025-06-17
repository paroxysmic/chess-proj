import pygame as py
import time
import math
import random
py.init()   
win = py.display.set_mode((640, 640))
CWHITE, CBLACK = 0xf0f9fa, 0xa2cade
DCWHITE, DCBLACK = 0xabb2b3, 0x95bacc
LIGHTGRAY, GRAY, DARKGRAY = 0xaaaaaa, 0x888888, 0x666666
YELLOW, CYAN, MAGENTA = 0xffff00, 0x00ffff, 0xff00ff
pspsh = py.image.load("spsheet.png")
pspsh.set_colorkey(MAGENTA)
fspsh = py.image.load("highlspsheet.png")
fspsh = py.transform.scale_by(fspsh, 5)
fspsh.set_colorkey(MAGENTA)
hsurf = py.Surface((160, 80), py.HWSURFACE)
hsurf.fill(MAGENTA)
hsurf.set_colorkey(MAGENTA)
pscreen = py.Surface((640, 640), py.HWSURFACE)
titlecard_stupid = py.image.load("titlecard-stupid.png")
titlecard_chess = py.image.load("titlecard-chess.png")
titlecard_game = py.image.load("titlecard-game.png")
titlecard_stupid.set_colorkey(MAGENTA)
titlecard_chess.set_colorkey(MAGENTA)
titlecard_game.set_colorkey(MAGENTA)
pscreen.fill(0x333333)
pscreen.set_alpha(0x80)
py.draw.circle(hsurf, 0xaaaaaa, (40, 40), 10)
py.draw.circle(hsurf, 0xaaaaaa, (120, 40), 35)
py.draw.circle(hsurf, MAGENTA, (120, 40), 30)
hsurf.set_alpha(0x80)
pnumtoname = {0 : '*', 1 : '', 2 : 'N', 3 : 'B', 4 : 'R', 5 : 'Q', 6 : 'K'}
#PAWNS: not included bcz they move in different ways based on team
pttolegalmoves = {2 : [(i, j) for i in (-2, -1, 1, 2) for j in (-2, -1, 1, 2) if (i + j) & 0x01 == 1], 
                  6 : [(i, j) for i in range(-1, 2) for j in range(-1, 2) if i != 0 or j != 0]}
pttolegaldirec = {3 : [(-1, -1), (-1, 1), (1, -1), (1, 1)], 
                  4 : [(-1, 0), (0, -1), (0, 1), (1, 0)], 
                  5 : [(i, j) for i in range(-1, 2) for j in range(-1, 2) if i != 0 or j != 0]}
kskewhash = {pttolegalmoves[6][i] : pttolegalmoves[6][7 - i] for i in range(8)}
fx, fy = 0, 0
turn = 0
highlighted = False
#team -> white: 0, black: 1 
#type -> empty: 0, pawn: 1, knight: 2, bishop: 3, rook: 4, queen: 5, king: 6 
#x -> 0 - 7, left to right increasing
#y -> 0 - 7, top to bottom increasing (reverse of normal, graphics convention)
def inbounds(cx, cy):
    return cx >= 0 and cx < 8 and cy >= 0 and cy < 8
class Board():
    def __init__(self):
        self.data = []
    def __repr__(self):
        rt = ""
        for i in self.data:
            rt += f"{i.__repr__()} "
        return rt
    def initialize(self):
        for i in range(8):
            self.data.append(Piece(1, 1, i, 6))
            self.data.append(Piece(1, 0, i, 1))
        for i in range(4):
            i1, i0 = i >> 1, i & 0x01
            self.data.append(Piece(4, i1, 7 * i0, 7 * i1))
            self.data.append(Piece(2, i1, 5 * i0 + 1, 7 * i1))
            self.data.append(Piece(3, i1, 3 * i0 + 2, 7 * i1))
            self.data.append(Piece(5 + i0, i1, i0 + 3, 7 * i1))
    def render(self):
        for i in range(64):
            py.draw.rect(win, CWHITE if (((i & 0x07) + (i >> 3)) & 0x01 == 0) else CBLACK, ((i & 0x07) * 80, (i >> 3) * 80, 80, 80))
        for piece in self.data:
            piece.render()
    def gpa(self, x, y):
        for piece in self.data:
            if piece.x == x and piece.y == y:
                return piece
        return Piece(0, 0, x, y)
    def get_legal_moves(self, x, y) -> list:
        ptype = self.gpa(x, y).type
        pteam = self.gpa(x, y).team
        legalmoves = []
        if ptype == 0:
            return []
        if ptype == 1:
            #PAWN
            dy = 1 - (pteam << 1)
            ny = y + dy
            if (self.gpa(x, ny).type == 0 and inbounds(x, ny)):
                legalmoves.append((0, dy))
                if (self.gpa(x, ny + dy).type == 0 and inbounds(x, ny + dy) and y == 5 * pteam + 1):
                    legalmoves.append((0, 2 * dy))
            for dx in (-1, 1):
                nx = x + dx
                if (self.gpa(nx, ny).type not in (0, 6) and self.gpa(nx, ny).team != pteam):
                    legalmoves.append((dx, dy))
        if ptype == 2:
            #KNIGHT
            for move in pttolegalmoves[2]:
                dx, dy = move[0], move[1]
                nx, ny = x + dx, y + dy
                np = self.gpa(nx, ny)
                if (np.type == 0 and inbounds(nx, ny)):
                    legalmoves.append((dx, dy))
                if (np.type not in (0, 6) and np.team != pteam and inbounds(nx, ny)):
                    legalmoves.append((dx, dy))
        if ptype in (3, 4, 5):
            #BISHOP, ROOK, QUEEN
            for direc in pttolegaldirec[ptype]:
                unblocked = True
                cdx, cdy = 0, 0
                #cumulative delta x/y
                dx, dy = direc[0], direc[1]
                #delta x/y
                while unblocked:
                    cdx += dx
                    cdy += dy
                    nx, ny = x + cdx, y + cdy
                    np = self.gpa(nx, ny)
                    if inbounds(nx, ny):
                        if (np.type == 0):
                            legalmoves.append((cdx, cdy))
                        else:
                            unblocked = False
                            if (np.type != 6 and np.team != pteam):
                                legalmoves.append((cdx, cdy))
                    else:
                        unblocked = False
        if ptype == 6:
            otas = self.get_attacked_squares(pteam)
            availmoves = [move for move in pttolegalmoves[6] if inbounds(x + move[0],y + move[1])]
            oppoteam = [piece for piece in self.data if piece.team != pteam]
            for oppopiece in oppoteam:
                opx, opy = oppopiece.x, oppopiece.y
                opt = oppopiece.type
                if opt == 1:
                    dy = (pteam * 2) - 1
                    for dx in (-1, 1):
                        if (opx + dx - x, opy + dy - y) in availmoves:
                            availmoves.remove((opx + dx - x, opy + dy - y))
                if opt == 2:
                    for (dx, dy) in pttolegalmoves[2]:
                        if (opx + dx - x, opy + dy - y) in availmoves:
                            availmoves.remove((opx + dx - x, opy + dy - y))
                if opt == 3 or opt == 5:
                    if abs(opx - x) == abs(opy - y):
                        if (opx - x) == (opy - y):
                            if ((-1, -1) in availmoves):
                                availmoves.remove((-1, -1))
                            if ((1, 1) in availmoves):
                                availmoves.remove((1, 1))
                        else:
                            if ((-1, 1) in availmoves):
                                availmoves.remove((-1, 1))
                            if ((1, -1) in availmoves):
                                availmoves.remove((1, -1))
                if opt == 4 or opt == 5:
                    if opy == y:
                        if ((-1, 0) in availmoves and (opx != x - 1 or opy != y)):
                            availmoves.remove((-1, 0))
                        if ((1, 0) in availmoves and (opx != x + 1 or opy != y)):  
                            availmoves.remove((1, 0))
                    if opx == x:
                        if ((0, -1) in availmoves and (opx != x or opy != y - 1)):
                            availmoves.remove((0, -1))
                        if ((0, 1) in availmoves and (opx != x or opy != y + 1)):
                            availmoves.remove((0, 1))
                # if opt == 6:
                #     for i in range(-1, 2):
                #         for j in range(-1, 2):
                #             if                 # 
            availmoves = [move for move in availmoves if move not in otas]
            legalmoves += availmoves
        return legalmoves
    def giving_check(self, x, y) -> bool:
        ptype = self.gpa(x, y).type
        pteam = self.gpa(x, y).team
        king = [piece for piece in self.data if piece.type == 6 and piece.team != pteam][0]
        if ptype == 1:
            #PAWN
            dy = 1 - (pteam << 1)
            for dx in (-1, 1):
                nx, ny = x + dx, y + dy
                if (nx == king.x and ny == king.y):
                    return True
        if ptype == 2:
            #KNIGHT
            for move in pttolegalmoves[2]:
                nx, ny = x + move[0], y + move[1]
                if(nx == king.x and ny == king.y):
                    return True
        if ptype in (3, 4, 5):
            #BISHOP, ROOK, QUEEN
            for direc in pttolegaldirec[ptype]:
                unblocked = True
                cx, cy = x, y
                #cumulative delta x/y
                dx, dy = direc[0], direc[1]
                #delta x/y
                while unblocked:
                    cx += dx
                    cy += dy
                    if(inbounds(cx, cy)):
                        if(self.gpa(cx, cy).team == pteam):
                            unblocked = False
                        else:
                            if(self.gpa(cx, cy).type == 6):
                                return True
                            else:
                                unblocked = False
                    else:
                        unblocked = False
        
        return False
    def in_check(self, team):
        oppoteam = [piece for piece in self.data if piece.team != team]
        return any([self.giving_check(p.x, p.y) for p in oppoteam])
    def get_attacked_squares(self, team):
        attackedsquares = set()
        oppoteam = [piece for piece in self.data if piece.team != team and piece.type != 6]
        for piece in oppoteam:
            px, py = piece.x, piece.y
            if piece.type == 1:
                dy = 1 - (piece.team * 2)
                attackedsquares.add((px - 1, py + dy))
                attackedsquares.add((px + 1, py + dy))
            else:
                for move in self.get_legal_moves(px, py):
                    attackedsquares.add((px + move[0], py + move[1]))
        return list(attackedsquares)
    def move_piece(self, ox, oy, dx, dy):
        cp = self.gpa(ox, oy)
        for piece in self.data:
            if (piece.x == dx) and (piece.y == dy):
                self.data.remove(piece)
        cp.x = dx
        cp.y = dy
        global turn
        turn += 1
    def is_checkmated(self, team):
        king = [piece for piece in self.data if piece.type == 6 and piece.team == team][0]
        return (len(self.get_legal_moves(king.x, king.y)) == 0 and self.in_check(team)) 
class Piece():
    def __init__(self, type: int, team: int, x: int, y: int):
        self.type = type
        self.team = team
        self.x = x
        self.y = y
    def render(self):
        win.blit(pspsh, (self.x * 80, self.y * 80), (self.type * 80, self.team * 80, 80, 80))
    def __repr__(self):
        return f"{pnumtoname[self.type]}{"abcdefgh"[self.x]}{"12345678"[self.y]}"
running, paused = True, False
clock = py.time.Clock()
board = Board()
board.initialize()
def gameClickHandler(board: Board):
    mp = py.mouse.get_pos()
    mx, my = mp[0] // 80, mp[1] // 80
    global fx, fy, highlighted
    fp = board.gpa(fx, fy)
    if (fx == mx and fy == my):
        highlighted = not highlighted
    else:
        highlighted = True        
        if(turn % 2 != fp.team and (mx - fx, my - fy) in board.get_legal_moves(fx, fy)):
            board.move_piece(fx, fy, mx, my)
            highlighted = False
    fx, fy = mx, my
def highlightMoveableSquares(x, y):
    for move in board.get_legal_moves(x, y):
        mx, my = move[0] + x, move[1] + y
        if board.gpa(mx, my).type != 0:
            win.blit(hsurf, (mx * 80, my * 80), (80, 0, 80, 80))
        else:
            win.blit(hsurf, (mx * 80, my * 80), (0, 0, 80, 80))
while running:
    clock.tick(60)
    events = py.event.get()
    keys = py.key.get_pressed()
    mpos = py.mouse.get_pos()
    mx, my = mpos[0]//80, mpos[1]//80
    for event in events:
        if event.type == py.QUIT:
            running = False
        if event.type == py.MOUSEBUTTONDOWN:
            mpressed = py.mouse.get_pressed()
            if mpressed[0]:
                if not paused:
                    gameClickHandler(board)
        if event.type == py.KEYDOWN:
            if keys[py.K_p]:
                highlighted = False
                paused = not paused
    if keys[py.K_q]:
        running = False
    board.render()
    if highlighted:
        highlightMoveableSquares(fx, fy)
    if paused:
        win.blit(pscreen, (0, 0))
        win.blit(titlecard_stupid, (50, 50 + 10 * math.sin(time.time())))
        win.blit(titlecard_chess, (100, 120 + 10 * math.sin(1 + time.time())))
        win.blit(titlecard_game, (150, 190 + 10 * math.sin(2 + time.time())))
    py.display.update()