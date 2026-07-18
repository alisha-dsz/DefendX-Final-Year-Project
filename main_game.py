def run_game():
    import pygame
    import os
    import random
    from .player import Fighter
    from .rounds import ROUNDS

    # ----------------- Pygame Initialization -----------------
    pygame.init()
    pygame.font.init()
    pygame.mixer.init()

    BASE_WIDTH, BASE_HEIGHT = 1280, 720
    screen = pygame.display.set_mode((BASE_WIDTH, BASE_HEIGHT))
    pygame.display.set_caption("DefendX")

    clock = pygame.time.Clock()
    FPS = 60

    # ----------------- Paths -----------------
    BASE_DIR = os.path.dirname(__file__)
    ASSETS_DIR = os.path.join(BASE_DIR, "assets")

    # ----------------- Background helper -----------------
    def load_background_for_round(round_num):
        idx = ((round_num - 1) % 3) + 1
        img_name = f"img {idx}.png"
        try:
            bg = pygame.image.load(os.path.join(BASE_DIR, img_name)).convert()
            bg = pygame.transform.scale(bg, (BASE_WIDTH, BASE_HEIGHT))
            return bg
        except Exception:
            s = pygame.Surface((BASE_WIDTH, BASE_HEIGHT))
            s.fill((0, 0, 0))
            return s

    background = load_background_for_round(1)

    # ----------------- Intro Images -----------------
    INTRO_DIR = os.path.join(ASSETS_DIR, "intro")
    intro_images = {
        4: pygame.image.load(os.path.join(INTRO_DIR, "4.png")).convert_alpha(),
        3: pygame.image.load(os.path.join(INTRO_DIR, "3.png")).convert_alpha(),
        2: pygame.image.load(os.path.join(INTRO_DIR, "2.png")).convert_alpha(),
        1: pygame.image.load(os.path.join(INTRO_DIR, "1.png")).convert_alpha(),
    }

    # ----------------- Sounds -----------------
    intro_sound = pygame.mixer.Sound(os.path.join(ASSETS_DIR, "music", "321fight.mp3"))

    bg_music_path = os.path.join(ASSETS_DIR, "music", "bg.mp3")

    gameover_sound = pygame.mixer.Sound(os.path.join(BASE_DIR, "gameover.mp3"))

    # Apply user audio preferences (music + sfx)
    try:
        import profile_popup
        import user_state
        import settings_popup
        import leaderboard

        current_user = profile_popup.get_current_user()
        if current_user:
            music_enabled, sfx_enabled = user_state.get_user_settings(current_user)
        else:
            music_enabled, sfx_enabled = settings_popup.MUSIC_ENABLED, settings_popup.SFX_ENABLED

        # SFX: intro_sound and gameover_sound
        intro_sound.set_volume(settings_popup.SFX_VOLUME if sfx_enabled else 0)
        gameover_sound.set_volume(settings_popup.SFX_VOLUME if sfx_enabled else 0)

        # Music: pygame mixer music volume
        pygame.mixer.music.set_volume(settings_popup.MUSIC_VOLUME if music_enabled else 0)
    except Exception:
        # fallback to defaults
        intro_sound.set_volume(0.8)
        pygame.mixer.music.set_volume(0.5)

    # ----------------- Game Over Image -----------------
    gameover_img = pygame.image.load(os.path.join(ASSETS_DIR, "gameover.png")).convert_alpha()
    gameover_img = pygame.transform.scale(gameover_img, (600, 300))

    # ----------------- Fonts -----------------
    hud_font = pygame.font.SysFont("arial", 26)
    sub_font = pygame.font.SysFont("arial", 28)

    # ----------------- Button Class -----------------
    class Button:
        def __init__(self, x, y, width, height, text, font, color=(100, 100, 100), hover_color=(150, 150, 150), text_color=(255, 255, 255)):
            self.rect = pygame.Rect(x, y, width, height)
            self.text = text
            self.font = font
            self.color = color
            self.hover_color = hover_color
            self.text_color = text_color
            self.hovered = False

        def is_clicked(self, pos):
            return self.rect.collidepoint(pos)

        def update(self, pos):
            self.hovered = self.rect.collidepoint(pos)

        def draw(self, surface):
            color = self.hover_color if self.hovered else self.color
            pygame.draw.rect(surface, color, self.rect, border_radius=8)
            pygame.draw.rect(surface, (200, 200, 200), self.rect, 2, border_radius=8)
            text_surf = self.font.render(self.text, True, self.text_color)
            text_rect = text_surf.get_rect(center=self.rect.center)
            surface.blit(text_surf, text_rect)

    # ----------------- Health Bar Class -----------------
    class HealthBar:
        def __init__(self, x, y, width=300, height=26, max_health=100, name=""):
            self.x = x
            self.y = y
            self.width = width
            self.height = height
            self.max_health = max_health
            self.current_health = max_health
            self.display_health = max_health
            self.name = name
            self.font = pygame.font.SysFont("arial", 18, bold=True)
            self.border_radius = 12
            self.padding = 4
            self.flash_timer = 0

        def update(self, health):
            self.current_health = max(0, health)
            if self.display_health > self.current_health:
                self.display_health -= max(
                    0.5, (self.display_health - self.current_health) * 0.15
                )
            else:
                self.display_health = self.current_health

        def get_color(self, ratio):
            if ratio > 0.6:
                return (60, 220, 80)
            elif ratio > 0.3:
                return (240, 210, 60)
            else:
                return (240, 60, 60)

        def draw(self, surface):
            ratio = max(0, min(1, self.current_health / self.max_health))
            lag_ratio = self.display_health / self.max_health

            pygame.draw.rect(
                surface, (0, 0, 0),
                (self.x - 3, self.y - 3, self.width + 6, self.height + 6),
                border_radius=self.border_radius
            )

            pygame.draw.rect(
                surface, (30, 30, 30),
                (self.x, self.y, self.width, self.height),
                border_radius=self.border_radius
            )

            lag_width = int((self.width - self.padding * 2) * lag_ratio)
            pygame.draw.rect(
                surface, (200, 200, 200),
                (self.x + self.padding, self.y + self.padding,
                 lag_width, self.height - self.padding * 2),
                border_radius=self.border_radius
            )

            fill_width = int((self.width - self.padding * 2) * ratio)
            color = self.get_color(ratio)
            pygame.draw.rect(
                surface, color,
                (self.x + self.padding, self.y + self.padding,
                 fill_width, self.height - self.padding * 2),
                border_radius=self.border_radius
            )

                    # Low-health glow
            if ratio < 0.3:
                glow = pygame.Surface(
                    (fill_width + 10, self.height), pygame.SRCALPHA
                )
                pygame.draw.rect(
                    glow, (*color, 100),
                    glow.get_rect(),
                    border_radius=self.border_radius
                )
                surface.blit(glow, (self.x + self.padding - 5, self.y))

            # Critical flashing border
            if ratio < 0.25:
                self.flash_timer = (self.flash_timer + 1) % 30
                if self.flash_timer < 15:
                    pygame.draw.rect(
                        surface,
                        (255, 80, 80),
                        (self.x, self.y, self.width, self.height),
                        2,
                        border_radius=self.border_radius
                    )


            surface.blit(
                self.font.render(self.name, True, (230, 230, 230)),
                (self.x, self.y - 26)
            )
            # draw numeric health points to the right of the bar
            hp_surf = self.font.render(str(int(self.current_health)), True, (230, 230, 230))
            surface.blit(hp_surf, (self.x + self.width + 10, self.y))

    # ----------------- Game Setup -----------------
    current_round = 1
    round_data = ROUNDS[current_round]
    # Best-of-2-wins match state (up to 3 rounds, tiebreaker on round 3 if 1-1)
    player_round_wins = 0
    enemy_round_wins = 0
    rounds_played = 0
    MAX_ROUNDS = 3
    match_result = None
    GROUND_Y = 570

    PLAYER_START_X = 300
    player = Fighter(PLAYER_START_X, GROUND_Y)
    enemy = Fighter(980, GROUND_Y, is_enemy=True, difficulty=round_data["difficulty"])

    player_name = current_user if current_user else "PLAYER"
    player_bar = HealthBar(40, 30, name=player_name)
    enemy_bar = HealthBar(BASE_WIDTH - 340, 30, name="ENEMY")

    ok_button = Button(BASE_WIDTH // 2 - 60, BASE_HEIGHT // 2 + 180, 120, 50, "OK", sub_font)

    # ----------------- Feedback System -----------------
    feedback_text = ""
    feedback_timer = 0
    feedback_font = pygame.font.SysFont("arial", 36, bold=True)

    def evaluate_attack(attacker, defender):
        """Evaluate attack accuracy and return feedback if perfect"""
        # Base score from timing (frame)
        frame_score = 100 - (attacker.frame * 30)
        
        # Distance bonus
        distance = abs(attacker.rect.centerx - defender.rect.centerx)
        dist_bonus = 20 if distance < 50 else 10 if distance < 100 else 0
        
        # Random factor
        random_factor = random.randint(-10, 10)
        
        total_score = frame_score + dist_bonus + random_factor
        total_score = max(0, min(100, total_score))
        
        if total_score >= 90:
            action = attacker.action
            if action == "punch":
                feedback = random.choice(["Perfect Punch!", "Excellent Punch!", "Great Punch!"])
            elif action == "kick":
                feedback = random.choice(["Perfect Kick!", "Excellent Kick!", "Great Kick!"])
            else:
                feedback = f"Perfect {action.title()}!"
            return feedback
        return None

    def evaluate_defense(defender, action):
        """Return feedback for perfect defense"""
        if action == "dodge":
            return random.choice(["Perfect Dodge!", "Excellent Dodge!", "Great Dodge!"])
        elif action == "block":
            return random.choice(["Perfect Block!", "Excellent Block!", "Great Block!"])
        return None

    INTRO, PLAYING, END = "intro", "playing", "end"
    game_state = INTRO

    intro_count = 4
    last_intro_time = pygame.time.get_ticks()
    intro_sound_played = False

    end_start_time = 0
    gameover_played = False
    MIN_END_TIME = 3

    # ----------------- Main Loop -----------------
    running = True
    while running:
        clock.tick(FPS)
        now = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # only accept left-click and only after end-screen delay
                if event.button == 1 and game_state == END and end_start_time:
                    elapsed = (now - end_start_time) / 1000.0
                    if elapsed >= MIN_END_TIME and ok_button.is_clicked(event.pos):
                        return "menu"

        if game_state == INTRO:
            screen.fill((0, 0, 0))

            if not intro_sound_played:
                intro_sound.play()
                intro_sound_played = True

            img = intro_images[intro_count]
            screen.blit(img, img.get_rect(center=(BASE_WIDTH // 2, BASE_HEIGHT // 2)))

            if pygame.time.get_ticks() - last_intro_time > 1000:
                intro_count -= 1
                last_intro_time = pygame.time.get_ticks()
                if intro_count == 0:
                    pygame.mixer.music.load(bg_music_path)
                    pygame.mixer.music.play(-1)
                    game_state = PLAYING

        elif game_state == PLAYING:
            screen.blit(background, (0, 0))

            player.move(BASE_WIDTH, enemy)
            enemy.move(BASE_WIDTH, player)

            if player.attacking and not player.has_hit and player.rect.colliderect(enemy.rect):
                enemy.take_damage(15, player.flip)
                player.has_hit = True
                feedback = evaluate_attack(player, enemy)
                if feedback:
                    feedback_text = feedback
                    feedback_timer = 30  # 0.5 seconds

            if enemy.attacking and not enemy.has_hit and enemy.rect.colliderect(player.rect):
                if player.dodging:
                    # Successful dodge
                    feedback = evaluate_defense(player, "dodge")
                    if feedback:
                        feedback_text = feedback
                        feedback_timer = 30
                else:
                    player.take_damage(15, enemy.flip)
                enemy.has_hit = True

            player.update()
            enemy.update()
            player.draw(screen)
            enemy.draw(screen)

            player_bar.update(player.health)
            enemy_bar.update(enemy.health)
            player_bar.draw(screen)
            enemy_bar.draw(screen)

            # draw round score (player wins : enemy wins)
            score_surf = sub_font.render(f"{player_round_wins} : {enemy_round_wins}", True, (255, 215, 0))
            screen.blit(score_surf, score_surf.get_rect(center=(BASE_WIDTH // 2, 20)))

            # Update and draw feedback
            if feedback_timer > 0:
                feedback_timer -= 1
                if feedback_text:
                    feedback_surf = feedback_font.render(feedback_text, True, (255, 255, 255))
                    feedback_rect = feedback_surf.get_rect(center=(BASE_WIDTH // 2, BASE_HEIGHT // 2 - 100))
                    # Add shadow
                    shadow_surf = feedback_font.render(feedback_text, True, (0, 0, 0))
                    shadow_rect = shadow_surf.get_rect(center=(BASE_WIDTH // 2 + 2, BASE_HEIGHT // 2 - 98))
                    screen.blit(shadow_surf, shadow_rect)
                    screen.blit(feedback_surf, feedback_rect)

            if enemy.health <= 0 or player.health <= 0:
                # round finished
                if enemy.health <= 0:
                    player_round_wins += 1
                    round_winner = "PLAYER"
                else:
                    enemy_round_wins += 1
                    round_winner = "ENEMY"

                rounds_played += 1

                # check match end: first to 2 wins, or after round 3
                if player_round_wins == 2 or enemy_round_wins == 2 or rounds_played >= MAX_ROUNDS:
                    match_result = "PLAYER" if player_round_wins > enemy_round_wins else "ENEMY"
                    pygame.mixer.music.stop()
                    # record win for logged-in user
                    try:
                        if match_result == "PLAYER" and current_user:
                            user_state.add_win(current_user, mode="button")
                    except Exception:
                        pass
                    game_state = END
                    end_start_time = pygame.time.get_ticks()
                else:
                    # advance to next round/level
                    current_round = min(len(ROUNDS), current_round + 1)
                    round_data = ROUNDS[current_round]
                    # recreate enemy with new difficulty
                    enemy = Fighter(980, GROUND_Y, is_enemy=True, difficulty=round_data["difficulty"])
                    # update background for the new round/level
                    background = load_background_for_round(current_round)
                    # reset health
                    player.health = 100
                    enemy.health = 100
                    player.alive = True
                    enemy.alive = True
                    # reset player position and transient state so the next round starts from the beginning
                    player.rect.centerx = PLAYER_START_X
                    player.knockback = 0
                    player.attacking = False
                    player.kicking = False
                    player.blocking = False
                    player.dodging = False
                    player.invincible = False
                    player.has_hit = False
                    player.running = False
                    player.set_action("idle")
                    # brief pause between rounds
                    pygame.time.wait(700)

        elif game_state == END:
            if not gameover_played:
                gameover_sound.play()
                gameover_played = True

            # Draw leaderboard with result and OK button prompt
            leaderboard.draw_leaderboard(screen, BASE_WIDTH, BASE_HEIGHT, match_result)

            # show and enable OK button only after MIN_END_TIME seconds
            if end_start_time:
                elapsed = (now - end_start_time) / 1000.0
                if elapsed >= MIN_END_TIME:
                    mouse_pos = pygame.mouse.get_pos()
                    ok_button.update(mouse_pos)
                    ok_button.draw(screen)

        pygame.display.flip()

    return "menu"
