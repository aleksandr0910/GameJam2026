import pygame
import sys
import random
import math
from ui import UI, GAME_INTRO, GAME_PLAYING, GAME_PAUSED

# ================= INITIALISERING =================
pygame.init()
WIDTH, HEIGHT = 1280, 720
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Knight & Grow")

GAME_BOSS = "BOSS_FIGHT"
GAME_OVER = "GAME_OVER"
CLOCK = pygame.time.Clock()
FPS = 60
CENTER_X, CENTER_Y = WIDTH // 2, HEIGHT // 2

# Fonter - NÅ MED ALLE DEFINISJONER
FONT_XP = pygame.font.SysFont("Arial", 20, bold=True)
FONT_LVL = pygame.font.SysFont("Arial", 16, bold=True)
FONT_INFO = pygame.font.SysFont("Arial", 24, bold=True)
FONT_UNLOCK = pygame.font.SysFont("Arial", 40, bold=True)
FONT_OVER = pygame.font.SysFont("Arial", 64, bold=True)

ui = UI(SCREEN)
game_state = GAME_INTRO
DIR_ORDER = ["up", "left", "down", "right"]

# ================= HJELPEFUNKSJONER =================
PATH_TO_MAP = r"C:\Users\henni\Documents\UiO\GameJam2026\bilder\world\world.png"

try:
    BG_TILE = pygame.image.load(PATH_TO_MAP).convert_alpha()
    BG_W, BG_H = BG_TILE.get_size()
    COLLISION_MAP = BG_TILE.copy()
except:
    BG_W, BG_H = 2000, 2000
    BG_TILE = pygame.Surface((BG_W, BG_H))
    BG_TILE.fill((34, 139, 34))
    COLLISION_MAP = BG_TILE

def is_walkable(x, y):
    if x < 40 or x > BG_W - 60 or y < 40 or y > BG_H - 80: return False
    try:
        color = COLLISION_MAP.get_at((int(x), int(y)))
        if color.b > 120 and color.b > color.g + 10: return False 
    except: return False
    return True

def get_safe_spawn():
    for _ in range(200):
        tx, ty = random.randint(100, BG_W-100), random.randint(100, BG_H-100)
        if is_walkable(tx + 32, ty + 50): return tx, ty
    return 500, 500

def load_anim(path, fw, fh, count):
    try:
        sheet = pygame.image.load(path).convert_alpha()
        anim = {}
        sheet_h = sheet.get_height()
        for i, d in enumerate(DIR_ORDER):
            frames = []
            y_offset = i * fh if sheet_h >= (i + 1) * fh else 0
            for col in range(count):
                frames.append(sheet.subsurface(pygame.Rect(col*fw, y_offset, fw, fh)).copy())
            anim[d] = frames
        return anim
    except:
        s = pygame.Surface((fw, fh)); s.fill((255, 0, 255))
        return {d: [s] for d in DIR_ORDER}

# ================= KLASSER FOR EFFEKTER =================
class FireParticle:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.timer = 45
        self.size = random.randint(12, 18)
        self.color = (random.randint(200, 255), random.randint(50, 100), 20)
    def update(self, enemies, boss):
        self.timer -= 1
        self.size *= 0.95
        rect = pygame.Rect(self.x - 15, self.y - 15, 30, 30)
        for e in enemies:
            if not e.dying and rect.colliderect(e.rect()): e.health -= 0.8
        if boss and rect.colliderect(boss.rect()): boss.health -= 1.5
    def draw(self, surf, cx, cy):
        if self.timer > 0: pygame.draw.circle(surf, self.color, (int(self.x - cx), int(self.y - cy)), int(self.size))

