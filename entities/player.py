import pygame
import math
from settings import PLAYER_SPEED, PLAYER_JUMP_POWER
from entities.base_entity import BaseEntity
from systems.skill import Skill


class Player(BaseEntity):
    def __init__(self, x, y, name="Player", player_id=1):
        super().__init__(x, y, 44, 64, name)

        self.player_id = player_id

        # 색상 테마
        if player_id == 1:
            self.color       = (60,  130, 230)
            self.trim_color  = (30,   70, 160)
            self.glow_color  = (120, 180, 255)
        else:
            self.color       = (220,  60,  60)
            self.trim_color  = (150,  25,  25)
            self.glow_color  = (255, 140, 120)

        # 스탯
        self.max_hp      = 150
        self.hp          = 150
        self.max_fatigue = 100
        self.fatigue     = 0
        self.attack_damage = 12

        # 스톡 (목숨)
        self.stocks      = 3
        self.respawning  = False
        self.respawn_timer = 0
        self.spawn_x     = x
        self.spawn_y     = y

        self.job = "default"
        self.skills = {
            "skill_1": Skill(
                name="Energy Burst",
                damage=28,
                fatigue_cost=30,
                cooldown=90,
            )
        }

        # 스킬 히트박스
        self.skill_timer   = 0
        self.skill_has_hit = False

        # 애니메이션
        self.bob_t = 0.0
        self.walk_t = 0.0
        self.last_vx = 0.0

    # ─── 입력 (연속키) ──────────────────────────────────────
    def handle_input(self, keys, p_id=None):
        if self.dead or self.respawning:
            return

        pid = p_id if p_id else self.player_id
        moving = False

        if pid == 1:
            left_key  = pygame.K_a
            right_key = pygame.K_d
        else:
            left_key  = pygame.K_LEFT
            right_key = pygame.K_RIGHT

        if keys[left_key]:
            self.vel.x = -PLAYER_SPEED
            self.facing = -1
            moving = True
        if keys[right_key]:
            self.vel.x = PLAYER_SPEED
            self.facing = 1
            moving = True

        if not moving:
            self.vel.x *= 0.75
            if abs(self.vel.x) < 0.2:
                self.vel.x = 0

        self.last_vx = self.vel.x

    # ─── 입력 (단발키) ──────────────────────────────────────
    def handle_keydown(self, key, event_bus, particle_system=None):
        if self.dead or self.respawning:
            return

        pid = self.player_id
        if pid == 1:
            jump_key   = pygame.K_w
            attack_key = pygame.K_f
            skill_key  = pygame.K_g
        else:
            jump_key   = pygame.K_UP
            attack_key = pygame.K_l
            skill_key  = pygame.K_SEMICOLON

        if key == jump_key:
            self.jump(particle_system)
        if key == attack_key:
            self.start_attack()
            if particle_system:
                ox = self.rect.right if self.facing == 1 else self.rect.left - 20
                particle_system.spawn(ox, self.rect.centery, self.glow_color,
                                      count=8, speed=5, life=18, r=4)
        if key == skill_key:
            self.use_skill("skill_1", event_bus, particle_system)

    def jump(self, particle_system=None):
        if self.jump_count < self.max_jumps:
            power = PLAYER_JUMP_POWER if self.jump_count == 0 else PLAYER_JUMP_POWER * 0.85
            self.vel.y = power
            self.jump_count += 1
            if particle_system:
                particle_system.spawn_jump(self.rect.centerx, self.rect.bottom, self.glow_color)

    def use_skill(self, skill_key, event_bus, particle_system=None):
        skill = self.skills.get(skill_key)
        if skill is None:
            return
        if skill.can_use(self.fatigue):
            skill.use()
            self.fatigue += skill.fatigue_cost
            self.skill_timer   = 28
            self.skill_has_hit = False
            event_bus.emit("skill_used", {"user": self, "skill": skill})
            if particle_system:
                particle_system.spawn_skill(self.rect.centerx, self.rect.centery, self.glow_color)

    def get_skill_hitbox(self):
        if not (6 <= self.skill_timer <= 24):
            return None
        w, h = 90, self.rect.height
        if self.facing == 1:
            return pygame.Rect(self.rect.right - 10, self.rect.y, w, h)
        else:
            return pygame.Rect(self.rect.left - w + 10, self.rect.y, w, h)

    def check_skill_collision(self, target, event_bus, particle_system=None, floater_system=None):
        if self.dead or target.dead or target.invincible > 0:
            return
        sk = self.get_skill_hitbox()
        if sk is None or self.skill_has_hit:
            return
        if sk.colliderect(target.rect):
            self.skill_has_hit = True
            skill = list(self.skills.values())[0]
            event_bus.emit("attack_hit", {
                "attacker": self,
                "target": target,
                "damage": skill.damage,
                "is_skill": True,
                "particle_system": particle_system,
                "floater_system": floater_system,
            })

    # ─── 스톡 / 리스폰 ──────────────────────────────────────
    def lose_stock(self, event_bus):
        self.stocks -= 1
        self.hp = self.max_hp
        self.damage_pct = 0
        self.vel = pygame.Vector2(0, 0)
        if self.stocks <= 0:
            self.dead = True
            event_bus.emit("entity_dead", {"entity": self})
        else:
            self.respawning = True
            self.respawn_timer = 90

    def do_respawn(self, particle_system=None):
        self.respawning = False
        self.rect.x = self.spawn_x
        self.rect.y = self.spawn_y
        self.vel = pygame.Vector2(0, 0)
        self.invincible = 120
        if particle_system:
            particle_system.spawn_respawn(self.rect.centerx, self.rect.centery, self.glow_color)

    # ─── update ─────────────────────────────────────────────
    def update(self, dt, platforms, event_bus, particle_system=None):
        if self.respawning:
            self.respawn_timer -= 1
            if self.respawn_timer <= 0:
                self.do_respawn(particle_system)
            return

        super().update(dt, platforms, event_bus)

        if self.fatigue > 0:
            self.fatigue = max(0, self.fatigue - 0.3)

        for skill in self.skills.values():
            skill.update()

        if self.skill_timer > 0:
            self.skill_timer -= 1
        if self.skill_timer <= 0:
            self.skill_has_hit = False

        self.bob_t += 0.07
        if abs(self.vel.x) > 0.5:
            self.walk_t += 0.22

    # ─── 렌더링 ─────────────────────────────────────────────
    def draw(self, screen, camera):
        if self.dead:
            return
        if self.respawning:
            # 리스폰 대기 중: 하늘에 아이콘 표시
            self._draw_respawn_icon(screen, camera)
            return

        # 무적 깜빡임
        if self.invincible > 0 and (self.invincible // 4) % 2 == 1:
            return

        dr = self._get_draw_rect(camera)
        bob = int(math.sin(self.bob_t) * 2) if self.on_ground else 0

        # 그림자
        if self.on_ground:
            shadow_rect = pygame.Rect(dr.x + 5, dr.y + dr.h - 2, dr.w - 10, 8)
            shadow_surf = pygame.Surface((shadow_rect.w, shadow_rect.h), pygame.SRCALPHA)
            pygame.draw.ellipse(shadow_surf, (0, 0, 0, 80), shadow_surf.get_rect())
            screen.blit(shadow_surf, shadow_rect)

        # 스킬 이펙트 오라
        if self.skill_timer > 0:
            self._draw_skill_aura(screen, dr, bob)

        # 다리
        self._draw_legs(screen, dr, bob)

        # 몸통
        flash = self.hit_flash > 0 and (self.hit_flash // 3) % 2 == 0
        body_color = (255, 255, 255) if flash else self.color
        body_rect = pygame.Rect(dr.x + 2, dr.y + 22 + bob, dr.w - 4, 32)
        pygame.draw.rect(screen, body_color, body_rect, border_radius=6)

        # 가운 (trim)
        coat_rect = pygame.Rect(dr.x + 4, dr.y + 24 + bob, 14, 28)
        pygame.draw.rect(screen, self.trim_color, coat_rect, border_radius=3)

        # 머리
        head_rect = pygame.Rect(dr.x + 6, dr.y + 2 + bob, 32, 24)
        pygame.draw.rect(screen, body_color, head_rect, border_radius=9)

        # 안경
        eye_x = dr.x + (24 if self.facing == 1 else 10)
        eye_y = dr.y + 9 + bob
        pygame.draw.rect(screen, (200, 230, 255), (eye_x - 7, eye_y - 5, 12, 10), border_radius=3)
        pygame.draw.rect(screen, (80, 80, 100), (eye_x - 7, eye_y - 5, 12, 10), 1, border_radius=3)
        pygame.draw.circle(screen, (20, 20, 40), (eye_x - 1, eye_y), 3)

        # 공격 팔
        if self.attack_timer > 0:
            self._draw_attack_arm(screen, dr, bob)

        # 스킬 빔
        if self.skill_timer > 6:
            self._draw_skill_beam(screen, dr, bob)

    def _draw_legs(self, screen, dr, bob):
        leg_color = self.trim_color
        if self.on_ground:
            walk = int(math.sin(self.walk_t) * 6) if abs(self.vel.x) > 0.5 else 0
            pygame.draw.rect(screen, leg_color, (dr.x + 6,  dr.y + 52 + bob - walk, 13, 14), border_radius=3)
            pygame.draw.rect(screen, leg_color, (dr.x + 24, dr.y + 52 + bob + walk, 13, 14), border_radius=3)
        else:
            pygame.draw.rect(screen, leg_color, (dr.x + 6,  dr.y + 52 + bob - 4, 13, 18), border_radius=3)
            pygame.draw.rect(screen, leg_color, (dr.x + 24, dr.y + 52 + bob + 4, 13, 12), border_radius=3)

    def _draw_attack_arm(self, screen, dr, bob):
        progress = 1 - self.attack_timer / 18
        arm_y = dr.y + 24 + bob - int(math.sin(progress * math.pi) * 10)
        arm_x = dr.x + dr.w - 2 if self.facing == 1 else dr.x - 18
        pygame.draw.rect(screen, self.color, (arm_x, arm_y, 18, 16), border_radius=4)
        if 4 <= self.attack_timer <= 15:
            glow_surf = pygame.Surface((36, 36), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (*self.glow_color, 120), (18, 18), 18)
            screen.blit(glow_surf, (arm_x + 9 - 18, arm_y + 8 - 18))

    def _draw_skill_aura(self, screen, dr, bob):
        r = 52 + int(math.sin(self.bob_t * 3) * 6)
        aura_surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        alpha = int(80 * (self.skill_timer / 28))
        pygame.draw.circle(aura_surf, (*self.glow_color, alpha), (r, r), r)
        screen.blit(aura_surf, (dr.centerx - r, dr.centery - r + bob))

    def _draw_skill_beam(self, screen, dr, bob):
        beam_len = 110
        beam_x = dr.right - 5 if self.facing == 1 else dr.left + 5 - beam_len
        beam_y = dr.centery + bob - 6
        beam_w = int(14 * (self.skill_timer / 28))
        alpha = int(220 * (self.skill_timer / 28))
        beam_surf = pygame.Surface((beam_len, beam_w + 10), pygame.SRCALPHA)
        pygame.draw.rect(beam_surf, (*self.glow_color, alpha), (0, 5, beam_len, beam_w), border_radius=4)
        pygame.draw.rect(beam_surf, (255, 255, 255, alpha // 2), (0, 7, beam_len, max(2, beam_w - 4)), border_radius=4)
        screen.blit(beam_surf, (beam_x, beam_y - 5))

    def _draw_respawn_icon(self, screen, camera):
        # 이름 위에 카운트다운 표시
        text_surf = pygame.font.SysFont("Arial", 16, bold=True).render(
            f"{self.name} ✦ {self.respawn_timer // 10 + 1}", True, self.glow_color
        )
        x = 80 if self.player_id == 1 else screen.get_width() - 160
        screen.blit(text_surf, (x, 60))
