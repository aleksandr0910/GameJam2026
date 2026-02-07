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
FPS = 100

font = pygame.font.Font(None, 24)

CENTER_x = WIDTH // 2
CENTER_y = HEIGHT // 2


class Soldat:
    def __init__(self):
        self._status = "Soldat"
        self._maxhealth = 100
        self._health = 40
        self._healthbar = pygame.Rect(20,100,self._health,40)
        self._xakse= 100
        self._yakse= 100
        self._damage = 10
        self._speed = 5
        self._size = 50
        self._combat_timer = 0
        self._combat_cooldown = 30
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
        if self._health >= self._maxhealth:
            return Tank(self._xakse, self._yakse, self._health)
        
    def sjekkDod(self):
        if self._health <= 0:
            return True

spiller = Soldat()
            
class Tank(Soldat):
    def __init__(self, x=None, y=None, current_health=None):
        super().__init__()
        self._maxhealth = 200
        if current_health is not None:
            self._health = current_health
        else:
            self._health = self._maxhealth
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
    def __init__(self, size, health=None):
        self._status = "Fiende"
        # If no health provided, pick a random value between 10 and 100
        if health is None:
            health = random.randint(10, 100)
        self._health = health
        # keep a fixed max so the bar shows proportion of 0..100
        self._maxhealth = 100
        self._dmg = 5
        self._size = size
        self._xakse = 500
        self._yakse = 500


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
    health_farge = (0,255,0)   
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
        health_farge = (255,0,10)
        spiller = ny_spiller
    if spiller._combat_timer > 0:
        spiller._combat_timer -= 1

    if isinstance(spiller, Tank) and spiller._health < 100:
        soldat_novo = Soldat()
        soldat_novo._xakse = spiller._xakse
        soldat_novo._yakse = spiller._yakse
        soldat_novo._health = spiller._health
        soldat_novo._healthbar.width = soldat_novo._health
        health_farge = (0,255,0)
        spiller = soldat_novo
        
    player_pos = (CENTER_x - spiller._size // 2, CENTER_y - spiller._size // 2)
    player_rect = pygame.Rect(player_pos[0], player_pos[1], spiller._size, spiller._size)
   

    for f in fiender[:]:
        enemy_rect = pygame.Rect(f._xakse - camera_x, f._yakse - camera_y, f._size, f._size)
        tank_rect = pygame.Rect(f._xakse - camera_x, f._yakse - camera_y, f._size, f._size)
        enemy_healthbar = None

        if player_rect.colliderect(enemy_rect) or player_rect.colliderect(tank_rect):
            # combat only applies when cooldown timer reached
            if spiller._combat_timer <= 0:
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
                spiller._combat_timer = spiller._combat_cooldown
        
        if f in fiender:
            pygame.draw.rect(screen,(255,0,0),enemy_rect)
            hb_width = max(24, f._size)
            hb_height = 8
            hb_x = f._xakse - camera_x
            hb_y = f._yakse - camera_y - hb_height - 6
            bg_rect = pygame.Rect(hb_x, hb_y, hb_width, hb_height)
            fill_w = hb_width
            if getattr(f, '_maxhealth', None) and f._maxhealth > 0:
                fill_w = max(0, int(f._health / f._maxhealth * hb_width))
            fill_rect = pygame.Rect(hb_x, hb_y, fill_w, hb_height)
            pygame.draw.rect(screen, (80,80,80), bg_rect)
            pygame.draw.rect(screen, (200,40,40), fill_rect)
            if isinstance(f, FiendeTank):
                pygame.draw.rect(screen, f._farger, tank_rect)
   
    if random.random() < 0.9:
        ny_fiende = Fiende(100, random.randint(10,100))
        ny_fiende._xakse = random.randint(-20000, 20000)
        ny_fiende._yakse = random.randint(-15000, 15000)
        fiender.append(ny_fiende)
        if random.random() < 0.01:
            ny_Tank = FiendeTank(250)
            ny_Tank._xakse = random.randint(-20000,20000)
            ny_Tank._yakse = random.randint(-15000,15000)
            fiender.append(ny_Tank)
    
   

    pygame.draw.rect(screen,(health_farge),spiller._healthbar)
    
    health_text = font.render(f"Health: {spiller._health}", True, (0, 0, 0))
    screen.blit(health_text, (spiller._healthbar.x, spiller._healthbar.y - 25))
    
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