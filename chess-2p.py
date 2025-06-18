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
menu_play = py.image.load("pausecard-play.png")
menu_draw = py.image.load("pausecard-draw.png")
menu_resign = py.image.load("pausecard-resign.png")
menu_select = py.image.load("pausecard-selector.png")
menu_reject = py.image.load("pausecard-rejected.png")
endcard_white = py.image.load("endscr-white.png")
endcard_black = py.image.load("endscr-black.png")
titlecard_stupid.set_colorkey(MAGENTA)
titlecard_chess.set_colorkey(MAGENTA)
titlecard_game.set_colorkey(MAGENTA)
menu_play.set_colorkey(MAGENTA)
menu_draw.set_colorkey(MAGENTA)
menu_resign.set_colorkey(MAGENTA)
menu_select.set_colorkey(MAGENTA)
menu_reject.set_colorkey(MAGENTA)
endcard_white.set_colorkey(MAGENTA)
endcard_black.set_colorkey(MAGENTA)
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
pttovalue = {0 : 0, 1 : 10, 2 : 31, 3 : 33, 4 : 56, 5 : 95, 6 : 2000}
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
        return Piece(0, 2, x, y)
    def get_legal_moves(self, x, y) -> list:
        ptype = self.gpa(x, y).type
        pteam = self.gpa(x, y).team
        legalmoves = []
        if self.in_check(pteam) and ptype != 6:
            return []
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
            availmoves = [move for move in pttolegalmoves[6] if inbounds(x + move[0],y + move[1]) and self.gpa(x + move[0], y + move[1]).team != pteam]
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
                if opt == 6:
                    availmoves = [move for move in availmoves if max(abs(x + move[0] - opx), abs(y + move[1] - opy)) > 1]
            availmoves = [move for move in availmoves if move not in otas]
            legalmoves += availmoves
        return legalmoves
    def giving_check(self, x, y) -> bool:
        ptype = self.gpa(x, y).type
        pteam = self.gpa(x, y).team
        oppok = [piece for piece in self.data if piece.type == 6 and piece.team != pteam][0]
        okx, oky = oppok.x, oppok.y
        if ptype == 1:
            dy = (2 * pteam) - 1
            return any([dy + y == oky and dx + x == okx for dx in (-1, 1)])
        if ptype == 2:
            return any([dx + x == okx and dy + y == oky for (dx, dy) in pttolegalmoves[2]])
        if ptype in (3, 4, 5):
            for direc in pttolegaldirec[ptype]:
                cpx = x
                cpy = y
                dx, dy = direc[0], direc[1]
                unblocked = True
                while unblocked:
                    cpx += dx
                    cpy += dy
                    if not inbounds(cpx, cpy):
                        unblocked = False
                        break
                    if self.gpa(cpx, cpy).type == 6 and self.gpa(cpx, cpy).team != pteam:
                        return True
                    elif self.gpa(cpx, cpy).type == 0:
                        continue
                    else:
                        unblocked = False
                        break
        return False
    def in_check(self, team):
        oppoteam = [piece for piece in self.data if piece.team != team]
        return any([self.giving_check(p.x, p.y) for p in oppoteam])
    def get_attacked_squares(self, team):
        attackedsquares = []
        oppoteam = [piece for piece in self.data if piece.team != team and piece.type != 6]
        for piece in oppoteam:
            px, py = piece.x, piece.y
            if piece.type == 1:
                dy = 1 - (piece.team * 2)
                attackedsquares.append((px - 1, py + dy))
                attackedsquares.append((px + 1, py + dy))
            else:
                for move in self.get_legal_moves(px, py):
                    attackedsquares.append((px + move[0], py + move[1]))
        return sorted(list(set(attackedsquares)))
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
    def value(self):
        value = 0
        for piece in self.data:
            value += pttovalue[piece.type] * ((2 * piece.team) - 1)
        return value
    def move_randomp(self, team):
        teampieces = [piece for piece in self.data if piece.team == team]
        selecpiece = teampieces[random.randint(0, len(teampieces) - 1)]
        while len(self.get_legal_moves(selecpiece.x, selecpiece.y)) == 0:
            selecpiece = teampieces[random.randint(0, len(teampieces) - 1)]
        selecpmoves = self.get_legal_moves(selecpiece.x, selecpiece.y)
        selecmove = selecpmoves[random.randint(0, len(selecpmoves) - 1)]
        self.move_piece(selecpiece.x, selecpiece.y, selecmove[0] + selecpiece.x, selecmove[1] + selecpiece.y)
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
class TextBox():
    def __init__(self, filename, origpos, falling=False, braking=False, wobbling=False, wobbleintensity=0, wshift=0, btarg=[0, 0]):
        self.im = py.image.load(filename)
        self.im.set_colorkey(MAGENTA)
        self.pos = [0, 0]
        self.pos[0] = origpos[0]
        self.pos[1] = origpos[1]
        self.origpos = [0, 0]
        self.origpos[0] = origpos[0]
        self.origpos[1] = origpos[1]
        self.vel = [1 + random.random(), -(10 + random.random())]
        self.falling = falling  
        self.braking = braking
        if falling:
            self.acc = [0, 0.5]
        if braking:
            self.acc = [btarg[0] - self.pos[0], btarg[1] - self.pos[1]]
            len = math.sqrt(self.acc[0] * self.acc[0] + self.acc[1] * self.acc[1])
            self.acc[0] *= 1/len
            self.acc[1] *= 1/len
            self.btarg = btarg
        self.wobbling = True
        self.wintensity = wobbleintensity
        self.wshift = wshift
        self.inittime = time.time()
        self.bounces = 0
    def posUpdate(self):
        self.pos[0] += self.vel[0]
        self.pos[1] += self.vel[1]
        self.vel[0] += self.acc[0]
        self.vel[1] += self.acc[1]
        if self.falling:
            if self.pos[1] > 429:
                self.pos[1] = 429
                self.vel[0] *= 0.8
                self.vel[1] *= -0.4
                self.bounces += 1
        if self.braking:
            xsgn = 1 if (self.btarg[0] - self.pos[0]) > 0 else -1
            ysgn = 1 if (self.btarg[1] - self.pos[1]) > 0 else -1
            self.acc[0] = max(-3, min(3, 0.03 * xsgn * (self.btarg[0] - self.pos[0]) * (self.btarg[0] - self.pos[0])))
            self.acc[1] = max(-3, min(3, 0.03 * ysgn * (self.btarg[1] - self.pos[1]) * (self.btarg[1] - self.pos[1])))
            if max(abs(self.acc[0]), abs(self.acc[1])) < 0.01:
                self.pos[0] = self.btarg[0]
                self.pos[1] = self.btarg[1]
            else:
                self.acc[0] *= 0.9
                self.vel[0] *= 0.7            
                self.acc[1] *= 0.9
                self.vel[1] *= 0.7
    def timeAlive(self):
        return time.time() - self.inittime
    def render(self):
        if self.wobbling:
            win.blit(self.im, (self.pos[0], self.pos[1] + self.wintensity * 2 * math.sin(time.time() + self.wshift)))
        else:
            win.blit(self.im, (self.pos[0], self.pos[1]))
    def resetPos(self):
        self.pos[0] = self.origpos[0]
        self.pos[1] = self.origpos[1]
        self.vel = [0, 0]
        self.acc = [0, 0]
