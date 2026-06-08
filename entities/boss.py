from systems.font_manager import font
import pygame
import math
from entities.base_entity import BaseEntity
from systems.skill import Skill


class Boss(BaseEntity):
    """HP 없음. damage_pct 누적 + blast zone 실점."""

    def __init__(self, x, y, name="Boss"):
        super().__init__(x, y, 72, 92, name)

        self.color      = (195, 65, 65)
        self.trim_color = (115, 25, 25)
        self.glow_color = (255, 110, 85)
        self.dark_color = (80,  10, 10)

        self.attack_damage = 16

        self.stocks = 3
        self.spawn_x = x
        self.spawn_y = y

        self.ai_timer = 0
        self.target   = None

        self.skill = Skill("Shockwave", damage=32, cooldown=160)
        self.skill_timer   = 0
        self.skill_has_hit = False

        self.bob_t  = 0.0
        self.walk_t = 0.0

    def set_target(self, player):
        self.target = player

    # ─── AI ───────────────────────────────────────────────────
    def basic_ai(self, platforms):
        if self.target is None or self.target.dead:
            return
        self.ai_timer += 1
        dx   = self.target.rect.centerx - self.rect.centerx
        dist = abs(dx)

        if dist < 380:
            spd = 3.8
            self.vel.x  = math.copysign(spd, dx)
            self.facing = 1 if dx > 0 else -1
            if dist < 120 and self.ai_timer % 55 == 0:
                self.start_attack()
            if dist < 220 and self.ai_timer % 160 == 0 and self.skill.can_use(0):
                self.skill.use()
                self.skill_timer   = 32
                self.skill_has_hit = False
        else:
            spd = 2.4
            self.vel.x  = math.copysign(spd, dx)
            self.facing = 1 if dx > 0 else -1

        # 낭떠러지 방지
        if self.on_ground:
            ahead = pygame.Rect(
                self.rect.x + self.facing * (self.rect.w + 4),
                self.rect.bottom, 8, 4)
            if not any(ahead.colliderect(p) for p in platforms):
                self.vel.x  = 0
                self.facing = -self.facing

    def get_skill_hitbox(self):
        if not (5 <= self.skill_timer <= 28):
            return None
        w = 120; h = self.rect.h + 24
        ox = self.rect.right - 14 if self.facing == 1 else self.rect.left - w + 14
        return pygame.Rect(ox, self.rect.y - 12, w, h)

    def check_skill_collision(self, target, event_bus, psys=None, fsys=None):
        if self.dead or target.dead or target.invincible > 0:
            return
        sk = self.get_skill_hitbox()
        if sk is None or self.skill_has_hit:
            return
        if sk.colliderect(target.rect):
            self.skill_has_hit = True
            event_bus.emit("attack_hit", {
                "attacker": self, "target": target,
                "damage": self.skill.damage, "is_skill": True,
                "particle_system": psys, "floater_system": fsys,
            })

    # ─── update ───────────────────────────────────────────────
    def update(self, dt, platforms, event_bus, psys=None):
        if self.dead:
            return
        self.basic_ai(platforms)
        super().update(dt, platforms, event_bus)
        self.skill.update()
        if self.skill_timer > 0: self.skill_timer -= 1
        if self.skill_timer <= 0: self.skill_has_hit = False
        self.bob_t  += 0.055
        if abs(self.vel.x) > 0.4:
            self.walk_t += 0.18

    # ─── 렌더링 ───────────────────────────────────────────────
    def draw(self, screen, camera):
        if self.dead:
            return
        if self.invincible > 0 and (self.invincible // 4) % 2 == 1:
            return

        dx, dy = self._get_draw_pos(camera)
        bob   = int(math.sin(self.bob_t) * 2.5) if self.on_ground else 0
        flash = self.hit_flash > 0 and (self.hit_flash // 3) % 2 == 0
        fc    = (255, 255, 255) if flash else self.color

        # 그림자
        if self.on_ground:
            sh = pygame.Surface((self.rect.w - 8, 10), pygame.SRCALPHA)
            pygame.draw.ellipse(sh, (0, 0, 0, 85), sh.get_rect())
            screen.blit(sh, (dx + 4, dy + self.rect.h - 4))

        # 스킬 오라
        if self.skill_timer > 0:
            r  = 72 + int(math.sin(self.bob_t * 5) * 9)
            a  = int(80 * self.skill_timer / 32)
            sf = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
            pygame.draw.circle(sf, (*self.glow_color, a), (r, r), r)
            screen.blit(sf, (dx + self.rect.w//2 - r, dy + self.rect.h//2 - r))

        # 다리
        lc = self.trim_color if not flash else (255,255,255)
        swing = int(math.sin(self.walk_t) * 8) if self.on_ground and abs(self.vel.x) > 0.4 else 0
        leg_y = dy + int(self.rect.h * 0.70) + bob
        pygame.draw.rect(screen, lc, (dx + 8,  leg_y - swing, 18, 26), border_radius=4)
        pygame.draw.rect(screen, lc, (dx + 46, leg_y + swing, 18, 26), border_radius=4)

        # 몸통
        pygame.draw.rect(screen, fc,
                         (dx + 4, dy + int(self.rect.h*0.28)+bob, self.rect.w-8, int(self.rect.h*0.44)),
                         border_radius=8)

        # 머리
        pygame.draw.rect(screen, fc,
                         (dx + 10, dy + 2+bob, self.rect.w-20, int(self.rect.h*0.30)),
                         border_radius=11)

        # 뿔
        for ox in [18, self.rect.w - 18]:
            pygame.draw.polygon(screen, self.trim_color, [
                (dx + ox,     dy + 4 + bob),
                (dx + ox - 5, dy - 16 + bob),
                (dx + ox + 5, dy + 4 + bob),
            ])

        # 눈
        ex = dx + (self.rect.w - 18 if self.facing == 1 else 18)
        pygame.draw.circle(screen, (255, 55, 55), (ex, dy + 16 + bob), 7)
        pygame.draw.circle(screen, (255, 200, 200), (ex, dy + 14 + bob), 3)
        pygame.draw.circle(screen, (255, 255, 255), (ex-2, dy+12+bob), 1)

        # 공격 팔
        if self.attack_timer > 0:
            prog = 1.0 - self.attack_timer / 20.0
            ay   = dy + int(self.rect.h*0.35) + bob - int(math.sin(prog*math.pi)*14)
            ax   = dx + self.rect.w - 4 if self.facing == 1 else dx - 26
            pygame.draw.rect(screen, fc, (ax, ay, 26, 22), border_radius=5)
            if 4 <= self.attack_timer <= 16:
                g = pygame.Surface((46,46), pygame.SRCALPHA)
                pygame.draw.circle(g, (*self.glow_color, 110), (23,23), 23)
                screen.blit(g, (ax+13-23, ay+11-23))

        # 스킬 빔
        if self.skill_timer > 6:
            t  = self.skill_timer / 32.0
            bl = 140
            bw = max(4, int(20 * t))
            bx = dx + self.rect.w - 8 if self.facing == 1 else dx - bl + 8
            by = dy + int(self.rect.h*0.50) + bob - bw//2
            bs = pygame.Surface((bl, bw+14), pygame.SRCALPHA)
            a  = int(235 * t)
            pygame.draw.rect(bs, (*self.glow_color, a),         (0,7, bl, bw), border_radius=5)
            pygame.draw.rect(bs, (*self.glow_color, a//3),      (0,2, bl, bw+10), border_radius=7)
            pygame.draw.rect(bs, (255,255,255,int(a*0.65)),     (0,7+bw//2-2, bl, 4), border_radius=5)
            screen.blit(bs, (bx, by-7))

        # 보스 이름 + damage%
        fnt = font(13, bold=True)
        nm  = fnt.render(f"{self.name}  {int(self.damage_pct)}%",
                         True, (255, 170, 170))
        screen.blit(nm, (dx + self.rect.w//2 - nm.get_width()//2,
                         dy - 20 + bob))
