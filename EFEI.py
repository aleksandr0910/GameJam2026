import pygame
import sys

#Starter pygame
pygame.init()

WIDTH = 1080
HEIGHT = 720
screen = pygame.display.set_mode((WIDTH,HEIGHT))
pygame.display.set_caption("Her er caption")

#Klokke objekt
clock = pygame.time.Clock()
FPS = 60

#Spiller
class Spiller:
    def __init__(self):
        self._xakse= 100
        self._yakse= 100
        self._speed = 5
        self._size = 50

spiller = Spiller()

class Fiende:
    def __init__(self,size):
        self._health = 100
        self._dmg = 5
        self._size = size
        self._xakse = 500
        self._yakse = 500
fiende = Fiende(100)

run = True
while run:
    clock.tick(FPS)


    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

    #Tastaturklikk
    keys = pygame.key.get_pressed()
    
    if keys[pygame.K_w]:
        spiller._yakse-= spiller._speed
    if keys[pygame.K_s]:
        spiller._yakse+= spiller._speed
    if keys[pygame.K_a]:
        spiller._xakse-= spiller._speed
    if keys[pygame.K_d]:
        spiller._xakse += spiller._speed

    
    

    screen.fill((255,255,255))
    pygame.draw.rect(screen,(0,255,0),(spiller._xakse,spiller._yakse,spiller._size, spiller._size))
    pygame.draw.rect(screen,(0,255,255),(fiende._xakse,fiende._yakse,fiende._size, fiende._size))

    
    

    pygame.display.flip()       #Oppaterer display



#Slutter pygame
pygame.quit()
sys.exit()