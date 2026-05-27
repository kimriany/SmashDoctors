import pygame
import math
from settings import GRAVITY, MAX_FALL_SPEED, BASE_KNOCKBACK, KNOCKBACK_SCALE


class BaseEntity:
    def __init__(self, x, y, width, height, name="Entity"):
        self.name = name
        self.rect = pygame.Rect(x, y, width, height)
        self.vel = pygame.Vector2(0, 0)

        self.hp = 100
        self.max_hp = 100
        self.dead = False

        self.on_ground = False
        self.facing = 1

        self.color = (255, 255, 255)

        self.attack_cooldown = 0
        self.attack_timer = 0
        self.attack_damage = 10
        self.has_hit = False

        # 스매시 스타일 누적 데미지 %
        self.damage_pct = 0

        # 점프
        self.jump_count = 0
        self.max_jumps = 2

        # 무적 프레임
        self.invincible = 0

        # 시각 효과
        self.hit_flash = 0
        self.shake_x = 0.0
        self.shake_y = 0.0

        # 더블점프 이펙트용
        self._prev_on_ground = False

    # ─── 물리 ──────────────────────────────────────────────
    def apply_gravity(self):
        self.vel.y += GRAVITY
        self.vel.y = min(self.vel.y, MAX_FALL_SPEED)

    def move_and_collide(self, platforms):
        # X
        self.rect.x += int(self.vel.x)
        for p in platforms:
            if self.rect.colliderect(p):
                if self.vel.x > 0:
                    self.rect.right = p.left
                elif self.vel.x < 0:
                    self.rect.left = p.right
                self.vel.x = 0

        # Y
        self._prev_on_ground = self.on_ground
        self.on_ground = False
        self.rect.y += int(self.vel.y)
        for p in platforms:
            if self.rect.colliderect(p):
                if self.vel.y > 0:
                    self.rect.bottom = p.top
                    self.vel.y = 0
                    self.on_ground = True
                    self.jump_count = 0
                elif self.vel.y < 0:
                    self.rect.top = p.bottom
                    self.vel.y = 0

    # ─── 공격 ──────────────────────────────────────────────
    def start_attack(self):
        if self.attack_cooldown <= 0:
            self.attack_timer = 18
            self.attack_cooldown = 32
            self.has_hit = False

    def get_attack_hitbox(self):
        if not (4 <= self.attack_timer <= 15):
            return None
        w, h = 55, 38
        if self.facing == 1:
            return pygame.Rect(self.rect.right, self.rect.y + 12, w, h)
        else:
            return pygame.Rect(self.rect.left - w, self.rect.y + 12, w, h)

    def check_attack_collision(self, target, event_bus, particle_system=None, floater_system=None):
        if self.dead or target.dead or target.invincible > 0:
            return
        hitbox = self.get_attack_hitbox()
        if hitbox is None or self.has_hit:
            return
        if hitbox.colliderect(target.rect):
            self.has_hit = True
            event_bus.emit("attack_hit", {
                "attacker": self,
                "target": target,
                "damage": self.attack_damage,
                "particle_system": particle_system,
                "floater_system": floater_system,
            })

    # ─── 피격 / 넉백 ────────────────────────────────────────
    def take_damage(self, damage):
        if self.invincible > 0:
            return
        self.hp = max(0, self.hp - damage)
        self.damage_pct += damage
        self.hit_flash = 14
        self.invincible = 20

    def apply_knockback(self, attacker, damage):
        """스매시 브라더스식 누적 넉백 계산"""
        kb = BASE_KNOCKBACK + self.damage_pct * KNOCKBACK_SCALE + damage * 0.3
        dir_x = 1 if attacker.rect.centerx < self.rect.centerx else -1
        self.vel.x = dir_x * kb
        self.vel.y = -(kb * 0.55)
        self.shake_x = dir_x * 8
        self.shake_y = -5

    # ─── 공통 update ────────────────────────────────────────
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
        if self.invincible > 0:
            self.invincible -= 1
        if self.hit_flash > 0:
            self.hit_flash -= 1

        # 쉐이크 감쇠
        self.shake_x *= 0.70
        self.shake_y *= 0.70

        if self.hp <= 0 and not self.dead:
            self.dead = True
            event_bus.emit("entity_dead", {"entity": self})

    # ─── 렌더링 헬퍼 ────────────────────────────────────────
    def _get_draw_rect(self, camera):
        r = camera.apply_rect(self.rect)
        r.x += int(self.shake_x)
        r.y += int(self.shake_y)
        return r

    def draw(self, screen, camera):
        draw_rect = self._get_draw_rect(camera)

        # 무적 깜빡임
        if self.invincible > 0 and (self.invincible // 4) % 2 == 1:
            return

        # 히트 플래시
        color = (255, 255, 255) if (self.hit_flash > 0 and (self.hit_flash // 3) % 2 == 0) else self.color
        pygame.draw.rect(screen, color, draw_rect, border_radius=8)

        # 어택 히트박스 시각화 (개발용, 필요 시 주석처리)
        hitbox = self.get_attack_hitbox()
        if hitbox:
            hb_draw = camera.apply_rect(hitbox)
            pygame.draw.rect(screen, (255, 220, 60), hb_draw, 2, border_radius=4)
