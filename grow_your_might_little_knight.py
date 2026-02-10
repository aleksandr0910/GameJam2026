import pygame
import sys
import random
import math
import os
from ui import UI, GAME_INTRO, GAME_PLAYING, GAME_PAUSED

# ================= FILSTI-HÅNDTERING =================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_path(rel_path):
    return os.path.join(BASE_DIR, rel_path).replace("\\", "/")

# ================= INITIALISERING =================
pygame.init()
pygame.mixer.init()

WIDTH, HEIGHT = 1280, 720
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Grow your might, little knight!")

GAME_BOSS = "BOSS_FIGHT"
GAME_OVER = "GAME_OVER"
GAME_VICTORY = "GAME_VICTORY"
CLOCK = pygame.time.Clock()
FPS = 60
CENTER_X, CENTER_Y = WIDTH // 2, HEIGHT // 2

shake_amount = 0

# ================= LYDEFFEKTER =================
sounds = {}
def load_sound(name, rel_path, volume=0.4):
    try:
        s = pygame.mixer.Sound(get_path(rel_path))
        s.set_volume(volume)
        sounds[name] = s
    except:
        sounds[name] = None

load_sound("slash", "lyder/slash.wav", 0.3)
load_sound("whirlwind", "lyder/whirlwind.wav", 0.4)
load_sound("dash", "lyder/dash.wav", 0.3)
load_sound("potion", "lyder/potion.wav", 0.5)
load_sound("lvl_up", "lyder/levelup.wav", 0.6)
load_sound("hurt", "lyder/hurt.wav", 0.3)
load_sound("enemy_death", "lyder/die.wav", 0.3)

def play_sfx(name):
    if name in sounds and sounds[name]:
        sounds[name].play()

# ================= FONTS =================
def get_font(size): return pygame.font.SysFont("georgia", size, bold=True)
FONT_XP = get_font(20); FONT_LVL = get_font(14); FONT_INFO = get_font(24)
FONT_UNLOCK = get_font(40); FONT_OVER = get_font(64); FONT_HUD = get_font(28)

ui = UI(SCREEN)
game_state = GAME_INTRO
DIR_ORDER = ["up", "left", "down", "right"]