class FloatingText:
    def __init__(self, x, y, text, color=(0, 150, 255), stay=False):
        self.x, self.y, self.text, self.color = x, y, text, color
        self.timer = 180 if stay else 60; self.alpha = 255; self.stay = stay
    def update(self):
        if not self.stay: self.y -= 0.8
        self.timer -= 1
        if self.timer < 30: self.alpha = max(0, self.alpha - 8)
    def draw(self, surf, cx, cy):
        font = FONT_UNLOCK if self.stay else FONT_XP
        t = font.render(self.text, True, self.color)
        t.set_alpha(self.alpha)
        pos = (WIDTH//2 - t.get_width()//2, 150) if self.stay else (self.x - cx, self.y - cy)
        surf.blit(t, pos)

class Potion:
    def __init__(self): self.x, self.y = get_safe_spawn()
    def draw(self, surf, cx, cy):
        pygame.draw.rect(surf, (200, 0, 0), (self.x - cx - 8, self.y - cy - 4, 16, 16), border_radius=3)
        pygame.draw.rect(surf, (255, 255, 255), (self.x - cx - 4, self.y - cy - 8, 8, 4))
    def rect(self): return pygame.Rect(self.x - 10, self.y - 10, 20, 20)

class Portal:
    def __init__(self, x, y): self.x, self.y, self.active, self.timer = x, y, False, 0
    def draw(self, surf, cx, cy):
        if not self.active: return
        self.timer += 0.05
        for i in range(4):
            r = 50 + i * 10 + math.sin(self.timer + i) * 8
            pygame.draw.circle(surf, (150, 50, 255), (int(self.x - cx), int(self.y - cy)), int(r), 2)
    def rect(self): return pygame.Rect(self.x - 40, self.y - 40, 80, 80)

class Boss:
    def __init__(self): self.x, self.y, self.max_health, self.health, self.timer = WIDTH // 2, 250, 12000, 12000, 0
    def update(self):
        self.timer += 0.04
        self.x = WIDTH // 2 + math.cos(self.timer) * 200
    def draw(self, surf):
        pygame.draw.circle(surf, (150, 0, 0), (int(self.x), int(self.y)), 100)
        pygame.draw.rect(surf, (50, 0, 0), (WIDTH // 2 - 300, 30, 600, 25))
        pygame.draw.rect(surf, (255, 0, 0), (WIDTH // 2 - 300, 30, 600 * (self.health / self.max_health), 25))
    def rect(self): return pygame.Rect(self.x - 90, self.y - 90, 180, 180)

# ================= SPILLER KLASSE =================
class Player:
    def __init__(self):
        self.animations = {
            "idle": load_anim("bilder/lpc/idle.png", 64, 64, 2),
            "walk": load_anim("bilder/lpc/walk.png", 64, 64, 9),
            "slash": load_anim("bilder/lpc/slash.png", 128, 128, 6),
            "hurt": load_anim("bilder/lpc/hurt.png", 64, 64, 6)
        }
        self.reset()

    def reset(self):
        self.x, self.y = 510, 185
        self.state, self.direction = "idle", "down"
        self.frame, self.timer = 0, 0
        self.level, self.xp, self.xp_to_next = 1, 0, 100
        self.max_health, self.health, self.damage = 100, 100, 45
        self.speed = 4
        self.dash_timer, self.dash_cooldown = 0, 0
        self.dash_unlocked = False
        self.whirlwind_timer, self.whirlwind_cooldown = 0, 0
        self.shield_active_timer, self.shield_cooldown = 0, 0
        self.dying, self.attacking, self.hit_done = False, False, False
        self.invul_timer = 0

    def take_damage(self, amount, effects):
        if self.invul_timer > 0 or self.dying: return
        if self.level >= 4 and self.shield_cooldown <= 0:
            self.shield_active_timer = 120
            self.shield_cooldown = 900 
            effects.append(FloatingText(self.x, self.y - 40, "SHIELD!", (255, 255, 255)))
            return
        if self.shield_active_timer > 0: return
        self.health -= amount
        effects.append(FloatingText(self.x, self.y, f"-{amount}", (255, 0, 0)))
        if self.health <= 0:
            self.health, self.state, self.frame, self.timer, self.dying = 0, "hurt", 0, 0, True
        else: self.invul_timer = 40

    def update(self, keys, enemies, effects, fire_trail, current_game_state, boss=None):
        if self.invul_timer > 0: self.invul_timer -= 1
        if self.shield_active_timer > 0: self.shield_active_timer -= 1
        if self.shield_cooldown > 0: self.shield_cooldown -= 1
        if self.whirlwind_cooldown > 0: self.whirlwind_cooldown -= 1
        
        if self.dying: 
            self.state = "hurt"; self.play_anim(10); return

        if self.dash_timer > 0: 
            self.dash_timer -= 1
            if self.level >= 5: fire_trail.append(FireParticle(self.x + 32, self.y + 32))
        if self.dash_cooldown > 0: self.dash_cooldown -= 1

        if keys and keys[pygame.K_LCTRL] and self.level >= 3 and self.whirlwind_cooldown <= 0:
            self.whirlwind_timer = 20
            self.whirlwind_cooldown = 480 
            self.attacking, self.state, self.frame, self.timer = True, "slash", 0, 0
            for e in enemies:
                if not e.dying and math.hypot(e.x-self.x, e.y-self.y) < 130:
                    e.take_damage(self.damage * 1.5, self, effects)
            if boss and math.hypot(boss.x-self.x, boss.y-self.y) < 200: boss.health -= self.damage * 2

        if self.attacking:
            self.state = "slash"; self.timer += 1
            if self.timer >= 5:
                self.timer = 0; self.frame += 1
                if self.frame == 3 and not self.hit_done and self.whirlwind_timer <= 0:
                    attack_rect = pygame.Rect(self.x+32-70, self.y+32-70, 140, 140)
                    for e in enemies:
                        if not e.dying and attack_rect.colliderect(e.rect()):
                            e.take_damage(self.damage, self, effects); self.hit_done = True
                    if boss and attack_rect.colliderect(boss.rect()): boss.health -= self.damage; self.hit_done = True
                if self.frame >= len(self.animations["slash"][self.direction]):
                    self.attacking, self.hit_done, self.whirlwind_timer, self.state, self.frame = False, False, 0, "idle", 0
            return 

        if keys and keys[pygame.K_SPACE]:
            self.attacking, self.state, self.frame, self.timer, self.hit_done = True, "slash", 0, 0, False
            return

        curr_speed = self.speed * 3 if self.dash_timer > 0 else self.speed
        move = False; nx, ny = self.x, self.y
        if keys:
            if keys[pygame.K_w]: ny -= curr_speed; self.direction="up"; move=True
            elif keys[pygame.K_s]: ny += curr_speed; self.direction="down"; move=True
            elif keys[pygame.K_a]: nx -= curr_speed; self.direction="left"; move=True
            elif keys[pygame.K_d]: nx += curr_speed; self.direction="right"; move=True
            if is_walkable(nx + 32, ny + 50): self.x, self.y = nx, ny
            if keys[pygame.K_LSHIFT] and self.dash_unlocked and self.dash_cooldown <= 0 and move:
                self.dash_timer, self.dash_cooldown = 12, 60

        self.state = "walk" if move else "idle"
        self.play_anim(4 if self.dash_timer > 0 else 7)

    def play_anim(self, speed):
        self.timer += 1
        if self.timer >= speed:
            self.timer = 0
            anim_list = self.animations[self.state][self.direction]
            self.frame = min(self.frame + 1, len(anim_list) - 1) if self.dying else (self.frame + 1) % len(anim_list)

    def draw(self, surf, cx, cy):
        anim = self.animations[self.state][self.direction]
        img = anim[min(self.frame, len(anim)-1)]
        off = (img.get_width() - 64) // 2
        if self.invul_timer % 4 < 2: surf.blit(img, (self.x - cx - off, self.y - cy - off))
        if self.shield_active_timer > 0:
            pygame.draw.circle(surf, (150, 220, 255), (int(self.x-cx+32), int(self.y-cy+32)), 50, 3)
        if self.whirlwind_timer > 0:
            pygame.draw.circle(surf, (255, 255, 255), (int(self.x-cx+32), int(self.y-cy+32)), 120, 2)

    def rect(self): return pygame.Rect(self.x+16, self.y+16, 32, 32)

# ================= FIENDE KLASSE =================
class Enemy:
    def __init__(self, lvl=1):
        self.x, self.y = get_safe_spawn(); self.lvl = lvl
        folder = f"lpc_enemy_lvl_{lvl}"
        self.state, self.direction, self.frame, self.timer = "idle", "down", 0, 0
        self.dying, self.death_timer, self.attacking, self.hit_done = False, 0, False, False
        self.enemy_dash_timer = self.enemy_dash_cooldown = 0
        self.wander_target, self.wander_timer = (self.x, self.y), 0
        if lvl == 4:
            self.health, self.damage, self.speed, self.xp_reward, self.range = 1200, 40, 0.8, 500, 100
            self.animations = {"idle": load_anim(f"bilder/{folder}/idle.png", 64, 64, 2), "walk": load_anim(f"bilder/{folder}/walk_128.png", 128, 128, 9), "attack": load_anim(f"bilder/{folder}/thrust_oversize.png", 192, 192, 6), "hurt": load_anim(f"bilder/{folder}/hurt.png", 64, 64, 6)}
        elif lvl == 3:
            self.health, self.damage, self.speed, self.xp_reward, self.range = 450, 25, 1.4, 150, 80
            self.animations = {"idle": load_anim(f"bilder/{folder}/idle.png", 64, 64, 2), "walk": load_anim(f"bilder/{folder}/walk.png", 64, 64, 9), "attack": load_anim(f"bilder/{folder}/slash_oversize.png", 192, 192, 6), "hurt": load_anim(f"bilder/{folder}/hurt.png", 64, 64, 6)}
        elif lvl == 2:
            self.health, self.damage, self.speed, self.xp_reward, self.range = 200, 15, 1.7, 55, 60
            self.animations = {"idle": load_anim(f"bilder/{folder}/idle.png", 64, 64, 2), "walk": load_anim(f"bilder/{folder}/walk.png", 64, 64, 9), "attack": load_anim(f"bilder/{folder}/slash_oversize.png", 192, 192, 6), "hurt": load_anim(f"bilder/{folder}/hurt.png", 64, 64, 6)}
        else:
            self.health, self.damage, self.speed, self.xp_reward, self.range = 60, 6, 2.2, 20, 60
            self.animations = {"idle": load_anim(f"bilder/{folder}/idle.png", 64, 64, 2), "walk": load_anim(f"bilder/{folder}/walk.png", 64, 64, 9), "attack": load_anim(f"bilder/{folder}/thrust.png", 64, 64, 6), "hurt": load_anim(f"bilder/{folder}/hurt.png", 64, 64, 6)}
        self.max_health = self.health

    def update(self, player, effects):
        if self.dying: self.death_timer -= 1; self.state = "hurt"; self.play_anim(8); return self.death_timer <= 0
        dx, dy = player.x - self.x, player.y - self.y
        dist = math.hypot(dx, dy)
        if self.lvl == 3:
            if self.enemy_dash_cooldown > 0: self.enemy_dash_cooldown -= 1
            if dist < 180 and self.enemy_dash_cooldown == 0 and not self.attacking: self.enemy_dash_timer, self.enemy_dash_cooldown = 15, 140
        if self.attacking:
            self.state = "attack"; self.timer += 1
            if self.timer >= 7:
                self.timer = 0; self.frame += 1
                if self.frame == 3 and not self.hit_done:
                    if dist < self.range + 30 and not player.dying: player.take_damage(self.damage, effects); self.hit_done = True
                if self.frame >= len(self.animations["attack"][self.direction]): self.attacking, self.hit_done, self.state, self.frame = False, False, "idle", 0
            return False
        if dist < 250:
            if dist > self.range:
                self.state = "walk"; s = self.speed * 4 if self.enemy_dash_timer > 0 else self.speed
                if self.enemy_dash_timer > 0: self.enemy_dash_timer -= 1
                self.move_towards(player.x, player.y, s)
            else: self.attacking, self.frame, self.timer = True, 0, 0
        else:
            self.wander_timer -= 1
            if self.wander_timer <= 0: self.wander_target, self.wander_timer = (self.x + random.randint(-100, 100), self.y + random.randint(-100, 100)), random.randint(120, 300)
            if math.hypot(self.wander_target[0] - self.x, self.wander_target[1] - self.y) > 5: self.state = "walk"; self.move_towards(self.wander_target[0], self.wander_target[1], self.speed * 0.4)
            else: self.state = "idle"
        self.play_anim(10); return False

    def move_towards(self, tx, ty, speed):
        dx, dy = tx - self.x, ty - self.y
        dist = math.hypot(dx, dy)
        if dist > 2:
            vx, vy = (dx/dist) * speed, (dy/dist) * speed
            if is_walkable(self.x + vx + 32, self.y + vy + 50): self.x += vx; self.y += vy
            if abs(dx) > abs(dy): self.direction = "right" if dx > 0 else "left"
            else: self.direction = "down" if dy > 0 else "up"

    def take_damage(self, dmg, player, effects):
        if self.dying: return
        self.health -= dmg
        if self.health <= 0:
            self.state, self.frame, self.timer, self.dying, self.death_timer = "hurt", 0, 0, True, 50
            player.xp += self.xp_reward
            effects.append(FloatingText(self.x, self.y, f"+{self.xp_reward} XP", (0, 200, 255)))
            while player.xp >= player.xp_to_next:
                player.xp -= player.xp_to_next; player.level += 1; player.xp_to_next = int(player.xp_to_next * 1.5)
                player.damage += 15; player.max_health += 30; player.health = player.max_health
                effects.append(FloatingText(player.x, player.y-45, "LEVEL UP!", (255, 215, 0)))
                if player.level == 2: 
                    player.dash_unlocked = True
                    effects.append(FloatingText(0, 0, "LEVEL 2: DASH UNLOCKED (L-SHIFT)", (255,255,255), True))
                elif player.level == 3:
                    effects.append(FloatingText(0, 0, "LEVEL 3: WHIRLWIND UNLOCKED (L-CTRL)", (255,255,255), True))
                elif player.level == 4:
                    effects.append(FloatingText(0, 0, "LEVEL 4: AUTO-SHIELD UNLOCKED", (255,255,255), True))
                elif player.level == 5:
                    effects.append(FloatingText(0, 0, "LEVEL 5: FIRE TRAIL UNLOCKED", (255,255,255), True))
        else: effects.append(FloatingText(self.x, self.y, f"-{dmg}", (255, 50, 50)))

    def play_anim(self, speed):
        self.timer += 1
        if self.timer >= speed:
            self.timer = 0
            anim_list = self.animations[self.state][self.direction]
            self.frame = min(self.frame + 1, len(anim_list) - 1) if self.dying else (self.frame + 1) % len(anim_list)

    def draw(self, surf, cx, cy):
        anim = self.animations[self.state][self.direction]
        img = anim[min(self.frame, len(anim)-1)]
        ox, oy = (img.get_width()-64)//2, (img.get_height()-64)//2
        surf.blit(img, (self.x - cx - ox, self.y - cy - oy))
        if not self.dying:
            pygame.draw.rect(surf, (50,0,0), (self.x-cx+12, self.y-cy-5, 40, 4))
            pygame.draw.rect(surf, (255,0,0), (self.x-cx+12, self.y-cy-5, 40*(self.health/self.max_health), 4))
    def rect(self): return pygame.Rect(self.x+16, self.y+16, 32, 32)

# ================= SPILL-LOGIKK / RESTART =================
player = Player()
enemies, effects, potions, fire_trail = [Enemy(1) for _ in range(5)], [], [Potion() for _ in range(3)], []
portal, boss = Portal(1450, 450), None

def restart_game():
    global player, enemies, effects, potions, portal, boss, game_state, fire_trail
    player.reset(); enemies = [Enemy(1) for _ in range(5)]
    effects, potions, fire_trail = [], [Potion() for _ in range(3)], []
    portal, boss, game_state = Portal(1450, 450), None, GAME_PLAYING

# ================= HOVEDLØKKE =================
while True:
    CLOCK.tick(FPS)
    events = pygame.event.get()
    for event in events:
        if event.type == pygame.QUIT: pygame.quit(); sys.exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if game_state in [GAME_PLAYING, GAME_BOSS]: game_state = GAME_PAUSED
                elif game_state == GAME_PAUSED: game_state = GAME_PLAYING
            if game_state == GAME_OVER and event.key == pygame.K_r: restart_game()

    new_state, ui_action = ui.handle_events(events, game_state)
    if ui_action == "QUIT": break
    if new_state: game_state = new_state

    if game_state in [GAME_PLAYING, GAME_BOSS]:
        if not player.dying:
            player.update(pygame.key.get_pressed(), enemies, effects, fire_trail, game_state, boss)
            if game_state == GAME_PLAYING:
                for e in enemies[:]:
                    if e.update(player, effects): enemies.remove(e)
                if random.random() < 0.012 and len(enemies) < 12: enemies.append(Enemy(random.randint(1, min(4, player.level))))
                for p in potions[:]:
                    if player.rect().colliderect(p.rect()): player.health = min(player.max_health, player.health + 40); potions.remove(p)
                if player.level >= 5:
                    portal.active = True
                    if player.rect().colliderect(portal.rect()): game_state, boss, player.x, player.y = GAME_BOSS, Boss(), WIDTH//2, 600
            elif boss:
                boss.update()
                if boss.health <= 0: restart_game()
        else:
            player.update(None, enemies, effects, fire_trail, game_state)
            if player.frame >= len(player.animations["hurt"][player.direction]) - 1: game_state = GAME_OVER

        for f in effects[:]:
            f.update()
            if f.timer <= 0: effects.remove(f)
        for p in fire_trail[:]:
            p.update(enemies, boss)
            if p.timer <= 0: fire_trail.remove(p)

    cx, cy = (0, 0) if game_state == GAME_BOSS else (player.x - CENTER_X, player.y - CENTER_Y)
    SCREEN.fill((30, 30, 30))
    if game_state != GAME_BOSS: SCREEN.blit(BG_TILE, (-cx, -cy))
    portal.draw(SCREEN, cx, cy)
    for p in potions: p.draw(SCREEN, cx, cy)
    for p in fire_trail: p.draw(SCREEN, cx, cy)
    for e in sorted(enemies, key=lambda en: en.y): e.draw(SCREEN, cx, cy)
    if boss: boss.draw(SCREEN)
    player.draw(SCREEN, cx, cy)
    for f in effects: f.draw(SCREEN, cx, cy)

    # ================= HUD OG COOLDOWNS =================
    if game_state in [GAME_PLAYING, GAME_BOSS, GAME_PAUSED]:
        # XP Bar
        pygame.draw.rect(SCREEN, (40,40,40), (WIDTH//2-200, HEIGHT-30, 400, 10))
        pygame.draw.rect(SCREEN, (0,150,255), (WIDTH//2-200, HEIGHT-30, 400*(player.xp/player.xp_to_next), 10))
        
        # Health Bar
        pygame.draw.rect(SCREEN, (40,40,40), (20,20,204,24))
        pygame.draw.rect(SCREEN, (220,30,30), (22,22,200*max(0, player.health/player.max_health),20))
        
        # Ability Guide - Dynamisk liste
        y_off = 60
        guide_items = [("SPACE: Angrep", True)]
        if player.dash_unlocked: guide_items.append(("L-SHIFT: Dash", True))
        if player.level >= 3:    guide_items.append(("L-CTRL: Whirlwind", True))
        if player.level >= 4:    guide_items.append(("AUTO: Shield", True))
        if player.level >= 5:    guide_items.append(("PASSIVE: Fire Trail", True))
        for text, _ in guide_items:
            SCREEN.blit(FONT_INFO.render(text, True, (255, 255, 255)), (20, y_off))
            y_off += 30

        # Cooldown Sirkler
        if player.level >= 3: 
            pygame.draw.circle(SCREEN, (40,40,40), (WIDTH-60, HEIGHT-60), 25)
            if player.whirlwind_cooldown > 0:
                angle = (player.whirlwind_cooldown / 480) * (2 * math.pi)
                pygame.draw.arc(SCREEN, (255,255,255), (WIDTH-85, HEIGHT-85, 50, 50), 0, angle, 5)
            SCREEN.blit(FONT_LVL.render("WIND", True, (255,255,255)), (WIDTH-80, HEIGHT-65))
        if player.level >= 4:
            pygame.draw.circle(SCREEN, (40,40,40), (WIDTH-120, HEIGHT-60), 25)
            if player.shield_cooldown > 0:
                angle = (player.shield_cooldown / 900) * (2 * math.pi)
                pygame.draw.arc(SCREEN, (150,220,255), (WIDTH-145, HEIGHT-85, 50, 50), 0, angle, 5)
            SCREEN.blit(FONT_LVL.render("SHLD", True, (150,220,255)), (WIDTH-140, HEIGHT-65))

    if game_state == GAME_OVER:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA); overlay.fill((0, 0, 0, 180)); SCREEN.blit(overlay, (0,0))
        txt = FONT_OVER.render("GAME OVER", True, (255, 50, 50))
        SCREEN.blit(txt, (WIDTH//2-txt.get_width()//2, HEIGHT//2-50))

    ui.draw(game_state, hud_data={"Lvl": player.level})
    pygame.display.flip()