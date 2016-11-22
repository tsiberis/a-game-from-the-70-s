#!/usr/bin/env python

'''
Back at the late 70's my cousin Peter showed me a gadget-game in which,
I think, the player had a paddle trying to catch balls from falling.

This version however is more like a pool game as shown from above.

Started coding at 3/20/2010 and finished at 12/17/2012 !!!
This game was a side project.
'''

#-------------------Imports-------------------
import pygame
from pygame.locals import *
from os import path
from random import randint
from math import cos, sin, atan, atan2, radians, pi, sqrt
from sys import platform

#-------------------Constants-------------------
VERSION = '0.2'
_FONT = 'space age.ttf'
DATA_FOLDER = '70s_data'
SIZE = (350,700)
BALL_DIMENSION = 18
BALL_ENTRY_POINT = BALL_DIMENSION * 1.5
NUMBER_OF_BALLS = 10
CLOCK = pygame.time.Clock()
FURTHER_FACTOR = 1
PLATFORM = platform

#-------------------Global functions-------------------
def display_some_text(text,size,place,background,orientation):
    font = pygame.font.Font(path.join(DATA_FOLDER,_FONT), size)
    t = font.render(text, 0, Color("yellow"))
    trect = t.get_rect()
    if orientation == 0:
        trect.left = place[0]
        trect.top = place[1]
    elif orientation == 1:
        trect.centerx = place[0]
        trect.centery = place[1]
    elif orientation == 2:
        trect.right = place[0]
        trect.top = place[1]
    background.blit(t, trect)

def _time(miliseconds):
    # Derived from 'How to think like a computer scientist - Learning with Python'
    seconds = miliseconds / 1000
    hours = (seconds / 3600) % 24
    minutes = (seconds % 3600) / 60
    seconds = seconds % 60

    h = 2 - len(str(hours))
    m = 2 - len(str(minutes))
    s = 2 - len(str(seconds))

    h = h * '0' + str(hours)
    m = m * '0' + str(minutes)
    s = s * '0' + str(seconds)

    return h+':'+m+':'+s

#-------------------Classes-------------------
class rolling_ball(pygame.sprite.Sprite):
    image = None
    def __init__(self,index):
        pygame.sprite.Sprite.__init__(self)
        if rolling_ball.image is None:
            rolling_ball.image = pygame.Surface((BALL_DIMENSION, BALL_DIMENSION)).convert()
            rolling_ball.image.fill(Color("black"))
            rolling_ball.image.lock()
            pygame.draw.circle(rolling_ball.image,Color("yellow"),(BALL_DIMENSION/2, BALL_DIMENSION/2), BALL_DIMENSION/2)
            rolling_ball.image.unlock()
        self.image = rolling_ball.image
        self.rect = self.image.get_rect()
        self.rect.topleft = (randint(BALL_ENTRY_POINT,SIZE[0] - BALL_ENTRY_POINT),randint(-SIZE[1],0))
        self.x_direction = 1
        self.index = index
        self.velocity = randint(4,14)
        self.angle = 90
        self.collides_with = -1
    def update(self):
        self.dx = self.velocity * cos(radians(self.angle)) * self.x_direction
        self.dy = self.velocity * sin(radians(self.angle))
        self.rect = self.rect.move(self.dx,self.dy)
    def kill(self):
        self.__init__(self.index)

