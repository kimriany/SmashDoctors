import pygame

from settings import GRAVITY, MAX_FALL_SPEED


class BaseEntity:
    def __init__(self, x, y, width, height, name="Entity"):
        self.name = name
        self.rect = pygame.Rect(x, y, width, height)
        self.vel = pygame.Vector2(0, 0)

        self.hp = 100
        self.dead = False

        self.on_ground = False
        self.facing = 1

        self.color = (255, 255, 255)

        self.attack_cooldown = 0
        self.attack_timer = 0
        self.attack_damage = 10
        self.has_hit = False

    def update(self, dt, platforms, event_bus):
        if self.dead:
            return

        self.apply_gravity()
        self.move_and_collide(platforms)

        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

        if self.attack_timer > 0:
            self.attack_timer -= 1

        if self.attack_timer <= 0:
            self.has_hit = False

        if self.hp <= 0 and not self.dead:
            self.dead = True
            event_bus.emit("entity_dead", {"entity": self})

    def apply_gravity(self):
        self.vel.y += GRAVITY
        self.vel.y = min(self.vel.y, MAX_FALL_SPEED)

    def move_and_collide(self, platforms):
        # X축 이동
        self.rect.x += int(self.vel.x)
        for platform in platforms:
            if self.rect.colliderect(platform):
                if self.vel.x > 0:
                    self.rect.right = platform.left
                elif self.vel.x < 0:
                    self.rect.left = platform.right
                self.vel.x = 0

        # Y축 이동
        self.on_ground = False
        self.rect.y += int(self.vel.y)
        for platform in platforms:
            if self.rect.colliderect(platform):
                if self.vel.y > 0:
                    self.rect.bottom = platform.top
                    self.vel.y = 0
                    self.on_ground = True
                elif self.vel.y < 0:
                    self.rect.top = platform.bottom
                    self.vel.y = 0

    def start_attack(self):
        if self.attack_cooldown <= 0:
            self.attack_timer = 15
            self.attack_cooldown = 30
            self.has_hit = False

    def get_attack_hitbox(self):
        if not (5 <= self.attack_timer <= 12):
            return None

        if self.facing == 1:
            return pygame.Rect(self.rect.right, self.rect.y + 15, 45, 30)
        else:
            return pygame.Rect(self.rect.left - 45, self.rect.y + 15, 45, 30)

    def check_attack_collision(self, target, event_bus):
        if self.dead or target.dead:
            return

        hitbox = self.get_attack_hitbox()
        if hitbox is None:
            return

        if self.has_hit:
            return

        if hitbox.colliderect(target.rect):
            self.has_hit = True
            event_bus.emit(
                "attack_hit",
                {
                    "attacker": self,
                    "target": target,
                    "damage": self.attack_damage,
                },
            )

    def take_damage(self, damage):
        self.hp -= damage
        self.hp = max(0, self.hp)

    def draw(self, screen, camera):
        draw_rect = camera.apply_rect(self.rect)
        pygame.draw.rect(screen, self.color, draw_rect, border_radius=8)

        hitbox = self.get_attack_hitbox()
        if hitbox:
            hitbox_rect = camera.apply_rect(hitbox)
            pygame.draw.rect(screen, (255, 230, 100), hitbox_rect, 2, border_radius=8)
