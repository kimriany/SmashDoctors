"""
Nobel — 직스 스타일, 튀기는 폭탄과 공중 폭격으로 공간 제어

일반 스킬:
  Q / ;  Bouncing Bomb    — 튀어나가는 반동 폭탄 (직스 Q)
  E / '  Mega Bomb Drop   — 하늘에서 거대 폭탄 낙하 (직스 R 느낌)

영역 전개 중:
  Q / ;  Cluster Bomb     — 연속 폭탄 3발 연속 발사
  E / '  Carpet Bombing   — 전방 광범위 폭탄 비 (범위 공격)
"""
from entities.player import Player
from systems.skill import ProjectileSkill, SummonZoneSkill, Skill, DomainUltimateSkill
import pygame
import math
import random


class _DomainOnlyMixin:
    def can_activate(self, owner): return getattr(owner, "domain_active", False)

class _NormalOnlyMixin:
    def can_activate(self, owner): return not getattr(owner, "domain_active", False)

def _alpha(v): return max(0, min(255, int(v)))

BOMB_COLORS = [(245, 180, 60), (255, 140, 40), (255, 220, 80), (200, 100, 20)]


# ── Q: Bouncing Bomb (직스 Q — 튀기는 반동 폭탄) ────────────────────────────
class BouncingBomb(_NormalOnlyMixin, ProjectileSkill):
    DISPLAY_NAME = "Bouncing Bomb"
    DESCRIPTION  = "Throw a bomb that bounces on the ground.\nExplodes on 2nd contact."
    PROJ_SPEED   = 11.0
    PROJ_SIZE    = 18
    PROJ_COLOR   = (245, 180, 60)
    PROJ_GLOW    = (255, 230, 130)
    ARTIFACT_PATH = "assets/images/charactor/Nobel/nobel_bomb.png"
    COOLDOWN_SEC = 4.0

    BOUNCE_COUNT = 2    # 최대 바운스 횟수
    EXPLODE_ON   = 2    # 몇 번째 바운스에서 폭발

    def __init__(self):
        super().__init__("Bouncing Bomb", damage=26, cooldown=240, duration=120)
        self.charge_value = 1.0
        self._bounces    = 0
        self._exploding  = False
        self._explode_t  = 0
        self._spin       = 0.0

    def on_start(self, owner, event_bus=None, psys=None):
        self._px       = float(owner.rect.centerx + owner.facing * 28)
        self._py       = float(owner.rect.centery - 14)
        self._vx       = self.PROJ_SPEED * owner.facing
        self._vy       = -6.0   # 위로 던지기
        self._alive    = True
        self._bounces  = 0
        self._exploding = False
        self._explode_t = 0
        self._spin      = 0.0
        if psys:
            psys.spawn(self._px, self._py, (255, 220, 80),
                       count=6, speed=3, gravity=0.1, life=12, r=4, glow=True)

    def on_update(self, owner, event_bus=None, psys=None):
        if not self._alive: return
        if self._exploding:
            self._explode_t += 1
            if self._explode_t > 20: self._alive = False
            return

        self._px  += self._vx
        self._vy  += 0.55   # 중력
        self._py  += self._vy
        self._spin += 8.0

        # 바닥 바운스 (y > 스테이지 바닥 추정 — 대략 owner.rect.bottom 기준)
        ground_y = owner.rect.bottom + 20
        if self._py >= ground_y and self._vy > 0:
            self._vy    *= -0.58   # 반동
            self._vx    *= 0.85
            self._py     = ground_y
            self._bounces += 1

            if psys:
                psys.spawn(self._px, self._py, (255, 160, 40),
                           count=8, speed=3, gravity=0.1, life=12, r=3, glow=True)

            if self._bounces >= self.EXPLODE_ON:
                self._trigger_explosion(owner, event_bus, psys)

        # 화면 밖 제거
        if abs(self._px - owner.rect.centerx) > 900:
            self._alive = False

        # 이동 중 파티클
        if psys and int(self._spin) % 24 < 3:
            psys.spawn(self._px, self._py, (245, 180, 60),
                       count=2, speed=1.5, gravity=0.05, life=10, r=3, glow=True)

    def _trigger_explosion(self, owner, event_bus, psys):
        self._exploding = True
        self.has_hit    = False   # 폭발 시 재판정
        if psys:
            for col in BOMB_COLORS:
                psys.spawn(self._px, self._py, col,
                           count=14, speed=8, gravity=0.05, life=24, r=6, glow=True)
            psys.spawn(self._px, self._py, (255, 255, 255),
                       count=8, speed=5, gravity=0, life=14, r=4, glow=True)

    def get_hitbox(self, owner):
        if not self._alive: return None
        if self._exploding:
            r = self.PROJ_SIZE * 3
            return pygame.Rect(int(self._px)-r, int(self._py)-r, r*2, r*2)
        r = self.PROJ_SIZE
        return pygame.Rect(int(self._px)-r, int(self._py)-r, r*2, r*2)

    def on_hit(self, owner, target, event_bus, psys=None, fsys=None):
        if self._exploding:
            target.vel.x += owner.facing * 8
            target.vel.y -= 6
        super().on_hit(owner, target, event_bus, psys, fsys)

    def draw_front(self, owner, screen, camera, dr, bob, z):
        if not self._alive: return
        sx, sy = camera.world_to_screen(self._px, self._py)
        r = max(4, int(self.PROJ_SIZE * z))

        if self._exploding:
            # 폭발 이펙트
            t     = self._explode_t / 20
            exp_r = int(r * (1 + t * 4))
            for col, dr2, aa in [(BOMB_COLORS[0], exp_r, 180),
                                  (BOMB_COLORS[2], int(exp_r*0.65), 220),
                                  ((255,255,255),  int(exp_r*0.3),  255)]:
                es = pygame.Surface((dr2*2+4, dr2*2+4), pygame.SRCALPHA)
                pygame.draw.circle(es, (*col, _alpha(aa*(1-t))), (dr2+2, dr2+2), dr2)
                screen.blit(es, (sx-dr2-2, sy-dr2-2))
        else:
            # 회전하는 폭탄
            ang = math.radians(self._spin)
            bs  = pygame.Surface((r*4, r*4), pygame.SRCALPHA)
            bc  = r*2
            pygame.draw.circle(bs, (*self.PROJ_GLOW, 100), (bc, bc), r+4)
            pygame.draw.circle(bs, self.PROJ_COLOR,         (bc, bc), r)
            pygame.draw.circle(bs, (30, 20, 10),            (bc, bc), r, max(1, int(2*z)))
            # 도화선
            fx = bc + int(math.cos(ang) * r)
            fy = bc + int(math.sin(ang) * r)
            pygame.draw.line(bs, (200, 150, 50), (bc, bc), (fx, fy), max(1, int(2*z)))
            pygame.draw.circle(bs, (255, 220, 60), (fx, fy), max(2, int(3*z)))
            screen.blit(bs, (sx-r*2, sy-r*2))