class gameplay:
    def __init__(self):
        # Create the ball group and add balls
        self.ball_group = pygame.sprite.RenderUpdates()
        for x in range(NUMBER_OF_BALLS):
            self.ball_group.add(rolling_ball(x))
        # Create the other groups
        self.p = paddle()
        self.paddle_group = pygame.sprite.RenderUpdates()
        self.paddle_group.add(self.p)
        self.e = end_line()
        self.end_group = pygame.sprite.GroupSingle()
        self.end_group.add(self.e)
        self.missile_group = pygame.sprite.RenderUpdates()
        self.channel = pygame.mixer.Channel(2)
        self.sound = pygame.mixer.Sound(path.join(DATA_FOLDER,'clunk.ogg'))

    def update(self):
        for ball in self.ball_group:
            ball.collides_with = -1
            # Keep the balls in the playground area
            if ball.rect.left <= 0:
                ball.rect.left = 0
                ball.x_direction *= -1
            elif ball.rect.right >= SIZE[0]:
                ball.rect.right = SIZE[0]
                ball.x_direction *= -1

            for _ball in pygame.sprite.spritecollide(ball,self.ball_group,False):
                if ball.index != _ball.index:
                    if _ball.rect.top >= 0 and ball.rect.top >= 0:
                        if not ball.collides_with == _ball.index and not _ball.collides_with == ball.index:
                            ball.collides_with = _ball.index
                            _ball.collides_with = ball.index
                            # First find the impact angle using the atan2 function
                            impact_angle,c2 = self.get_impact_angle(ball.rect,_ball.rect)
                            # Then analyze the impact for every ball
                            o = self.analyze_impact(ball,impact_angle)
                            _o = self.analyze_impact(_ball,impact_angle)
                            # And the quantity of movement for each impact axis is
                            ball.x_velocity = o[0] * ball.velocity
                            ball.y_velocity = o[2] * ball.velocity
                            _ball.x_velocity = _o[0] * _ball.velocity
                            _ball.y_velocity = _o[2] * _ball.velocity
                            # The two balls exchange their x quantities according to the pool theory
                            temp = ball.x_velocity
                            ball.x_velocity = _ball.x_velocity
                            _ball.x_velocity = temp
                            # Of course the two balls exchange their x angles also
                            temp = o[1]
                            o[1] = _o[1]
                            _o[1] = temp
                            # Now find the new velocity of each ball with the Pythagorean theorem
                            ball.velocity = int(round(sqrt(ball.x_velocity**2 + ball.y_velocity**2)))
                            _ball.velocity = int(round(sqrt(_ball.x_velocity**2 + _ball.y_velocity**2)))
                            # A little bit of correction here
                            if ball.velocity < 2: ball.velocity = 2
                            if _ball.velocity < 2: _ball.velocity = 2
                            # Then for each ball, find the angle between the x and y quantities
                            ball.theta = int(round(atan(ball.y_velocity/ball.x_velocity) * 180 / pi))
                            _ball.theta = int(round(atan(_ball.y_velocity/_ball.x_velocity) * 180 / pi))
                            # Next compare the x and y angles
                            r =  self.compare_angles(o[1],o[3])
                            _r = self.compare_angles(_o[1],_o[3])
                            # Next, find for each ball its new angle
                            ball.angle = int(round(o[1] + ball.theta * r))
                            _ball.angle = int(round(_o[1] + _ball.theta * _r))
                            # And correct them
                            ball.angle = self.correct_angle(ball.angle)
                            _ball.angle = self.correct_angle(_ball.angle)
                            # After the impact, the balls must separate
                            if c2 == 0:
                                beta = 5 * cos(radians(ball.angle))
                                gama = 5 * sin(radians(ball.angle))
                                ball.rect.move_ip(beta,gama)
                                _beta = 5 * cos(radians(_ball.angle))
                                _gama = 5 * sin(radians(_ball.angle))
                                _ball.rect.move_ip(_beta,_gama)
                            else:
                                if c2 == 1:
                                    a2 = ball.rect
                                    a3 = ball.angle
                                    a4 = ball.velocity
                                    a5 = ball.x_direction
                                elif c2 == -1:
                                    a2 = _ball.rect
                                    a3 = _ball.angle
                                    a4 = _ball.velocity
                                    a5 = _ball.x_direction
                                beta = int(round(cos(radians(a3)) * a4 * FURTHER_FACTOR * a5))
                                gama = int(round(sin(radians(a3)) * a4 * FURTHER_FACTOR))
                                a2.move_ip(beta,gama)
                            self.channel.play(self.sound)
 
        self.missile_group.update()
        self.paddle_group.update()
        self.end_group.update()
        self.ball_group.update()

    def get_impact_angle(self,r1,r2):
        c = cmp(r1.centery, r2.centery)
        if c == 0:
            impact_angle = 0
        else:
            if c == 1:
                a = r1
                b = r2
            elif c == -1:
                a = r2
                b = r1
            _y = a.centery - b.centery
            _x = a.centerx - b.centerx
            impact_angle = int(round(atan2(_y,_x) * 180 / pi))
        return impact_angle, c

    def correct_angle(self,angle):
        while angle > 360:
            angle -= 360
        if 160 < angle < 270:
            angle = 160
        elif 270 <= angle <= 360 or 0 <= angle <= 20:
            angle = 20
        return angle

    def analyze_impact(self,ball,impact_angle):
        if impact_angle == 0:
            if 0 <= ball.angle <= 90:
                ball._angle =  ball.angle
                ball._x_angle = 0
                ball._y_angle = 90
            elif 90 < ball.angle <= 180:
                ball._angle =  180 - ball.angle
                ball._x_angle = 180
                ball._y_angle = 90
        elif impact_angle == 90:
            if 0 <= ball.angle <= 90:
                ball._angle =  90 - ball.angle
                ball._x_angle = 90
                ball._y_angle = 0
            elif 90 < ball.angle <= 180:
                ball._angle =  ball.angle - 90
                ball._x_angle = 90
                ball._y_angle = 180
        elif 0 < impact_angle < 90:
            if 0 <= ball.angle <= impact_angle:
                ball._angle =  impact_angle - ball.angle
                ball._x_angle = impact_angle
                ball._y_angle = impact_angle + 270
            elif impact_angle < ball.angle <= impact_angle + 90:
                ball._angle =  ball.angle - impact_angle
                ball._x_angle = impact_angle
                ball._y_angle = impact_angle + 90
            elif impact_angle + 90 < ball.angle <= 180:
                ball._angle =  180 - (ball.angle - impact_angle)
                ball._x_angle = impact_angle + 180
                ball._y_angle = impact_angle + 90
        elif 90 < impact_angle < 180:
            if 0 <= ball.angle <= impact_angle - 90:
                ball._angle =  180 - impact_angle + ball.angle
                ball._x_angle = impact_angle + 180
                ball._y_angle = impact_angle - 90
            elif impact_angle - 90 < ball.angle <= impact_angle:
                ball._angle =   impact_angle - ball.angle
                ball._x_angle = impact_angle
                ball._y_angle = impact_angle - 90
            elif impact_angle < ball.angle <= 180:
                ball._angle =  ball.angle - impact_angle
                ball._x_angle = impact_angle
                ball._y_angle = impact_angle + 90
        ball._x = cos(radians(ball._angle))
        ball._y = sin(radians(ball._angle))
        return [ball._x, ball._x_angle, ball._y, ball._y_angle]

    def compare_angles(self,x,y):
        if 270 <= x <= 360:
            r = 1
        else:
            if x > y:
                r = -1
            else:
                r = 1
        return r
                
