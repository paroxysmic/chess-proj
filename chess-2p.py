import pygame as py
import time
import random
py.init()   
win = py.display.set_mode((640, 640))
CWHITE, CBLACK = 0xf0f9fa, 0xa2cade
LIGHTGRAY, GRAY, DARKGRAY = 0xaaaaaa, 0x888888, 0x666666
YELLOW, CYAN, MAGENTA = 0xffff00, 0x00ffff, 0xff00ff
pspsh = py.image.load("spsheet.png")
pspsh.set_colorkey(MAGENTA)
fspsh = py.image.load("highlspsheet.png")
fspsh = py.transform.scale_by(fspsh, 5)
fspsh.set_colorkey(MAGENTA)
pnumtoname = {0 : '', 1 : 'p', 2 : 'n', 3 : 'b', 4 : 'r', 5 : 'q', 6 : 'k'}
pttolegalmoves = {1 : [(0, -1)], 
                  2 : [(i, j) for i in (-2, -1, 1, 2) for j in (-2, -1, 1, 2) if (i + j) & 0x01 == 1], 
                  6 : [(i, j) for i in range(-1, 2) for j in range(-1, 2) if i != 0 or j != 0]}
pttolegaldirec = {3 : [(-1, -1), (-1, 1), (1, -1), (1, 1)], 
                  4 : [(-1, 0), (0, -1), (0, 1), (1, 0)], 
                  5 : [(i, j) for i in range(-1, 2) for j in range(-1, 2) if i != 0 or j != 0]}
#team -> white: 0, black: 1 
#type -> empty: 0, pawn: 1, knight: 2, bishop: 3, rook: 4, queen: 5, king: 6 
#x -> 0 - 7, left to right increasing
#y -> 0 - 7, top to bottom increasing (reverse of normal, graphics convention)
class Board():
    def __init__(self):
        self.data = [Piece(0, 0, (i & 0x07), (i >> 3)) for i in range(64)]
        for i in range(8):
            self.data[8 + i].team = 0
            self.data[8 + i].type = 1
            self.data[48 + i].team = 1
            self.data[48 + i].type = 1
        for i in range(4):
            self.data[7 * (i & 0x01) + 56 * (i >> 1)].team = i >> 1
            self.data[7 * (i & 0x01) + 56 * (i >> 1)].type = 4
            self.data[1 + 5 * (i & 0x01) + 56 * (i >> 1)].team = i >> 1
            self.data[1 + 5 * (i & 0x01) + 56 * (i >> 1)].type = 2            
            self.data[2 + 3 * (i & 0x01) + 56 * (i >> 1)].team = i >> 1
            self.data[2 + 3 * (i & 0x01) + 56 * (i >> 1)].type = 3
            self.data[3 + (i & 0x01) + 56 * (i >> 1)].team = i >> 1
            self.data[3 + (i & 0x01) + 56 * (i >> 1)].type = 5 + (i & 0x01)
    def render(self):
        for i in range(64):
            py.draw.rect(win, CWHITE if (((i & 0x07) + (i >> 3)) & 0x01 == 0) else CBLACK, ((i & 0x07) * 80, (i >> 3) * 80, 80, 80))
            self.data[i].render()
    def get_legal_moves(self, cx, cy):
        pt = self.data[cx + cy * 8].type
        checkedlegalmoves = []
        if pt == 0:
            return []
        if pt == 1:
            dy = 1 - (self.data[cx + cy * 8].team << 1)
            ny = cy + dy
            if ny >= 0 and ny < 8 and self.data[cx + ny * 8].type == 0:
                checkedlegalmoves.append((0, dy))
        if pt == 2 or pt == 6:
            # this is the branch where there are a finite subset of moves
            # pawn / knight / king
            # i.e. they don't have laserbeam movement
            uncheckedlegalmoves = pttolegalmoves[pt]
            for move in uncheckedlegalmoves:
                dx, dy = move[0], move[1]
                nx, ny = cx + dx, cy + dy
                if nx >= 0 and nx < 8 and ny >= 0 and ny < 8 and self.data[nx + ny * 8].type == 0:
                    checkedlegalmoves.append(move)
        if pt == 3 or pt == 4 or pt == 5:
            # this is the branch where there are a varying subset of moves
            # bishop / rook / queen
            # i.e. they do have laserbeam movement
            uncheckedlegaldirecs = pttolegaldirec[pt]           
            for direc in uncheckedlegaldirecs:
                currx, curry = cx, cy
                unblocked = True
                while unblocked:
                    currx += direc[0]
                    curry += direc[1]
                    if currx >= 0 and currx < 8 and curry >= 0 and curry < 8 and self.data[currx + curry * 8].type == 0:
                        checkedlegalmoves.append((currx - cx, curry - cy))
                    else:
                        unblocked = False
        return checkedlegalmoves
    def move_piece(self, ox, oy, dx, dy):
        #o is origin, and d is destination
        if (dx, dy) in self.get_legal_moves(ox, oy):
            destx, desty = ox + dx, oy + dy
            self.data[destx + desty * 8].type = self.data[ox + oy * 8].type
            self.data[destx + desty * 8].team = self.data[ox + oy * 8].team
            self.data[ox + oy * 8].type = 0
    def rand_move(self, team):
        culledb = [piece for piece in self.data if piece.team == team]
        selecp = random.choice(culledb)
        while len(self.get_legal_moves(selecp.x, selecp.y)) == 0:
            selecp = random.choice(culledb)
        selecmove = random.choice(self.get_legal_moves(selecp.x, selecp.y))
        self.move_piece(selecp.x, selecp.y, selecmove[0], selecmove[1])
class Piece():
    def __init__(self, type: int, team: int, x: int, y: int):
        self.type = type
        self.team = team
        self.x = x
        self.y = y
        self.moveableto = False
    def render(self):
        win.blit(pspsh, (self.x * 80, self.y * 80), (self.type * 80, self.team * 80, 80, 80))
running = True
clock = py.time.Clock()
board = Board()
def clickHandler(board: Board):
    mp = py.mouse.get_pos()
    mx, my = mp[0] // 80, mp[1] // 80
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
                clickHandler(board)
    board.rand_move(random.randint(0, 1))
    if keys[py.K_q]:
        running = False
    board.render()
    py.display.update()