# ================= SYSTEM-KLASSER =================
class FloatingText:
    def __init__(self, x, y, text, color=(0, 150, 255), stay=False):
        self.x, self.y, self.text, self.color = x, y, text, color
        self.timer = 180 if stay else 60
        self.alpha = 255
        self.stay = stay

    def update(self):
        if not self.stay: self.y -= 0.8
        self.timer -= 1
        if self.timer < 30: self.alpha = max(0, self.alpha - 8)

    def draw(self, surf, cx, cy):
        font = FONT_UNLOCK if self.stay else FONT_XP
        t = font.render(self.text, True, self.color)
        t.set_alpha(self.alpha)
        pos = (WIDTH//2 - t.get_width()//2, 150) if self.stay else (self.x-cx, self.y-cy)
        surf.blit(t, pos)

class FireParticle:
    def __init__(self, x, y, color=None):
        self.x, self.y = x, y
        self.timer, self.size = 40, random.randint(10, 15)
        self.color = color if color else (random.randint(200, 255), random.randint(50, 100), 20)
    def update(self, enemies, boss):
        self.timer -= 1; self.size *= 0.94
        rect = pygame.Rect(self.x-15, self.y-15, 30, 30)
        for e in enemies:
            if not e.dying and rect.colliderect(e.rect()): e.health -= 0.8
        if boss and rect.colliderect(boss.rect()): boss.health -= 1.2
    def draw(self, surf, cx, cy):
        if self.timer > 0: pygame.draw.circle(surf, self.color, (int(self.x-cx), int(self.y-cy)), int(self.size))

# ================= KART OG KOLLISJON =================
try:
    BG_MAP = pygame.image.load(get_path("bilder/world/world.png")).convert()
    TREE_LAYER = pygame.image.load(get_path("bilder/world/world_trees.png")).convert_alpha()
    BG_W, BG_H = BG_MAP.get_size()
except:
    BG_W, BG_H = 2000, 2000
    BG_MAP = pygame.Surface((BG_W, BG_H)); BG_MAP.fill((34, 139, 34))
    TREE_LAYER = pygame.Surface((BG_W, BG_H), pygame.SRCALPHA)

def is_walkable(x, y):
    if x < 15 or x > BG_W - 50 or y < 15 or y > BG_H - 70: return False
    try:
        c = BG_MAP.get_at((int(x), int(y)))
        if c.b > 130 and c.b > c.g: return False
        if c.r < 80 and c.g < 80 and c.b > 80: return False
    except: return False
    return True

def get_tree_spawn():
    for _ in range(100):
        tx, ty = random.randint(100, BG_W-100), random.randint(100, BG_H-100)
        try:
            if TREE_LAYER.get_at((int(tx + 32), int(ty + 50))).a > 50: return tx, ty
        except: continue
    return 400, 400

def get_safe_spawn():
    for _ in range(100):
        tx, ty = random.randint(100, BG_W-100), random.randint(100, BG_H-100)
        if is_walkable(tx + 32, ty + 50): return tx, ty
    return 1250, 450

def load_anim(rel_path, fw, fh, count):
    try:
        sheet = pygame.image.load(get_path(rel_path)).convert_alpha()
        anim = {}
        for i, d in enumerate(DIR_ORDER):
            frames = []
            y_off = i * fh if sheet.get_height() >= (i + 1) * fh else 0
            for col in range(count):
                frames.append(sheet.subsurface(pygame.Rect(col*fw, y_off, fw, fh)).copy())
            anim[d] = frames
        return anim
    except:
        s = pygame.Surface((fw, fh)); s.fill((255, 0, 255)); return {d: [s] for d in DIR_ORDER}

def load_whirlwind(rel_path):
    try:
        sheet = pygame.image.load(get_path(rel_path)).convert_alpha()
        return [sheet.subsurface(pygame.Rect(i*256, 0, 256, 256)).copy() for i in range(4)]
    except:
        return [pygame.Surface((256, 256), pygame.SRCALPHA) for _ in range(4)]

# ================= SPILLOBJEKTER =================
class Potion:
    def __init__(self, x=None, y=None): 
        self.x, self.y = (x, y) if (x and y) else get_safe_spawn()
        self.bob = random.random() * 10 
        try:
            self.image = pygame.image.load(get_path("bilder/world/potion.png")).convert_alpha()
            self.image = pygame.transform.scale(self.image, (24, 24))
        except: self.image = None
    def draw(self, surf, cx, cy):
        self.bob += 0.1; off = math.sin(self.bob) * 5
        if self.image: surf.blit(self.image, (self.x-cx-12, self.y-cy-12+off))
        else: pygame.draw.rect(surf, (200,0,0), (self.x-cx-8, self.y-cy-8+off, 16, 16))
    def rect(self): return pygame.Rect(self.x-15, self.y-15, 30, 30)

class Portal:
    def __init__(self, x, y): 
        self.x, self.y = x, y
        self.active = False
        self.timer = 0
        self.notified = False
    def draw(self, surf, cx, cy):
        if not self.active: return
        self.timer += 0.05
        for i in range(3):
            r = 40 + i * 15 + math.sin(self.timer + i) * 5
            pygame.draw.circle(surf, (150, 50, 255), (int(self.x-cx), int(self.y-cy)), int(r), 2)
    def rect(self): return pygame.Rect(self.x-40, self.y-40, 80, 80)

class Boss:
    def __init__(self):
        self.x, self.y, self.max_health, self.timer = WIDTH // 2, 250, 15000
        self.health = self.max_health
        self.phase = 0
        self.state, self.attack_cooldown, self.projectiles = "hover", 0, []
        try:
            self.sheet = pygame.image.load(get_path("bilder/world/boss.png")).convert_alpha()
            self.fw, self.fh = 208, 250 
            self.frames = [[self.sheet.subsurface(c*self.fw, r*self.fh, self.fw, self.fh) for c in range(4)] for r in range(2)]
        except: self.frames = None; self.fw, self.fh = 200, 250

    def update(self, player, effects):
        self.timer += 1; self.attack_cooldown -= 1
        self.phase = 0 if self.health > self.max_health // 2 else 1
        spd = 1.0 if self.phase == 0 else 1.8
        if self.attack_cooldown <= 0:
            self.state = random.choice(["hover", "charge", "shoot"])
            self.attack_cooldown = 110 if self.phase == 0 else 70
        if self.state == "hover":
            self.x = WIDTH//2 + math.cos(self.timer*0.04)*300; self.y = 250 + math.sin(self.timer*0.02)*50
        elif self.state == "charge":
            dx, dy = player.x-self.x, player.y-self.y; dist = math.hypot(dx, dy)
            if dist > 10: self.x += (dx/dist)*6*spd; self.y += (dy/dist)*6*spd
            else: self.state = "hover"
        elif self.state == "shoot":
            if self.timer % (20 if self.phase == 0 else 12) == 0:
                ang = math.atan2(player.y-self.y, player.x-self.x)
                self.projectiles.append({"x":self.x, "y":self.y, "vx":math.cos(ang)*7, "vy":math.sin(ang)*7, "t":180})
        for p in self.projectiles[:]:
            p["x"] += p["vx"]; p["y"] += p["vy"]; p["t"] -= 1
            if pygame.Rect(p["x"]-10, p["y"]-10, 20, 20).colliderect(player.rect()):
                player.take_damage(15, effects); self.projectiles.remove(p)
            elif p["t"] <= 0: self.projectiles.remove(p)

    def draw(self, surf):
        if self.frames:
            surf.blit(self.frames[self.phase][(self.timer//12)%4], (self.x-self.fw//2, self.y-self.fh//2))
        else: pygame.draw.circle(surf, (200,0,0), (int(self.x), int(self.y)), 80)
        for p in self.projectiles: pygame.draw.circle(surf, (255,0,255), (int(p["x"]), int(p["y"])), 10)
        pygame.draw.rect(surf, (40,0,0), (WIDTH//2-300, 20, 600, 20))
        pygame.draw.rect(surf, (255,0,0), (WIDTH//2-300, 20, 600*(self.health/self.max_health), 20))
    def rect(self): return pygame.Rect(self.x-80, self.y-100, 160, 200)

# ================= PLAYER =================
class Player:
    def __init__(self):
        self.animations = {
            "idle": load_anim("bilder/lpc/idle.png", 64, 64, 2),
            "walk": load_anim("bilder/lpc/walk.png", 64, 64, 9),
            "slash": load_anim("bilder/lpc/slash.png", 128, 128, 6),
            "hurt": load_anim("bilder/lpc/hurt.png", 64, 64, 6)
        }
        self.whirlwind_frames = load_whirlwind("bilder/effects/whirlwind.png")
        self.reset()

    def reset(self):
        self.x, self.y, self.state, self.direction = 1250, 450, "idle", "left"
        self.frame, self.timer, self.level, self.xp, self.xp_to_next = 0, 0, 1, 0, 300
        self.max_health, self.health, self.damage, self.speed = 100, 100, 45, 4
        self.dash_timer = self.dash_cooldown = self.invul_timer = 0
        self.dash_unlocked = self.attacking = self.hit_done = self.dying = False
        self.whirlwind_timer = self.whirlwind_cooldown = 0
        self.shield_active_timer = self.shield_cooldown = 0

    def take_damage(self, amount, effects):
        if self.invul_timer > 0 or self.dying: return
        if self.level >= 4 and self.shield_cooldown <= 0:
            self.shield_active_timer, self.shield_cooldown = 120, 900
            effects.append(FloatingText(self.x, self.y-40, "SHIELD!", (255, 255, 255))); return
        self.health -= amount; play_sfx("hurt")
        effects.append(FloatingText(self.x, self.y, f"-{amount}", (255, 0, 0)))
        if self.health <= 0: self.health, self.state, self.dying = 0, "hurt", True
        else: self.invul_timer = 40

    def update(self, keys, enemies, effects, fire_trail, boss=None):
        global shake_amount
        if self.invul_timer > 0: self.invul_timer -= 1
        if self.shield_active_timer > 0: self.shield_active_timer -= 1
        if self.shield_cooldown > 0: self.shield_cooldown -= 1
        if self.whirlwind_cooldown > 0: self.whirlwind_cooldown -= 1
        if self.dying: self.state = "hurt"; self.play_anim(10); return

        if self.dash_timer > 0:
            self.dash_timer -= 1
            if self.level >= 5: fire_trail.append(FireParticle(self.x+32, self.y+32))
        if self.dash_cooldown > 0: self.dash_cooldown -= 1

        if keys and keys[pygame.K_LCTRL] and self.level >= 3 and self.whirlwind_cooldown <= 0:
            play_sfx("whirlwind"); self.whirlwind_timer, self.whirlwind_cooldown, shake_amount = 32, 480, 12
            self.attacking, self.state, self.frame, self.timer = True, "slash", 0, 0
            for e in enemies:
                if not e.dying and math.hypot(e.x-self.x, e.y-self.y) < 160: e.take_damage(self.damage*1.5, self, effects, [])
            if boss and math.hypot(boss.x-self.x, boss.y-self.y) < 220: boss.health -= self.damage*2

        if self.whirlwind_timer > 0: self.whirlwind_timer -= 1
        
        if self.attacking:
            self.state, self.timer = "slash", self.timer + 1
            if self.timer >= 5:
                self.timer, self.frame = 0, self.frame + 1
                if self.frame == 3 and not self.hit_done and self.whirlwind_timer <= 0:
                    ar = pygame.Rect(self.x-38, self.y-38, 140, 140)
                    for e in enemies:
                        if not e.dying and ar.colliderect(e.rect()): e.take_damage(self.damage, self, effects, []); self.hit_done = True
                    if boss and ar.colliderect(boss.rect()): boss.health -= self.damage; self.hit_done = True
                if self.frame >= len(self.animations["slash"][self.direction]):
                    self.attacking, self.hit_done, self.state, self.frame = False, False, "idle", 0
            return 

        if keys and keys[pygame.K_SPACE]: 
            play_sfx("slash"); self.attacking, self.state, self.frame, self.timer, self.hit_done = True, "slash", 0, 0, False; return

        move, nx, ny = False, self.x, self.y; spd = self.speed * 3 if self.dash_timer > 0 else self.speed
        if keys:
            if keys[pygame.K_w]: ny -= spd; self.direction="up"; move=True
            if keys[pygame.K_s]: ny += spd; self.direction="down"; move=True
            if keys[pygame.K_a]: nx -= spd; self.direction="left"; move=True
            if keys[pygame.K_d]: nx += spd; self.direction="right"; move=True
            
            if game_state != GAME_BOSS:
                if is_walkable(nx + 32, ny + 55): self.x, self.y = nx, ny
            else:
                if 20 < nx < WIDTH-80 and 20 < ny < HEIGHT-80: self.x, self.y = nx, ny

            if keys[pygame.K_LSHIFT] and self.dash_unlocked and self.dash_cooldown <= 0 and move: 
                play_sfx("dash"); self.dash_timer, self.dash_cooldown = 12, 60
        self.state = "walk" if move else "idle"; self.play_anim(4 if self.dash_timer > 0 else 7)

    def play_anim(self, speed):
        self.timer += 1
        if self.timer >= speed:
            self.timer, al = 0, self.animations[self.state][self.direction]
            self.frame = min(self.frame + 1, len(al)-1) if self.dying else (self.frame + 1) % len(al)

    def draw(self, surf, cx, cy):
        anim = self.animations[self.state][self.direction]; img = anim[min(self.frame, len(anim)-1)]
        off = (img.get_width()-64)//2; surf.blit(img, (self.x-cx-off, self.y-cy-off))
        if self.whirlwind_timer > 0:
            surf.blit(self.whirlwind_frames[max(0, min(3, 3-(self.whirlwind_timer//8)))], (self.x-cx-96, self.y-cy-96))
        if self.shield_active_timer > 0: pygame.draw.circle(surf, (150, 220, 255), (int(self.x-cx+32), int(self.y-cy+32)), 50, 3)
    def rect(self): return pygame.Rect(self.x+16, self.y+16, 32, 32)

# ================= ENEMY =================
class Enemy:
    def __init__(self, lvl=1):
        self.x, self.y = get_tree_spawn()
        self.lvl = lvl
        f = f"lpc_enemy_lvl_{lvl}"
        self.state, self.direction, self.frame, self.timer = "idle", "down", 0, 0
        self.dying, self.death_timer, self.attacking, self.hit_done = False, 0, False, False
        
        # FIKS: Bruker thrust_oversize for Lvl 4 og slash_oversize for Lvl 3
        anim_file = f"bilder/{f}/thrust.png"
        fw, fh = 64, 64
        if lvl == 3:
            anim_file = f"bilder/{f}/slash_oversize.png"
            fw, fh = 192, 192
        elif lvl == 4:
            anim_file = f"bilder/{f}/thrust_oversize.png"
            fw, fh = 192, 192

        self.animations = {
            "idle": load_anim(f"bilder/{f}/idle.png", 64, 64, 2),
            "walk": load_anim(f"bilder/{f}/walk.png", 64, 64, 9),
            "attack": load_anim(anim_file, fw, fh, 6),
            "hurt": load_anim(f"bilder/{f}/hurt.png", 64, 64, 6)
        }
        stats = {1:(70,8,2.3,25,60), 2:(220,18,1.8,70,60), 3:(500,28,1.5,200,80), 4:(1500,45,0.9,600,100)}
        self.health, self.damage, self.speed, self.xp_reward, self.range = stats[lvl]
        self.max_health, self.wander_target, self.wander_timer = self.health, (self.x, self.y), 0
        self.dash_timer = 0
        self.dash_cooldown = 0

    def update(self, player, effects, fire_trail):
        if self.dying: self.death_timer -= 1; self.state = "hurt"; self.play_anim(8); return self.death_timer <= 0
        dx, dy = player.x-self.x, player.y-self.y; dist = math.hypot(dx, dy)
        
        if self.dash_cooldown > 0: self.dash_cooldown -= 1
        if self.dash_timer > 0: 
            self.dash_timer -= 1
            # FIKS: Fjernet FireParticle her for å hindre selvmord

        if self.attacking:
            self.state, self.timer = "attack", self.timer + 1
            if self.timer >= 7:
                self.timer, self.frame = 0, self.frame + 1
                if self.frame == 3 and not self.hit_done:
                    if dist < self.range+40 and not player.dying: player.take_damage(self.damage, effects); self.hit_done = True
                if self.frame >= len(self.animations["attack"][self.direction]): self.attacking, self.hit_done, self.state, self.frame = False, False, "idle", 0
            return False

        if dist < 400:
            if self.lvl == 3 and self.dash_cooldown <= 0 and 100 < dist < 250:
                self.dash_timer, self.dash_cooldown = 15, 120
            
            if dist > self.range: 
                self.state = "walk"
                spd = self.speed * 3 if self.dash_timer > 0 else self.speed
                self.move_towards(player.x, player.y, spd)
            else: 
                self.attacking, self.frame, self.timer = True, 0, 0
        else:
            self.wander_timer -= 1
            if self.wander_timer <= 0: self.wander_target, self.wander_timer = (self.x+random.randint(-100,100), self.y+random.randint(-100,100)), random.randint(120,300)
            if math.hypot(self.wander_target[0]-self.x, self.wander_target[1]-self.y) > 5: self.state = "walk"; self.move_towards(self.wander_target[0], self.wander_target[1], self.speed*0.4)
            else: self.state = "idle"
        self.play_anim(10); return False

    def move_towards(self, tx, ty, s):
        dx, dy = tx-self.x, ty-self.y; dist = math.hypot(dx, dy)
        if dist > 2:
            vx, vy = (dx/dist)*s, (dy/dist)*s
            if is_walkable(self.x+vx+32, self.y+vy+55): self.x += vx; self.y += vy
            if abs(dx) > abs(dy): self.direction = "right" if dx > 0 else "left"
            else: self.direction = "down" if dy > 0 else "up"

    def take_damage(self, dmg, player, effects, potions):
        if self.dying: return
        self.health -= dmg
        if self.health <= 0:
            play_sfx("enemy_death"); self.state, self.dying, self.death_timer = "hurt", True, 50
            player.xp += self.xp_reward; effects.append(FloatingText(self.x, self.y, f"+{self.xp_reward} XP", (0, 200, 255)))
            
            if random.random() < 0.20:
                potions.append(Potion(self.x, self.y))
                
            while player.xp >= player.xp_to_next:
                play_sfx("lvl_up"); player.xp -= player.xp_to_next; player.level += 1; player.xp_to_next = int(player.xp_to_next*1.8) 
                player.damage += 15; player.max_health += 30; player.health = player.max_health
                effects.append(FloatingText(player.x, player.y-45, "LEVEL UP!", (255, 215, 0), True))
                if player.level == 2: player.dash_unlocked = True
        else: play_sfx("hurt"); effects.append(FloatingText(self.x, self.y, f"-{dmg}", (255, 50, 50)))

    def play_anim(self, s):
        self.timer += 1
        if self.timer >= s:
            self.timer, al = 0, self.animations[self.state][self.direction]
            self.frame = min(self.frame+1, len(al)-1) if self.dying else (self.frame+1)%len(al)

    def draw(self, surf, cx, cy):
        anim = self.animations[self.state][self.direction]; img = anim[min(self.frame, len(anim)-1)]
        ox, oy = (img.get_width()-64)//2, (img.get_height()-64)//2
        surf.blit(img, (self.x-cx-ox, self.y-cy-oy))
        if not self.dying:
            bar_w = 40
            pygame.draw.rect(surf, (0,0,0), (self.x-cx+12, self.y-cy-5, bar_w, 5))
            pygame.draw.rect(surf, (255,0,0), (self.x-cx+12, self.y-cy-5, bar_w*(self.health/self.max_health), 5))
            lvl_t = FONT_LVL.render(f"Lvl {self.lvl}", True, (255,255,255))
            surf.blit(lvl_t, (self.x-cx+12, self.y-cy-20))

    def rect(self): return pygame.Rect(self.x+16, self.y+16, 32, 32)

# ================= CORE LOOP =================
def restart_game():
    global player, enemies, effects, potions, portal, boss, game_state, fire_trail
    player.reset()
    enemies, effects, fire_trail = [], [], []
    potions = [Potion() for _ in range(5)]
    portal = Portal(1250, 450)
    boss = None
    game_state = GAME_PLAYING

player = Player()
enemies, effects, potions, fire_trail = [], [], [Potion() for _ in range(5)], []
portal = Portal(1250, 450)
boss = None

while True:
    CLOCK.tick(FPS); events = pygame.event.get()
    for event in events:
        if event.type == pygame.QUIT: pygame.quit(); sys.exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE: game_state = GAME_PAUSED if game_state in [GAME_PLAYING, GAME_BOSS] else GAME_PLAYING
            if game_state in [GAME_OVER, GAME_VICTORY] and event.key == pygame.K_r: restart_game()

    new_state, ui_action = ui.handle_events(events, game_state)
    if ui_action == "QUIT": break
    if new_state: game_state = new_state

    if game_state in [GAME_PLAYING, GAME_BOSS]:
        if not player.dying:
            player.update(pygame.key.get_pressed(), enemies, effects, fire_trail, boss)
            
            if game_state == GAME_PLAYING:
                if len(potions) < 5 and random.random() < 0.005:
                    potions.append(Potion())

                for e in enemies[:]:
                    if e.update(player, effects, fire_trail): enemies.remove(e)
                
                if random.random() < 0.025 and len(enemies) < 15:
                    av = [1, 2, 3, 4] if player.level >= 4 else [1, 2, 3] if player.level >= 3 else [1, 2] if player.level >= 2 else [1]
                    enemies.append(Enemy(random.choice(av)))
                
                for p in potions[:]:
                    if player.rect().colliderect(p.rect()): 
                        play_sfx("potion")
                        player.health = min(player.max_health, player.health+40)
                        effects.append(FloatingText(player.x, player.y, "+40 HP", (0, 255, 0)))
                        potions.remove(p)
                
                if player.level >= 6: 
                    portal.active = True
                    if not portal.notified:
                        effects.append(FloatingText(player.x, player.y, "PORTALEN ER ÅPEN!", (0, 255, 255), True))
                        portal.notified = True
                    if player.rect().colliderect(portal.rect()): 
                        game_state, boss, player.x, player.y = GAME_BOSS, Boss(), WIDTH//2, 600
                        enemies = [] # Tømmer fiender når du går til boss
            
            elif game_state == GAME_BOSS and boss:
                boss.update(player, effects)
                if boss.health <= 0: game_state = GAME_VICTORY
        else:
            player.update(None, enemies, effects, fire_trail)
            if player.frame >= 5: game_state = GAME_OVER
        
        for f in effects[:]:
            f.update()
            if f.timer <= 0: effects.remove(f)
        for p in fire_trail[:]:
            p.update(enemies, boss)
            if p.timer <= 0: fire_trail.remove(p)

    cx = max(0, min(player.x-CENTER_X, BG_W-WIDTH)) if game_state != GAME_BOSS else 0
    cy = max(0, min(player.y-CENTER_Y, BG_H-HEIGHT)) if game_state != GAME_BOSS else 0
    if shake_amount > 0: cx += random.randint(-shake_amount, shake_amount); cy += random.randint(-shake_amount, shake_amount); shake_amount -= 1

    SCREEN.fill((20, 10, 30))
    if game_state != GAME_BOSS:
        SCREEN.blit(BG_MAP, (-cx, -cy))
        portal.draw(SCREEN, cx, cy)
        for p in potions: p.draw(SCREEN, cx, cy)
        for p in fire_trail: p.draw(SCREEN, cx, cy)
        for ent in sorted(enemies + [player], key=lambda e: e.y): ent.draw(SCREEN, cx, cy)
        SCREEN.blit(TREE_LAYER, (-cx, -cy))
    elif game_state == GAME_BOSS and boss:
        for i in range(0, WIDTH, 64):
            pygame.draw.line(SCREEN, (40,20,60), (i,0), (i,HEIGHT))
            pygame.draw.line(SCREEN, (40,20,60), (0,i), (WIDTH,i))
        boss.draw(SCREEN)
        for p in fire_trail: p.draw(SCREEN, 0, 0)
        player.draw(SCREEN, 0, 0)
    
    for f in effects: f.draw(SCREEN, cx, cy)

    if game_state in [GAME_PLAYING, GAME_BOSS, GAME_PAUSED]:
        pygame.draw.rect(SCREEN, (40,40,40), (WIDTH//2-200, HEIGHT-30, 400, 10))
        pygame.draw.rect(SCREEN, (0,150,255), (WIDTH//2-200, HEIGHT-30, 400*(player.xp/player.xp_to_next), 10))
        lvl_text = FONT_HUD.render(f"Level {player.level}", True, (255, 255, 255))
        SCREEN.blit(lvl_text, (WIDTH//2 - lvl_text.get_width()//2, HEIGHT - 70))
        pygame.draw.rect(SCREEN, (40,40,40), (20,20,204,24))
        pygame.draw.rect(SCREEN, (220,30,30), (22,22,200*max(0, player.health/player.max_health),20))
        y_off = 60
        for text, _ in [("SPACE: Attack", True), ("L-SHIFT: Dash", player.dash_unlocked), ("L-CTRL: Whirlwind", player.level>=3)]:
            if _: SCREEN.blit(FONT_INFO.render(text, True, (255,255,255)), (20, y_off)); y_off += 30

    if game_state == GAME_OVER:
        ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA); ov.fill((0,0,0,180)); SCREEN.blit(ov, (0,0))
        t = FONT_OVER.render("GAME OVER", True, (255,50,50)); SCREEN.blit(t, (WIDTH//2-t.get_width()//2, HEIGHT//2-50))
        r = FONT_HUD.render("Trykk R for å restarte", True, (255,255,255)); SCREEN.blit(r, (WIDTH//2-r.get_width()//2, HEIGHT//2+20))

    if game_state == GAME_VICTORY:
        ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA); ov.fill((0,0,0,200)); SCREEN.blit(ov, (0,0))
        t = FONT_OVER.render("VICTORY!", True, (255,215,0)); SCREEN.blit(t, (WIDTH//2-t.get_width()//2, HEIGHT//2-50))
        r = FONT_HUD.render("Du har bekjempet bossen! Trykk R for å spille igjen.", True, (255,255,255)); SCREEN.blit(r, (WIDTH//2-r.get_width()//2, HEIGHT//2+20))
    
    ui.draw(game_state) 
    pygame.display.flip()