class star(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.Surface((2,2)).convert()
        self.rect = self.image.get_rect()
        self.rect = pygame.draw.rect(self.image, Color('yellow'), self.rect)
        self.rect = self.rect.move(randint(0,SIZE[0]),randint(0,SIZE[1]))
        self.x = 0
    def update(self):
        if 0 <= self.x <= 20:
            self.x = self.x + 1
        else:
            self.__init__()

class paddle(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.Surface((80, 20)).convert()
        self.image.fill(Color("yellow"))
        self.rect = self.image.get_rect()
        self.rect = self.rect.move(0, 550)
        self.has_moved = ""
        self.step = 7
        self.channel = pygame.mixer.Channel(0)
        self.sound = pygame.mixer.Sound(path.join(DATA_FOLDER,'shoot.ogg'))
        self.channel2 = pygame.mixer.Channel(1)
        self.sound2 = pygame.mixer.Sound(path.join(DATA_FOLDER,'elec-crystal.ogg'))
        self.has_fired = 0
        self.cannon_is_drawn = 0
    def draw_cannon(self,score):
        if score > 0 and not self.cannon_is_drawn:
            self.image.fill(Color("black"),(35,0,10,3))
            self.cannon_is_drawn = 1
        elif score <= 0 and self.cannon_is_drawn:
            self.image.fill(Color("yellow"),(35,0,10,3))
            self.cannon_is_drawn = 0
    def update(self):
        if self.has_fired:
            self.channel2.play(self.sound2)
            self.has_fired = 0
        if self.has_moved == "right" and self.rect.right < SIZE[0]:
            self.rect = self.rect.move(self.step, 0)
        elif self.has_moved == "left" and self.rect.left > 0:
            self.rect = self.rect.move(-self.step, 0)
    def kill(self):
        self.channel.play(self.sound)

class end_line(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.Surface((SIZE[0], 4)).convert()
        self.rect = self.image.get_rect()
        self.rect = pygame.draw.rect(self.image, Color("yellow"), self.rect)
        self.rect = self.rect.move(0, 575)
    def update(self):
        pass
    def kill(self):
        pass

class missile(pygame.sprite.Sprite):
    def __init__(self,position):
        pygame.sprite.Sprite.__init__(self)
        self.position = position
        self.image = pygame.Surface((6, 10)).convert()
        self.image.fill(Color("yellow"))
        self.rect = self.image.get_rect()
        self.rect.midbottom = self.position
        self.velocity = 14
        self.channel = pygame.mixer.Channel(4)
        self.sound = pygame.mixer.Sound(path.join(DATA_FOLDER,'glasses2.ogg'))
    def update(self):
        if self.rect.bottom > 0:
            self.rect = self.rect.move(0,-self.velocity)
        else:
            self.kill()
    def kill(self):
        if self.rect.bottom > 0:
            self.sound.play()
        pygame.sprite.Sprite.kill(self)

class board:
    def __init__(self,x,y):
        self.board = pygame.Surface((180,20))
        self.board.fill(Color("black"))
        self.board_rect = self.board.get_rect()
        self.board_rect.topleft = (x,y)
    def write_on_board(self,text,screen):
        self.board.fill(Color("black"))
        display_some_text(str(text),25,(1,1),self.board,0)
        screen.blit(self.board,self.board_rect)

#-------------------Game functions-------------------
def welcome(screen, background):
    musicfile = path.join(DATA_FOLDER,'welcome.mid')
    pygame.mixer.music.load(musicfile)
    pygame.mixer.music.play(-1)

    # First welcome screen
    background.fill(Color("black"))
    _size = 35
    _size2 = 30
    _start = 120
    d = 4
    display_some_text("A GAME FROM" ,_size ,(SIZE[0]/2,_start+_size*1.5),background,1)
    display_some_text("THE 70's"    ,_size ,(SIZE[0]/2,_start+_size*3)  ,background,1)
    display_some_text('Press'       ,_size2,(SIZE[0]/2,_start+_size2*11),background,1)
    display_some_text('any key...'  ,_size2,(SIZE[0]/2,_start+_size2*13),background,1)

    group = []
    for x in range(40):
        group.append(star())
    allsprites = pygame.sprite.Group((group))

    running = 1
    while running:
        CLOCK.tick(120)
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                return 0
            elif event.type == KEYDOWN or event.type == MOUSEBUTTONDOWN:
                running = 0
        allsprites.update()       
        screen.blit(background, (0, 0))
        allsprites.draw(screen)
        pygame.display.update()

    # Second welcome screen
    background.fill(Color("black"))
    _size2 = 30
    _start = 50
    d = 30
    display_some_text("Try to catch"   ,_size2,(d,_start),background,0)
    display_some_text("the rolling"    ,_size2,(d,_start+_size2),background,0)
    display_some_text("balls with."    ,_size2,(d,_start+_size2*2),background,0)
    display_some_text("your paddle."   ,_size2,(d,_start+_size2*3),background,0)
    display_some_text('Z, X or left'   ,_size2,(d,_start+_size2*5),background,0)
    display_some_text('and right'      ,_size2,(d,_start+_size2*6),background,0)
    display_some_text('arrows to'      ,_size2,(d,_start+_size2*7),background,0)
    display_some_text('move.'          ,_size2,(d,_start+_size2*8),background,0)
    display_some_text('Once the'       ,_size2,(d,_start+_size2*10),background,0)
    display_some_text('score is'       ,_size2,(d,_start+_size2*11),background,0)
    display_some_text('above zero,'    ,_size2,(d,_start+_size2*12),background,0)
    display_some_text('use the'        ,_size2,(d,_start+_size2*13),background,0)
    display_some_text('<ctrl> keys'    ,_size2,(d,_start+_size2*14),background,0)
    display_some_text('to fire at'     ,_size2,(d,_start+_size2*15),background,0)
    display_some_text('the balls.'     ,_size2,(d,_start+_size2*16),background,0)
    display_some_text('Press any'      ,_size2,(d,_start+_size2*18),background,0)
    display_some_text('key...'         ,_size2,(d,_start+_size2*19),background,0)

    running = 1
    while running:
        CLOCK.tick(120)
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                return 0
            elif event.type == KEYDOWN or event.type == MOUSEBUTTONDOWN:
                running = 0
        allsprites.update()       
        screen.blit(background, (0, 0))
        allsprites.draw(screen)
        pygame.display.update()

    pygame.mixer.music.stop()
    del group, _size, _size2, _start, d, running
    return 1


def play(screen, background):
    background.fill(Color("black"))
    display_some_text('SCORE:',25,(10,600),background,0)
    display_some_text('TIME:',25,(10,645),background,0)
    screen.blit(background, [0, 0])
    pygame.display.update()

    musicfile = path.join(DATA_FOLDER,'play.mid')
    pygame.mixer.music.load(musicfile)
    pygame.mixer.music.set_volume(0.4)
    pygame.mixer.music.play(-1)

    a = gameplay()
    _end_line = a.end_group.sprites()[0].rect

    time = 0
    time_board = board(150,645)

    score = 0
    score_board = board(150,600)

    var = 1
    while score < 100:
        time += CLOCK.tick(120)
        t = _time(time)
        time_board.write_on_board(t,screen)
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                var = 0
                score = 1000
            elif event.type == KEYDOWN:
                if event.key == K_RCTRL or event.key == K_LCTRL:
                    if score > 0:
                        m = missile(a.p.rect.midbottom)
                        a.missile_group.add(m)
                        a.p.has_fired = 1
                        score -= 1
                        score_board.write_on_board(score,screen)
            if pygame.key.get_pressed()[275] or pygame.key.get_pressed()[120]:
                a.p.has_moved = "right"
            elif pygame.key.get_pressed()[276] or pygame.key.get_pressed()[122]:
                a.p.has_moved = "left"
            elif not pygame.key.get_pressed()[275] or not pygame.key.get_pressed()[120]:
                a.p.has_moved = ""
            elif not pygame.key.get_pressed()[276] or not pygame.key.get_pressed()[122]:
                a.p.has_moved = ""

        if pygame.sprite.groupcollide(a.missile_group, a.ball_group, 1, 1):
            score += 3
            score_board.write_on_board(score,screen)
        if pygame.sprite.groupcollide(a.paddle_group, a.ball_group, 1, 1):
            score += 2
            score_board.write_on_board(score,screen)
        if pygame.sprite.groupcollide(a.end_group, a.ball_group, 1, 1):
            score -= 1
            score_board.write_on_board(score,screen)
        a.update()
        a.p.draw_cannon(score)
        r1 = a.ball_group.draw(screen)
        r2 = a.paddle_group.draw(screen)
        r3 = a.missile_group.draw(screen)
        a.end_group.draw(screen)
        pygame.display.update()
        a.ball_group.clear(screen, background)
        a.paddle_group.clear(screen, background)
        a.missile_group.clear(screen, background)

    pygame.mixer.music.stop()
    del a, t, time_board, score, score_board
    return [var,time]

def scores(screen, background, time):
    musicfile = path.join(DATA_FOLDER,'scores.mid')
    pygame.mixer.music.load(musicfile)
    pygame.mixer.music.set_volume(0.2)
    pygame.mixer.music.play(-1)

    background.fill(Color("black"))
    display_some_text('SCORES',35,(175,40),background,1)
    display_some_text('O<K>  C<R>EDITS',25,(175,660),background,1)

    f = open(path.join(DATA_FOLDER,'scores.txt'),'a')
    if PLATFORM.startswith('win'):
        f.write(str(time)+'\n')
    else:
        f.write(str(time)+'\r\n')
    f.close()

    f = open(path.join(DATA_FOLDER,'scores.txt'))
    f2 = f.readlines()
    f3 = [int(x[:len(x)-1]) for x in f2]
    f3.sort()
    f.close()

    i = f3.index(time) + 1
    l = len(f3)

    x1 = 70
    x2 = 240
    y = 100
    y_move = 55
    size = 30
    f4 = []
    if l <= 10:
        f4 = f3
        count = 1
    else:
        if i <= 10:
            f4 = f3[:10]
            count = 1
        else:
            f4 = f3[i-5:i+5]
            count = i-4
    for score in f4:
        if count == i:
            num = 'You'
        else:
            num = str(count)
        display_some_text(num,size,(x1,y),background,1)
        display_some_text(_time(score),size,(x2,y),background,1)
        y += y_move
        count += 1

    group = []
    for x in range(40):
        group.append(star())
    allsprites = pygame.sprite.Group((group))

    running = 1
    while running:
        CLOCK.tick(120)
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                return 0
            elif event.type == KEYDOWN:
                if event.key == K_k:
                    return 1
                elif event.key == K_r:
                    return 2
        allsprites.update()       
        screen.blit(background, (0, 0))
        allsprites.draw(screen)
        pygame.display.update()

    pygame.mixer.music.stop()
    del f2,f3,f4,i,l,x,x1,x2,y,y_move,size,count,num,group

def _credits(screen, background):
    musicfile = path.join(DATA_FOLDER,'credits.mid')
    pygame.mixer.music.load(musicfile)
    pygame.mixer.music.play(-1)

    background.fill(Color("black"))
    display_some_text('O<K>',25,(175,660),background,1)

    f = open(path.join(DATA_FOLDER,'credits.txt'),"r")
    text = f.read()
    f.close()
    s = ''
    y = 20
    x = 175

    for t in text:
        if t != '\n':
            s = s + t
        else:
            display_some_text(s,20,(x,y),background,1)
            s = ''
            y = y + 20

    group = []
    for x in range(40):
        group.append(star())
    allsprites = pygame.sprite.Group((group))

    running = 1
    while running:
        CLOCK.tick(120)
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                return 0
            elif event.type == KEYDOWN:
                if event.key == K_k:
                    return 1
        allsprites.update()       
        screen.blit(background, (0, 0))
        allsprites.draw(screen)
        pygame.display.update()

    pygame.mixer.music.stop()
    del s,y,x,t,group

def main():
    pygame.init()
    screen = pygame.display.set_mode(SIZE)
    background = pygame.Surface(screen.get_size()).convert()
    pygame.display.set_caption("70's v" + VERSION)

    running = 1
    while running:
        a = welcome(screen, background)
        while a:
            b = play(screen, background)
            if b[0]:
                c = scores(screen, background, b[1])
                if c == 1:
                    break
                elif c == 2:
                    d = _credits(screen, background)
                    if d:
                        break
                    else:
                        running = 0
                        break
                else:
                    running = 0
                    break
            else:
                running = 0
                break
        else:
            running = 0
    pygame.quit()

if __name__ == '__main__': main()