running, paused = True, False
rejecttimer = 0
mselected = [0, 0]
clock = py.time.Clock()
rejects = []
board = Board()
bwins = 0
wwins = 0
board.data.append(Piece(4, 0, 0, 0))
board.data.append(Piece(4, 0, 0, 1))
board.data.append(Piece(6, 1, 4, 0))
board.data.append(Piece(6, 0, 7, 7))
print(board.is_checkmated(1))
def drawNum(k: int, pos: list[int]):
    nss = py.image.load("numspritesheet.png")
    nf = py.image.load("num-frame.png")
    nss.set_colorkey(MAGENTA)
    nf.set_colorkey(MAGENTA)
    k0 = k % 10
    k1 = k // 10
    if (k < 0 or k > 99):
        raise ValueError("k out of acceptable range")
    win.blit(nf, (pos[0]-36, pos[1]-25))
    win.blit(nss, (pos[0]-40, pos[1]-25), (k1 * 50, 0, 50, 50))
    win.blit(nss, (pos[0]-8, pos[1]-25), (k0 * 50, 0, 50, 50))
pscrtext = [
    TextBox("titlecard-stupid.png", [640, 50], False, True, True, 10, 0, [50, 50]),
    TextBox("titlecard-chess.png", [640, 110], False, True, True, 10, 0.5, [180, 110]),
    TextBox("titlecard-game.png", [640, 170], False, True, True, 10, 1, [310, 170]),
    TextBox("pausecard-play.png", [0, 320], False, True, True, 5, 0, [300, 320]),
    TextBox("pausecard-resign.png", [0, 380], False, True, True, 5, 0.5, [300, 380]),
    TextBox("pausecard-draw.png", [0, 440], False, True, True, 5, 1, [300, 440]),
]
def gameClickHandler():
    global board
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
def menuClickHandler():
    pass
