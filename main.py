import pygame
import sys
import random

#Starter pygame
pygame.init()

WIDTH = 1080
HEIGHT = 720
screen = pygame.display.set_mode((WIDTH,HEIGHT))
pygame.display.set_caption("Her er caption")
karakter_bilde = pygame.image.load("bilder/Soldat.png")

#Klokke objekt
clock = pygame.time.Clock()
FPS = 60

CENTER_x = WIDTH // 2
CENTER_y = HEIGHT // 2



#Spiller

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
        # Cache a scaled sprite for this character size
        try:
            self._sprite = pygame.transform.scale(karakter_bilde, (self._size, self._size))
        except Exception:
            # If loading/scaling fails, fall back to None and use rect drawing
            self._sprite = None
    
    def økHelse(self,helse):
        self._health += helse # Øk helsen med 10 når du kolliderer
        self._healthbar.width = self._health  # Oppdater healthbar bredden
    
    def synkHelse(self):
        self._health -= 1
        self._healthbar.width = self._health 

    def lagSoldat(self):
        if self._health > 500:
            # Return a Tank that preserves the current world position
            return Tank(self._xakse, self._yakse)
        
    def sjekkDod(self):
        if self._health <= 0:
            return True

spiller = Soldat()
            
class Tank(Soldat):
    def __init__(self, x=None, y=None):
        # Initialize base attributes then override as needed
        super().__init__()
        self._health = 700
        self._size = 100
        self._healthbar.width = self._health
        # If conversion provides a position, keep it instead of resetting to default
        if x is not None:
            self._xakse = x
        if y is not None:
            self._yakse = y
        # Rescale sprite to tank size
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

# Liste med alle fiender
fiender = [fiende]

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

    # Oppdater kameraposisjon
    camera_x = spiller._xakse - CENTER_x
    camera_y = spiller._yakse - CENTER_y
    
    screen.fill((255,255,255))
    
    # Sjekk om spiller skal bli Tank
    ny_spiller = spiller.lagSoldat()
    if ny_spiller:
        spiller = ny_spiller
    
    # Opprett posisjon og rect ETTER spiller er oppdatert (centered)
    player_pos = (CENTER_x - spiller._size // 2, CENTER_y - spiller._size // 2)
    player_rect = pygame.Rect(player_pos[0], player_pos[1], spiller._size, spiller._size)
    
    # Tegn alle fiender og sjekk collision
    for f in fiender[:]:  # Bruk kopi av listen
        enemy_rect = pygame.Rect(f._xakse - camera_x, f._yakse - camera_y, f._size, f._size)
        tank_rect = pygame.Rect(f._xakse - camera_x, f._yakse - camera_y, f._size, f._size)
        if player_rect.colliderect(enemy_rect) or player_rect.colliderect(tank_rect):
            if f._health < spiller._health:
                spiller._health += f._health
                spiller._healthbar.width = spiller._health  # Oppdater healthbar bredde
                fiender.remove(f)  # Fjern fienden etter at du øker helsen
            elif f._health > spiller._health:
                spiller.synkHelse()
                sjekk = spiller.sjekkDod()
                if sjekk == True:
                    player_pos = (0,0)
                    run = False
                    
            
            
            else:
                # Når helsen er lik, beveg spiller tilbake
                spiller._xakse -= 50
                spiller._yakse -= 50
        
        # Tegn fienden
        if f in fiender:  # Tegn bare hvis fienden ikke er fjernet
            # Standard fiende-farge
            pygame.draw.rect(screen,(255,0,0),enemy_rect)
            # Hvis fienden er en FiendeTank, tegn med dens farge (størrelse samme som enemy_rect)
            if isinstance(f, FiendeTank):
                pygame.draw.rect(screen, f._farger, tank_rect)
    
    # Lag nye fiender tilfeldig (1/100 sjanse hver frame)
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
        
       

    # Tegn healthbar
    pygame.draw.rect(screen,(0,255,0),spiller._healthbar)
    
    # Tegn spiller/tank som bilde (fallback to rect if sprite missing)
    if getattr(spiller, '_sprite', None) is not None:
        screen.blit(spiller._sprite, player_pos)
    else:
        if isinstance(spiller, Tank):
            pygame.draw.rect(screen,(255,255,0),player_rect)  # Gul for Tank
        else:
            pygame.draw.rect(screen,(0,255,255),player_rect)  # Cyan for Soldat
    
    pygame.display.flip()       #Oppaterer display



#Slutter pygame
pygame.quit()
sys.exit()