import pygame
import math
from entities.base_entity import BaseEntity
from systems.skill import Skill


class Boss(BaseEntity):
    def __init__(self, x, y, name="Boss"):
        super().__init__(x, y, 70, 90, name)

        self.color      = (200, 70, 70)
        self.trim_color = (120, 30, 30)
        self.glow_color = (255, 120, 80)

        self.max_hp = 200
        self.hp     = 200
        self.attack_damage = 15

        self.ai_timer    = 0
        self.ai_phase    = "patrol"   # patrol / chase / attack
        self.target      = None
        self.bob_t       = 0.0

        self.skill_timer   = 0
        self.skill_has_hit = False
        self.skill = Skill("Shockwave", damage=30, fatigue_cost=0, cooldown=180)

    # ─── AI ─────────────────────────────────────────────────
    def set_target(self, player):
        self.target = player

    def basic_ai(self, platforms):
        if self.target is None or self.target.dead:
            return

        dx = self.target.rect.centerx - self.rect.centerx
        dist = abs(dx)

        self.ai_timer += 1

        # 페이즈 전환
        if dist < 400:
            self.ai_phase = "chase"
        else:
            self.ai_phase = "patrol"

        if self.ai_phase == "patrol":
            spd = 2.2
            if (self.ai_timer // 120) % 2 == 0:
                self.vel.x = -spd; self.facing = -1
            else:
                self.vel.x =  spd; self.facing =  1

        elif self.ai_phase == "chase":
            spd = 3.5
            self.vel.x = math.copysign(spd, dx)
            self.facing = 1 if dx > 0 else -1

            # 가까우면 공격
            if dist < 110 and self.ai_timer % 60 == 0:
                self.start_attack()

            # 스킬 사용
            if dist < 200 and self.ai_timer % 180 == 0 and self.skill.can_use(0):
                self.skill.use()
                self.skill_timer   = 30
                self.skill_has_hit = False

        # 플랫폼 끝에서 방향 전환 (단순)
        if self.on_ground:
            ahead = pygame.Rect(
                self.rect.x + self.facing * (self.rect.w + 5),
                self.rect.bottom,
                10, 4
            )
            if not any(ahead.colliderect(p) for p in platforms):
                self.vel.x   = 0
                self.facing  = -self.facing

    def get_skill_hitbox(self):
        if not (5 <= self.skill_timer <= 26):
            return None
        w, h = 110, self.rect.height + 20
        if self.facing == 1:
            return pygame.Rect(self.rect.right - 15, self.rect.y - 10, w, h)
        else:
            return pygame.Rect(self.rect.left - w + 15, self.rect.y - 10, w, h)

    def check_skill_collision(self, target, event_bus, particle_system=None, floater_system=None):
        if self.dead or target.dead or target.invincible > 0:
            return
        sk = self.get_skill_hitbox()
        if sk is None or self.skill_has_hit:
            return
        if sk.colliderect(target.rect):
            self.skill_has_hit = True
            event_bus.emit("attack_hit", {
                "attacker": self,
                "target": target,
                "damage": self.skill.damage,
                "is_skill": True,
                "particle_system": particle_system,
                "floater_system": floater_system,
            })

    # ─── update ─────────────────────────────────────────────
    def update(self, dt, platforms, event_bus, particle_system=None):
        if self.dead:
            return

        self.basic_ai(platforms)
        super().update(dt, platforms, event_bus)

        self.skill.update()
        if self.skill_timer > 0:
            self.skill_timer -= 1
        if self.skill_timer <= 0:
            self.skill_has_hit = False

        self.bob_t += 0.06

    # ─── 렌더링 ─────────────────────────────────────────────
    def draw(self, screen, camera):
        if self.dead:
            return
        if self.invincible > 0 and (self.invincible // 4) % 2 == 1:
            return

        dr = self._get_draw_rect(camera)
        bob = int(math.sin(self.bob_t) * 2) if self.on_ground else 0

        # 그림자
        if self.on_ground:
            sh = pygame.Surface((dr.w - 10, 10), pygame.SRCALPHA)
            pygame.draw.ellipse(sh, (0, 0, 0, 80), sh.get_rect())
            screen.blit(sh, (dr.x + 5, dr.y + dr.h - 4))

        # 스킬 오라
        if self.skill_timer > 0:
            r = 70 + int(math.sin(self.bob_t * 4) * 8)
            aura = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(aura, (*self.glow_color, 60), (r, r), r)
            screen.blit(aura, (dr.centerx - r, dr.centery - r))

        flash = self.hit_flash > 0 and (self.hit_flash // 3) % 2 == 0
        c = (255, 255, 255) if flash else self.color

        # 다리
        pygame.draw.rect(screen, self.trim_color, (dr.x + 8,  dr.y + 66 + bob, 20, 24), border_radius=4)
        pygame.draw.rect(screen, self.trim_color, (dr.x + 42, dr.y + 66 + bob, 20, 24), border_radius=4)

        # 몸통
        pygame.draw.rect(screen, c, (dr.x + 4, dr.y + 28 + bob, dr.w - 8, 42), border_radius=8)

        # 머리
        pygame.draw.rect(screen, c, (dr.x + 10, dr.y + 2 + bob, dr.w - 20, 30), border_radius=10)

        # 뿔(보스 특징)
        pygame.draw.polygon(screen, self.trim_color, [
            (dr.x + 18, dr.y + 4 + bob),
            (dr.x + 14, dr.y - 14 + bob),
            (dr.x + 24, dr.y + 4 + bob),
        ])
        pygame.draw.polygon(screen, self.trim_color, [
            (dr.x + dr.w - 18, dr.y + 4 + bob),
            (dr.x + dr.w - 14, dr.y - 14 + bob),
            (dr.x + dr.w - 24, dr.y + 4 + bob),
        ])

        # 눈 (빨간 눈)
        eye_x = dr.x + (44 if self.facing == 1 else 24)
        pygame.draw.circle(screen, (255, 60, 60), (eye_x, dr.y + 17 + bob), 7)
        pygame.draw.circle(screen, (255, 200, 200), (eye_x, dr.y + 15 + bob), 3)

        # 공격 팔
        if self.attack_timer > 0:
            progress = 1 - self.attack_timer / 18
            arm_y = dr.y + 34 + bob - int(math.sin(progress * math.pi) * 12)
            arm_x = dr.x + dr.w - 4 if self.facing == 1 else dr.x - 24
            pygame.draw.rect(screen, self.color, (arm_x, arm_y, 24, 20), border_radius=5)
            if 4 <= self.attack_timer <= 15:
                g = pygame.Surface((44, 44), pygame.SRCALPHA)
                pygame.draw.circle(g, (*self.glow_color, 100), (22, 22), 22)
                screen.blit(g, (arm_x + 12 - 22, arm_y + 10 - 22))

        # 스킬 빔
        if self.skill_timer > 6:
            bl = 130
            bx = dr.right - 8 if self.facing == 1 else dr.left + 8 - bl
            by = dr.centery + bob - 8
            bw = int(18 * (self.skill_timer / 30))
            alpha = int(230 * (self.skill_timer / 30))
            bs = pygame.Surface((bl, bw + 12), pygame.SRCALPHA)
            pygame.draw.rect(bs, (*self.glow_color, alpha), (0, 6, bl, bw), border_radius=5)
            pygame.draw.rect(bs, (255, 255, 255, alpha // 3), (0, 8, bl, max(2, bw - 6)), border_radius=5)
            screen.blit(bs, (bx, by - 6))

        # 보스 이름 + HP 바
        font = pygame.font.SysFont("Arial", 13, bold=True)
        label = font.render(self.name, True, (255, 180, 180))
        screen.blit(label, (dr.centerx - label.get_width() // 2, dr.y - 22 + bob))

        bar_w = dr.w
        pygame.draw.rect(screen, (60, 20, 20), (dr.x, dr.y - 12 + bob, bar_w, 7), border_radius=3)
        hp_w = int(bar_w * max(0, self.hp / self.max_hp))
        pygame.draw.rect(screen, (220, 60, 60), (dr.x, dr.y - 12 + bob, hp_w, 7), border_radius=3)