def gameKeyboardHandler():
    global highlighted, paused, mselected, board
    if keys[py.K_k]:
        print(board.in_check(0))
    if keys[py.K_p]:
        highlighted = False
        paused = True
        mselected = [0, 0]
def menuKeyboardHandler():
    global paused, turn, board, pscrtext
    if keys[py.K_RETURN]:
        if mselected == [0, 0]:
            paused = False
            for textbox in pscrtext:
                textbox.resetPos()
        if mselected == [0, 1]:
            board = Board()
            board.initialize()
            turn = 0
            paused = False
            for textbox in pscrtext:
                textbox.resetPos()
        if mselected == [0, 2]:
            rejects.append(TextBox("pausecard-rejected.png", [0, 330], True, False, False, 0, 0))
    if keys[py.K_w] or keys[py.K_UP]:
        mselected[1] = (mselected[1] - 1) % 3
    if keys[py.K_s] or keys[py.K_DOWN]:
        mselected[1] = (mselected[1] + 1) % 3
def highlightMoveableSquares(x, y):
    for move in board.get_legal_moves(x, y):
        mx, my = move[0] + x, move[1] + y
        if board.gpa(mx, my).type != 0:
            win.blit(hsurf, (mx * 80, my * 80), (80, 0, 80, 80))
        else:
            win.blit(hsurf, (mx * 80, my * 80), (0, 0, 80, 80))
def renderGame():
    global board, highlighted
    board.render()
    if highlighted:
        highlightMoveableSquares(fx, fy)
def renderPauseMenu():
    global rejects, board, pscrtext
    board.render()
    bg = py.Surface((640, 640))
    for i in range(640):
        iang = i * math.pi / 320 + time.time()
        r = int((math.sin(iang) + 1) * 127.5)
        g = int((math.sin(iang + 2 * math.pi / 3) + 1) * 127.5)
        b = int((math.sin(iang + 4 * math.pi / 3) + 1) * 127.5)     
        col = (r << 16) + (g << 8) + b
        bg.fill(col, (0, i, 640, 1))
    bg.set_alpha(0x8f)
    win.blit(bg, (0, 0))
    for textbox in pscrtext:
        textbox.posUpdate()
        textbox.render()
    win.blit(menu_select, (pscrtext[3 + mselected[1]].pos[0] - 49, pscrtext[3 + mselected[1]].pos[1] + 10 * math.sin(time.time() + pscrtext[3 + mselected[1]].wshift)))
    drawNum(bwins, [160, 600])
    drawNum(wwins, [480, 600])
    win.blit(endcard_white, (40, 500))
    win.blit(endcard_black, (360, 500))
    rejects = [rej for rej in rejects if rej.timeAlive() < 2]
    for rej in rejects:
        rej.posUpdate()
        rej.render()
    
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
                    gameClickHandler()
                if paused:
                    menuClickHandler()
        if event.type == py.KEYDOWN:
            if paused:
                menuKeyboardHandler()
            if not paused:
                gameKeyboardHandler()
    if keys[py.K_q]:
        running = False
    if not paused:
        renderGame()
    if paused:
        renderPauseMenu()
    
    py.display.update()