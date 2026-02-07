import pygame
import sys
import random

pygame.init()

WIDTH = 1080
HEIGHT = 720
screen = pygame.display.set_mode((WIDTH,HEIGHT))
pygame.display.set_caption("Her er caption")
karakter_bilde = pygame.image.load("bilder/Soldat.png")

clock = pygame.time.Clock()
FPS = 60

CENTER_x = WIDTH // 2
CENTER_y = HEIGHT // 2


class Soldat:
    def __init__(self):
        self._status = "Soldat"
        self._health = 100
        self._healthbar = pygame.Rect(600,100,self._health,40)
        self._xakse= 100
        self._yakse= 100
        self._damage = 10
        self._speed = 5
        self._size = 50
        try:
            self._sprite = pygame.transform.scale(karakter_bilde, (self._size, self._size))
        except Exception:
            self._sprite = None
    
    def økHelse(self,helse):
        self._health += helse
        self._healthbar.width = self._health
    
    def synkHelse(self):
        self._health -= 1
        self._healthbar.width = self._health 

    def lagSoldat(self):
        if self._health > 500:
            return Tank(self._xakse, self._yakse)
        
    def sjekkDod(self):
        if self._health <= 0:
            return True

spiller = Soldat()
            
class Tank(Soldat):
    def __init__(self, x=None, y=None):
        super().__init__()
        self._health = 500
        self._size = 100
        self._healthbar.width = self._health
        if x is not None:
            self._xakse = x
        if y is not None:
            self._yakse = y
        try:
            self._sprite = pygame.transform.scale(karakter_bilde, (self._size, self._size))
        except Exception:
            self._sprite = None

class Fiende:
    def __init__(self,size,health):
        self._status = "Fiende"
        self._health = health
        self._dmg = 5
        self._size = size
        self._xakse = 500
        self._yakse = 500
        self._flereFiender = []

class FiendeTank(Fiende):
    def __init__(self, size, health=600):
        super().__init__(size, health)
        self._farger = (255,0,255)

fiende = Fiende(100,200)

bakgrunnsbilde = pygame.image.load("bilder/bacground.jpg")

fiender = [fiende]

run = True
while run:
    clock.tick(FPS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

    keys = pygame.key.get_pressed()
    
    if keys[pygame.K_w]:
        spiller._yakse-= spiller._speed
    if keys[pygame.K_s]:
        spiller._yakse+= spiller._speed
    if keys[pygame.K_a]:
        spiller._xakse-= spiller._speed
    if keys[pygame.K_d]:
        spiller._xakse += spiller._speed

    camera_x = spiller._xakse - CENTER_x
    camera_y = spiller._yakse - CENTER_y
    
    screen.fill((255,255,255))
    
    ny_spiller = spiller.lagSoldat()
    if ny_spiller:
        spiller = ny_spiller
    
    player_pos = (CENTER_x - spiller._size // 2, CENTER_y - spiller._size // 2)
    player_rect = pygame.Rect(player_pos[0], player_pos[1], spiller._size, spiller._size)
    
    for f in fiender[:]:
        enemy_rect = pygame.Rect(f._xakse - camera_x, f._yakse - camera_y, f._size, f._size)
        tank_rect = pygame.Rect(f._xakse - camera_x, f._yakse - camera_y, f._size, f._size)
        if player_rect.colliderect(enemy_rect) or player_rect.colliderect(tank_rect):
            if f._health < spiller._health:
                spiller._health += f._health
                spiller._healthbar.width = spiller._health
                fiender.remove(f)
            elif f._health > spiller._health:
                spiller.synkHelse()
                sjekk = spiller.sjekkDod()
                if sjekk == True:
                    player_pos = (0,0)
                    run = False
            else:
                spiller._xakse -= 50
                spiller._yakse -= 50
        
        if f in fiender:
            pygame.draw.rect(screen,(255,0,0),enemy_rect)
            if isinstance(f, FiendeTank):
                pygame.draw.rect(screen, f._farger, tank_rect)
   
    if random.random() < 0.05:
        ny_fiende = Fiende(100, random.randint(10,110))
        ny_fiende._xakse = random.randint(0, 2000)
        ny_fiende._yakse = random.randint(0, 1500)
        fiender.append(ny_fiende)
        if random.random() < 0.01:
            ny_Tank = FiendeTank(250)
            ny_Tank._xakse = random.randint(0,2000)
            ny_Tank._yakse = random.randint(0,1500)
            fiender.append(ny_Tank)
        
    pygame.draw.rect(screen,(0,255,0),spiller._healthbar)
    
    if getattr(spiller, '_sprite', None) is not None:
        screen.blit(spiller._sprite, player_pos)
    else:
        if isinstance(spiller, Tank):
            pygame.draw.rect(screen,(255,255,0),player_rect)
        else:
            pygame.draw.rect(screen,(0,255,255),player_rect)
    
    pygame.display.flip()

pygame.quit()
sys.exit()