# ── E: Mega Bomb Drop (직스 R 느낌 — 하늘에서 거대 폭탄 낙하) ──────────────
class MegaBombDrop(_NormalOnlyMixin, SummonZoneSkill):
    DISPLAY_NAME = "Mega Bomb Drop"
    DESCRIPTION  = "Drop a massive bomb from above.\nLarge warning, massive explosion."
    WARN_FRAMES  = 50
    ZONE_W       = 160
    ZONE_H       = 160
    ZONE_COLOR   = (245, 130, 40)
    ZONE_GLOW    = (255, 220, 80)
    COOLDOWN_SEC = 9.0

    def __init__(self):
        super().__init__("Mega Bomb Drop", damage=38, cooldown=540, duration=120)
        self.charge_value = 1.4
        self._bomb_y      = 0.0
        self._landed      = False

    def on_start(self, owner, event_bus=None, psys=None):
        target = getattr(owner, "_skill_target", None)
        if target and not target.dead:
            self._zone_x = target.rect.centerx
            self._zone_y = target.rect.bottom
        else:
            self._zone_x = owner.rect.centerx + owner.facing * 220
            self._zone_y = owner.rect.bottom
        self._bomb_y  = self._zone_y - 500   # 위에서 낙하
        self._landed  = False
        self.has_hit  = False

    def on_update(self, owner, event_bus=None, psys=None):
        elapsed = self.duration - self.timer
        if not self._landed:
            # 경고 중 폭탄이 천천히 내려옴
            drop_t = min(1.0, elapsed / self.WARN_FRAMES)
            self._bomb_y = (self._zone_y - 500) + 500 * drop_t
            if drop_t >= 1.0:
                self._landed = True
                if psys:
                    for col in BOMB_COLORS:
                        psys.spawn(self._zone_x, self._zone_y, col,
                                   count=20, speed=10, gravity=0.05, life=30, r=8, glow=True)
                    psys.spawn(self._zone_x, self._zone_y, (255,255,255),
                               count=12, speed=7, gravity=0, life=18, r=5, glow=True)
        # 착지 후 충격파 파티클
        if self._landed and psys and self.timer % 5 == 0:
            ang = random.uniform(0, math.pi * 2)
            r   = random.uniform(40, self.ZONE_W * 0.5)
            psys.spawn(self._zone_x + math.cos(ang)*r, self._zone_y + math.sin(ang)*r,
                       random.choice(BOMB_COLORS), count=1, speed=2,
                       gravity=-0.02, life=14, r=4, glow=True)

    def get_hitbox(self, owner):
        if not self.active or not self._landed: return None
        r = self.ZONE_W // 2
        return pygame.Rect(int(self._zone_x)-r, int(self._zone_y)-r, r*2, r*2)

    def on_hit(self, owner, target, event_bus, psys=None, fsys=None):
        # 중심에서 멀수록 약한 넉백
        dx = target.rect.centerx - self._zone_x
        dy = target.rect.centery - self._zone_y
        dist = max(1, math.sqrt(dx*dx + dy*dy))
        scale = 1 - min(0.5, dist / (self.ZONE_W * 0.5))
        target.vel.x += (dx/dist) * 10 * scale
        target.vel.y += (dy/dist) * 8 * scale - 4
        super().on_hit(owner, target, event_bus, psys, fsys)

    def draw_behind(self, owner, screen, camera, dr, bob, z):
        if not self.active: return
        zx = int(self._zone_x); zy = int(self._zone_y)
        sx, sy  = camera.world_to_screen(zx, zy)
        bsx, bsy = camera.world_to_screen(zx, int(self._bomb_y))
        elapsed  = self.duration - self.timer
        warn     = elapsed < self.WARN_FRAMES

        # 경고 원
        r   = int(self.ZONE_W * 0.5 * z)
        a   = _alpha(80 + 100 * abs(math.sin(elapsed * 0.2))) if warn else _alpha(160 * (self.timer / self.duration))
        ws  = pygame.Surface((r*2+8, r*2+8), pygame.SRCALPHA)
        pygame.draw.circle(ws, (*self.ZONE_COLOR, a//3), (r+4, r+4), r)
        pygame.draw.circle(ws, (*self.ZONE_GLOW, a),     (r+4, r+4), r, max(2, int(3*z)))
        screen.blit(ws, (sx-r-4, sy-r-4))

        # 낙하 중인 폭탄
        if not self._landed:
            br = max(6, int(28 * z))
            bs = pygame.Surface((br*4, br*4), pygame.SRCALPHA)
            bc = br*2
            pygame.draw.circle(bs, (*self.PROJ_GLOW, 120) if hasattr(self,'PROJ_GLOW') else (255,230,100,120), (bc,bc), br+6)
            pygame.draw.circle(bs, self.ZONE_COLOR, (bc,bc), br)
            pygame.draw.circle(bs, (30,20,10), (bc,bc), br, max(2,int(3*z)))
            # 충격파 원 (경고)
            ws2 = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
            pygame.draw.line(screen, (*self.ZONE_GLOW, a//2), (bsx, bsy), (sx, sy), max(1,int(2*z)))
            screen.blit(bs, (bsx-bc, bsy-bc))


# ── 영역 궁 ──────────────────────────────────────────────────────────────────
class NobelDomain(DomainUltimateSkill):
    DISPLAY_NAME          = "Nobel Domain"
    DESCRIPTION           = "Open Nobel's explosive domain.\nBomb skills become stronger."
    DOMAIN_BG_PATH        = "assets/images/charactor/Nobel/nobel_domain.png"
    DOMAIN_PARTICLE_COLOR = (245, 180, 60)
    BREAK_HITS            = 5
    CUTSCENE_FRAMES       = 30
    CUTSCENE_ZOOM         = 1.45
    TRANSITION_SPEED      = 0.055
    FREEZE_DURING_TRANSITION = True
    def __init__(self):
        super().__init__(name="Nobel Domain", damage=0, duration=999999)


# ── 강화 Q: Cluster Bomb (3연속 폭탄) ────────────────────────────────────────
class ClusterBomb(_DomainOnlyMixin, BouncingBomb):
    DISPLAY_NAME = "Cluster Bomb"
    DESCRIPTION  = "Domain — Fire 3 bouncing bombs in rapid succession."
    COOLDOWN_SEC = 5.0
    BOUNCE_COUNT = 1
    EXPLODE_ON   = 1   # 첫 바운스에서 폭발

    def __init__(self):
        ProjectileSkill.__init__(self, "Cluster Bomb", damage=32, cooldown=300, duration=140)
        self.charge_value          = 0.0
        self.finisher_charge_value = 1.6
        self._bounces   = 0
        self._exploding = False
        self._explode_t = 0
        self._spin      = 0.0
        self._shot_count = 0
        self._shot_timer = 0
        self._bombs = []   # 다중 폭탄 추적

    def on_start(self, owner, event_bus=None, psys=None):
        self._bombs      = []
        self._shot_count = 0
        self._shot_timer = 0
        self._alive      = True
        # 첫 발 즉시
        self._fire_bomb(owner, 0)

    def _fire_bomb(self, owner, spread):
        self._bombs.append({
            "px": float(owner.rect.centerx + owner.facing * 28),
            "py": float(owner.rect.centery - 14),
            "vx": 11.0 * owner.facing,
            "vy": -6.0 - spread * 1.5,
            "bounces": 0,
            "exploding": False,
            "explode_t": 0,
            "spin": 0.0,
            "alive": True,
        })

    def on_update(self, owner, event_bus=None, psys=None):
        # 0.2초 간격으로 3발
        self._shot_timer += 1
        if self._shot_count < 2 and self._shot_timer >= 12:
            self._shot_timer  = 0
            self._shot_count += 1
            self._fire_bomb(owner, self._shot_count)

        ground_y = owner.rect.bottom + 20
        for b in self._bombs:
            if not b["alive"]: continue
            if b["exploding"]:
                b["explode_t"] += 1
                if b["explode_t"] > 20: b["alive"] = False
                continue
            b["px"] += b["vx"]; b["vy"] += 0.55; b["py"] += b["vy"]; b["spin"] += 8
            if b["py"] >= ground_y and b["vy"] > 0:
                b["vy"] *= -0.55; b["vx"] *= 0.8; b["py"] = ground_y; b["bounces"] += 1
                if psys:
                    psys.spawn(b["px"], b["py"], (255,160,40), count=6, speed=3, gravity=0.1, life=10, r=3, glow=True)
                if b["bounces"] >= self.EXPLODE_ON:
                    b["exploding"] = True
                    self.has_hit = False
                    if psys:
                        for col in BOMB_COLORS:
                            psys.spawn(b["px"],b["py"],col,count=12,speed=8,gravity=0.05,life=22,r=6,glow=True)

    def get_hitbox(self, owner):
        # 폭발 중인 폭탄들의 히트박스 반환 (첫 번째)
        for b in self._bombs:
            if b["alive"] and b["exploding"]:
                r = self.PROJ_SIZE * 3
                return pygame.Rect(int(b["px"])-r, int(b["py"])-r, r*2, r*2)
        for b in self._bombs:
            if b["alive"] and not b["exploding"]:
                r = self.PROJ_SIZE
                return pygame.Rect(int(b["px"])-r, int(b["py"])-r, r*2, r*2)
        return None

    def draw_front(self, owner, screen, camera, dr, bob, z):
        for b in self._bombs:
            if not b["alive"]: continue
            sx, sy = camera.world_to_screen(b["px"], b["py"])
            r = max(4, int(self.PROJ_SIZE * z))
            if b["exploding"]:
                t     = b["explode_t"] / 20
                exp_r = int(r * (1 + t * 3.5))
                for col, rr, aa in [(BOMB_COLORS[0], exp_r, 180),
                                     (BOMB_COLORS[2], int(exp_r*0.6), 220),
                                     ((255,255,255), int(exp_r*0.3), 255)]:
                    es = pygame.Surface((rr*2+4, rr*2+4), pygame.SRCALPHA)
                    pygame.draw.circle(es, (*col, _alpha(aa*(1-t))), (rr+2,rr+2), rr)
                    screen.blit(es, (sx-rr-2, sy-rr-2))
            else:
                ang = math.radians(b["spin"])
                bs  = pygame.Surface((r*4, r*4), pygame.SRCALPHA)
                bc  = r*2
                pygame.draw.circle(bs, (255,230,130,100), (bc,bc), r+4)
                pygame.draw.circle(bs, (245,180,60), (bc,bc), r)
                pygame.draw.circle(bs, (30,20,10), (bc,bc), r, max(1,int(2*z)))
                fx = bc + int(math.cos(ang)*r); fy = bc + int(math.sin(ang)*r)
                pygame.draw.line(bs, (200,150,50), (bc,bc), (fx,fy), max(1,int(2*z)))
                pygame.draw.circle(bs, (255,220,60), (fx,fy), max(2,int(3*z)))
                screen.blit(bs, (sx-r*2, sy-r*2))


# ── 강화 E: Carpet Bombing (폭탄 비 — 전방 광범위) ──────────────────────────
class CarpetBombing(_DomainOnlyMixin, SummonZoneSkill):
    DISPLAY_NAME = "Carpet Bombing"
    DESCRIPTION  = "Domain — Rain bombs across a wide area.\nMultiple explosions."
    WARN_FRAMES  = 20
    ZONE_W       = 500
    ZONE_H       = 300
    ZONE_COLOR   = (245, 130, 40)
    ZONE_GLOW    = (255, 220, 80)
    COOLDOWN_SEC = 12.0

    BOMB_COUNT  = 8
    BOMB_INTERVAL = 10   # 프레임 간격

    def __init__(self):
        super().__init__("Carpet Bombing", damage=30, cooldown=720, duration=140)
        self.charge_value          = 0.0
        self.finisher_charge_value = 2.2
        self._bombs = []
        self._drop_timer = 0
        self._drop_count = 0

    def on_start(self, owner, event_bus=None, psys=None):
        self._zone_x = owner.rect.centerx + owner.facing * 260
        self._zone_y = owner.rect.bottom
        self._bombs  = []
        self._drop_timer = 0
        self._drop_count = 0
        self.has_hit = False
        if psys:
            for _ in range(12):
                psys.spawn(self._zone_x + random.uniform(-200,200),
                           self._zone_y - 30,
                           random.choice(BOMB_COLORS), count=1, speed=3,
                           gravity=-0.03, life=20, r=5, glow=True)

    def on_update(self, owner, event_bus=None, psys=None):
        # 새 폭탄 투하
        elapsed = self.duration - self.timer
        if elapsed > self.WARN_FRAMES and self._drop_count < self.BOMB_COUNT:
            self._drop_timer += 1
            if self._drop_timer >= self.BOMB_INTERVAL:
                self._drop_timer = 0
                self._drop_count += 1
                bx = self._zone_x + random.uniform(-self.ZONE_W*0.4, self.ZONE_W*0.4)
                self._bombs.append({
                    "px": bx, "py": self._zone_y - 400,
                    "alive": True, "exploding": False, "explode_t": 0
                })
                if psys:
                    psys.spawn(bx, self._zone_y - 400, (255,180,40),
                               count=4, speed=2, gravity=0.1, life=12, r=4, glow=True)

        # 폭탄 낙하 업데이트
        for b in self._bombs:
            if not b["alive"]: continue
            if b["exploding"]:
                b["explode_t"] += 1
                if b["explode_t"] > 18: b["alive"] = False
                continue
            b["py"] += 18   # 빠른 낙하
            if b["py"] >= self._zone_y:
                b["py"]       = self._zone_y
                b["exploding"] = True
                self.has_hit  = False
                if psys:
                    for col in BOMB_COLORS:
                        psys.spawn(b["px"], b["py"], col,
                                   count=10, speed=7, gravity=0.05, life=20, r=6, glow=True)

    def get_hitbox(self, owner):
        # 폭발 중인 폭탄 히트박스
        for b in self._bombs:
            if b["alive"] and b["exploding"]:
                r = 80
                return pygame.Rect(int(b["px"])-r, int(b["py"])-r, r*2, r*2)
        return None

    def draw_behind(self, owner, screen, camera, dr, bob, z):
        if not self.active: return
        for b in self._bombs:
            if not b["alive"]: continue
            sx, sy = camera.world_to_screen(int(b["px"]), int(b["py"]))
            r = max(5, int(22 * z))
            if b["exploding"]:
                t = b["explode_t"] / 18
                for col, rr, aa in [(BOMB_COLORS[0], int(r*(1+t*3)), 160),
                                     (BOMB_COLORS[2], int(r*(1+t*2)), 200),
                                     ((255,255,200), int(r*(1+t)), 240)]:
                    es = pygame.Surface((rr*2+4, rr*2+4), pygame.SRCALPHA)
                    pygame.draw.circle(es, (*col, _alpha(aa*(1-t))), (rr+2,rr+2), rr)
                    screen.blit(es, (sx-rr-2, sy-rr-2))
            else:
                bs = pygame.Surface((r*4, r*4), pygame.SRCALPHA)
                bc = r*2
                pygame.draw.circle(bs, (255,230,100,100), (bc,bc), r+4)
                pygame.draw.circle(bs, (245,160,40), (bc,bc), r)
                pygame.draw.circle(bs, (30,20,10), (bc,bc), r, max(1,int(2*z)))
                screen.blit(bs, (sx-bc, sy-bc))


# ── 캐릭터 ───────────────────────────────────────────────────────────────────
class Nobel(Player):
    WEIGHT     = 95;  KB_GROWTH = 82;  BASE_KB   = 30
    WALK_SPEED = 6.2; JUMP_POWER = -15.5; MAX_JUMPS = 2
    ATTACK_DMG = 12;  ATK_FRAMES = 20;   ATK_CD    = 32
    HIT_START  = 4;   HIT_END    = 16

    BODY_COLOR    = (55, 200, 90);  TRIM_COLOR  = (20, 120, 50)
    GLOW_COLOR    = (130, 255, 160); DARK_COLOR = (15, 80, 35)
    DISPLAY_NAME  = "Nobel"
    DESCRIPTION   = "Explosive zoner inspired by Ziggs.\nBounce bombs, rain explosions."
    PREVIEW_COLOR = (55, 200, 90)

    SPRITE_PATH   = "assets/images/charactor/Nobel/IDL.png"
    SPRITE_IDLE   = "assets/images/charactor/Nobel/IDL.png"
    SPRITE_JUMP   = "assets/images/charactor/Nobel/jump.png"
    SPRITE_ATTACK = "assets/images/charactor/Nobel/attack.png"
    SPRITE_SKILL  = "assets/images/charactor/Nobel/skill.png"
    SPRITE_SCALE  = 1.25; SPRITE_OFFSET_X = 0; SPRITE_OFFSET_Y = 6

    def __init__(self, x, y, name="Player", player_id=1):
        super().__init__(x, y, name, player_id)
        self.color = self.BODY_COLOR; self.trim_color = self.TRIM_COLOR
        self.glow_color = self.GLOW_COLOR; self.dark_color = self.DARK_COLOR
        self.max_jumps = self.MAX_JUMPS; self.attack_damage = self.ATTACK_DMG

    def _init_skills(self):
        self.skills["skill_Q"]        = BouncingBomb()
        self.skills["skill_E"]        = MegaBombDrop()
        self.skills["skill_R"]        = NobelDomain()
        self.skills["skill_Q_domain"] = ClusterBomb()
        self.skills["skill_E_domain"] = CarpetBombing()

    def get_char_name(self): return "Nobel"
