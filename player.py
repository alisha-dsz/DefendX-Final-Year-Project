import pygame
import random
import os

BASE_DIR = os.path.dirname(__file__)

# ----------------- Sounds -----------------
try:
    import settings_popup
except Exception:
    settings_popup = None

PUNCH_SOUND = None
KICK_SOUND = None
try:
    punch_path = os.path.join(BASE_DIR, "assets", "sounds", "punch.ogg")
    kick_path = os.path.join(BASE_DIR, "assets", "sounds", "kick.ogg")
    if os.path.isfile(punch_path):
        PUNCH_SOUND = pygame.mixer.Sound(punch_path)
    if os.path.isfile(kick_path):
        KICK_SOUND = pygame.mixer.Sound(kick_path)
except Exception:
    PUNCH_SOUND = None
    KICK_SOUND = None

def load_scaled(path, scale):
    img = pygame.image.load(os.path.join(BASE_DIR, path)).convert_alpha()
    return pygame.transform.smoothscale(img, scale)


class Fighter:
    def __init__(self, x, y, is_enemy=False, difficulty="normal"):
        self.is_enemy = is_enemy
        self.flip = is_enemy
        self.ground_y = y
        self.scale = (240, 320)

        # ---------------- Difficulty ----------------
        diff = {
            "easy":   {"speed": 2.5, "think": 30, "react": 0.25},
            "normal": {"speed": 3.2, "think": 20, "react": 0.45},
            "hard":   {"speed": 4.0, "think": 15, "react": 0.65},
        }[difficulty]

        self.speed = diff["speed"]
        self.ai_think_delay = diff["think"]
        self.reaction_chance = diff["react"]
        self.reaction_range = 120

        # ---------------- Animations ----------------
        if not self.is_enemy:
            self.animations = {
                "idle": [
                    load_scaled("assets/hero/walk/walk0.png", self.scale)
                ],

                "walk": [
                    load_scaled("assets/hero/walk/walk0.png", self.scale),
                    load_scaled("assets/hero/walk/walk1.png", self.scale),
                    load_scaled("assets/hero/walk/walk2.png", self.scale),
                ],

                # ✅ Punch (correct order)
                "punch": [
                    load_scaled("assets/hero/punch/rightpunch2.png", self.scale),
                    load_scaled("assets/hero/punch/rightpunch1.png", self.scale),
                ],

                # ✅ Kick
                "kick": [
                    load_scaled("assets/hero/kick/kick.png", self.scale),
                    
                ],

                # ✅ Block
                "block": [
                    load_scaled("assets/hero/block/block.png", self.scale),
                ],

                # ✅ Dodge
                "dodge": [
                    load_scaled("assets/hero/dodge/dodge.png", self.scale),
                ],
            }
        else:
            self.animations = {
                "idle": [
                    load_scaled("enemy/walk/enemywalk1.png", self.scale)
                ],

                "walk": [
                    load_scaled("enemy/walk/enemywalk1.png", self.scale),
                    load_scaled("enemy/walk/enemywalk2.png", self.scale),
                ],

                "punch": [
                    load_scaled("enemy/punch/enemypunch.png", self.scale)
                ],

                # ✅ Enemy kick
                "kick": [
                    load_scaled("enemy/kick/enemykick.png", self.scale)
                ],

                "block": [
                    load_scaled("enemy/dodge/enemydodge.png", self.scale)
                ],

                "dodge": [
                    load_scaled("enemy/dodge/enemydodge.png", self.scale)
                ],
            }

        # ---------------- State ----------------
        self.action = "idle"
        self.frame = 0
        self.image = self.animations[self.action][0]
        self.rect = self.image.get_rect(midbottom=(x, y))
        self.update_time = pygame.time.get_ticks()

        self.running = False
        self.attacking = False
        self.kicking = False
        self.blocking = False
        self.dodging = False
        self.invincible = False
        self.has_hit = False
        self.alive = True

        # ---------------- Stats ----------------
        self.health = 100
        self.cooldown = 0
        self.ai_timer = 0
        self.knockback = 0
        self.dodge_timer = 0

    # ==================================================
    def move(self, screen_width, target=None):
        if not self.alive:
            return

        dx = 0
        self.running = False
        keys = pygame.key.get_pressed()

        # ================= PLAYER =================
        if not self.is_enemy:
            if target:
                self.flip = target.rect.centerx < self.rect.centerx

            if keys[pygame.K_b]:
                self.block()

            elif keys[pygame.K_v]:
                self.dodge()

            if not (self.attacking or self.dodging or self.blocking):
                if keys[pygame.K_a]:
                    dx = -self.speed
                    self.running = True
                if keys[pygame.K_d]:
                    dx = self.speed
                    self.running = True
                if keys[pygame.K_f]:
                    self.attack("punch")
                if keys[pygame.K_g]:
                    self.attack("kick")

        # ================= ENEMY =================
        else:
            distance = target.rect.centerx - self.rect.centerx
            abs_dist = abs(distance)
            self.flip = distance < 0
            self.ai_timer += 1

            if abs_dist > 110:
                dx = self.speed if distance > 0 else -self.speed
                self.running = True

            if abs_dist <= self.reaction_range:
                if self.ai_timer >= self.ai_think_delay:
                    if random.random() < self.reaction_chance:
                        self.attack(random.choice(["punch", "kick"]))
                        self.ai_timer = 0

            if not self.dodging and random.random() < 0.01:
                self.dodge()

        # Apply movement
        self.rect.x += dx + self.knockback
        self.knockback *= 0.85
        self.rect.left = max(0, self.rect.left)
        self.rect.right = min(screen_width, self.rect.right)

        if self.cooldown > 0:
            self.cooldown -= 1

    # ==================================================
    def attack(self, kind):
        if self.cooldown == 0 and not self.blocking:
            self.attacking = True
            self.kicking = (kind == "kick")
            self.has_hit = False
            self.set_action(kind)
            self.cooldown = 40 if kind == "punch" else 55
            # play SFX (respect settings_popup mute/volume)
            try:
                vol = settings_popup.SFX_VOLUME if (settings_popup and settings_popup.SFX_ENABLED) else 0
            except Exception:
                vol = 0.6
            try:
                if kind == "punch" and PUNCH_SOUND:
                    PUNCH_SOUND.set_volume(vol)
                    PUNCH_SOUND.play()
                if kind == "kick" and KICK_SOUND:
                    KICK_SOUND.set_volume(vol)
                    KICK_SOUND.play()
            except Exception:
                pass

    def block(self):
        if not self.blocking:
            self.blocking = True
            self.attacking = False
            self.dodging = False
            self.invincible = True
            self.set_action("block")

    def dodge(self):
        if not self.dodging:
            self.attacking = False
            self.blocking = False
            self.dodging = True
            self.invincible = True
            self.dodge_timer = 18
            self.set_action("dodge")
            self.cooldown = 25

    def take_damage(self, amount, attacker_flip=False):
        # Ignore damage while invincible, blocking, or dodging
        if self.invincible or self.blocking or self.dodging:
            return

        self.health = max(0, self.health - int(amount))
        self.knockback = 8 if not attacker_flip else -8

        if self.health == 0:
            self.alive = False

    # ==================================================
    def set_action(self, action):
        if action != self.action:
            self.action = action
            self.frame = 0
            self.update_time = pygame.time.get_ticks()

    def update(self):
        if self.dodge_timer > 0:
            self.dodge_timer -= 1
        else:
            self.invincible = False

        if not (self.attacking or self.dodging or self.blocking):
            self.set_action("walk" if self.running else "idle")

        if pygame.time.get_ticks() - self.update_time > 200:
            self.frame += 1
            self.update_time = pygame.time.get_ticks()

        if self.frame >= len(self.animations[self.action]):
            self.frame = 0
            self.attacking = False
            self.kicking = False
            self.blocking = False
            self.dodging = False
            self.has_hit = False

        self.image = self.animations[self.action][self.frame]
        self.rect = self.image.get_rect(midbottom=(self.rect.centerx, self.ground_y))

    def draw(self, surface):
        surface.blit(
            pygame.transform.flip(self.image, self.flip, False),
            self.rect
        )
