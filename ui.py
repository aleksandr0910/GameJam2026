import pygame

# ----------------------------
# UI: Game states
# ----------------------------
GAME_INTRO = "intro"
GAME_PLAYING = "playing"
GAME_PAUSED = "paused"


class UI:
    def __init__(self, screen):
        self.screen = screen
        self.w, self.h = screen.get_size()

        # ----------------------------
        # UI: fonter
        # ----------------------------
        self.font = pygame.font.SysFont("arial", 22, bold=True)
        self.big_font = pygame.font.SysFont("arial", 48, bold=True)

        # ----------------------------
        # UI: last inn knapp-bilder
        # (disse filene MÅ finnes)
        # ----------------------------
        try:
            self.start_img  = pygame.image.load("bilder/ui/start.png").convert_alpha()
            self.quit_img   = pygame.image.load("bilder/ui/quit.png").convert_alpha()
            self.resume_img = pygame.image.load("bilder/ui/resume.png").convert_alpha()
            self.menu_img   = pygame.image.load("bilder/ui/menu.png").convert_alpha()
        except:
            # Fallback hvis bildene mangler
            self.start_img = self.quit_img = self.resume_img = self.menu_img = pygame.Surface((240, 60))
            self.start_img.fill((100, 100, 100))

        # ----------------------------
        # UI: skaler knapper
        # ----------------------------
        self.start_img  = pygame.transform.scale(self.start_img,  (240, 60))
        self.quit_img   = pygame.transform.scale(self.quit_img,   (240, 60))
        self.resume_img = pygame.transform.scale(self.resume_img, (240, 60))
        self.menu_img   = pygame.transform.scale(self.menu_img,   (240, 60))

        # ----------------------------
        # UI: hover-versjoner
        # ----------------------------
        self.start_hover  = self._make_hover(self.start_img)
        self.quit_hover   = self._make_hover(self.quit_img)
        self.resume_hover = self._make_hover(self.resume_img)
        self.menu_hover   = self._make_hover(self.menu_img)

        # ----------------------------
        # UI: knapp-rektangler
        # ----------------------------
        self.start_btn  = self.start_img.get_rect(center=(self.w//2, 320))
        self.quit_btn   = self.quit_img.get_rect(center=(self.w//2, 400))
        self.resume_btn = self.resume_img.get_rect(center=(self.w//2, 320))
        self.menu_btn   = self.menu_img.get_rect(center=(self.w//2, 400))

    # ----------------------------
    # UI: hover-effekt
    # ----------------------------
    def _make_hover(self, image):
        hover = image.copy()
        hover.fill((40, 40, 40, 0), special_flags=pygame.BLEND_RGBA_ADD)
        return hover

    # ----------------------------
    # UI: håndter input
    # ----------------------------
    def handle_events(self, events, game_state):
        new_state = None
        action = None

        for event in events:
            # Vi fjerner ESC herfra fordi den håndteres i game.py for å unngå dobbelt-trykk
            if event.type == pygame.MOUSEBUTTONDOWN:
                if game_state == GAME_INTRO:
                    if self.start_btn.collidepoint(event.pos):
                        new_state = GAME_PLAYING
                    elif self.quit_btn.collidepoint(event.pos):
                        action = "QUIT"

                elif game_state == GAME_PAUSED:
                    if self.resume_btn.collidepoint(event.pos):
                        new_state = GAME_PLAYING
                    elif self.menu_btn.collidepoint(event.pos):
                        new_state = GAME_INTRO

        return new_state, action

    # ----------------------------
    # UI: draw dispatcher
    # ----------------------------
    def draw(self, game_state, hud_data=None):
        if game_state == GAME_INTRO:
            self._draw_intro()
        elif game_state == GAME_PAUSED:
            self._draw_pause()
        
        # Tegn HUD hvis vi er i spill, pause eller boss-fight
        if (game_state in [GAME_PLAYING, GAME_PAUSED, "BOSS_FIGHT"]) and hud_data:
            self._draw_hud(hud_data)

    # ----------------------------
    # UI: intro
    # ----------------------------
    def _draw_intro(self):
        self.screen.fill((30, 30, 40))

        title = self.big_font.render("GROW YOUR MIGHT, LITTLE KNIGHT", True, (255, 255, 255))
        self.screen.blit(title, title.get_rect(center=(self.w//2, 200)))

        self._draw_button(self.start_img, self.start_hover, self.start_btn)
        self._draw_button(self.quit_img,  self.quit_hover,  self.quit_btn)

    # ----------------------------
    # UI: pause
    # ----------------------------
    def _draw_pause(self):
        # Vi lager et gjennomsiktig lag over spillet
        overlay = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        text = self.big_font.render("PAUSED", True, (255, 255, 255))
        self.screen.blit(text, text.get_rect(center=(self.w//2, 200)))

        self._draw_button(self.resume_img, self.resume_hover, self.resume_btn)
        self._draw_button(self.menu_img,   self.menu_hover,   self.menu_btn)

    # ----------------------------
    # UI: HUD
    # ----------------------------
    def _draw_hud(self, data):
        # Flyttet level-indikatoren til rett over XP-baren som forespurt
        if "Lvl" in data:
            lvl_txt = self.font.render(f"LEVEL {data['Lvl']}", True, (255, 215, 0))
            txt_rect = lvl_txt.get_rect(center=(self.w//2, self.h - 55))
            self.screen.blit(lvl_txt, txt_rect)
            
        # Beholder original HUD-stil for andre data hvis nødvendig
        y = 10
        for key, value in data.items():
            if key != "Lvl": # Lvl håndteres over
                txt = self.font.render(f"{key}: {value}", True, (255, 255, 255))
                self.screen.blit(txt, (10, y))
                y += 26

    # ----------------------------
    # UI: tegn bildeknapp
    # ----------------------------
    def _draw_button(self, img, hover_img, rect):
        if rect.collidepoint(pygame.mouse.get_pos()):
            self.screen.blit(hover_img, rect)
        else:
            self.screen.blit(img, rect)