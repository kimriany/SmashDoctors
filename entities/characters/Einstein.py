"""
Einstein — 중력과 시공간을 지배하는 과학자

일반 스킬:
  Q / ;  Gravity Lash     — 중력 채찍 전방 투사, 명중 시 끌어당김
  E / '  Event Horizon    — 블랙홀 소환, 다단 흡수 후 방출

영역 전개 중:
  Q / ;  Spacetime Rend   — 시공간 균열 광선, 관통 + 중력 왜곡
  E / '  Singularity      — 대형 특이점, 전장 전체 중력 붕괴
"""
from entities.player import Player
from systems.skill import Skill, BeamSkill, SummonZoneSkill, DomainUltimateSkill
import pygame
import math
import random


class _DomainOnlyMixin:
    def can_activate(self, owner): return getattr(owner, "domain_active", False)

class _NormalOnlyMixin:
    def can_activate(self, owner): return not getattr(owner, "domain_active", False)

def _alpha(v): return max(0, min(255, int(v)))

GRAVITY_COLORS = [(255, 120, 80), (255, 180, 100), (200, 80, 60), (255, 220, 150)]
LIGHT_COLORS = [(255, 240, 150), (255, 255, 220), (120, 190, 255), (255, 210, 90)]


# ── Q: Gravity Lash (중력 채찍 — 투사체 명중 시 끌어당김) ───────────────────
class GravityLash(_NormalOnlyMixin, Skill):
    DISPLAY_NAME = "Gravity Lash"
    DESCRIPTION  = "Fire a gravity hook forward.\nHit enemy is pulled toward you."
    COOLDOWN_SEC = 5.5

    LASH_SPEED   = 18
    LASH_LENGTH  = 320
    PULL_SPEED   = 12

    def __init__(self):
        super().__init__("Gravity Lash", damage=20,
                         cooldown=330, duration=60)
        self.charge_value = 1.1
        self._lx = 0.0; self._ly = 0.0
        self._lax = 0.0; self._lay = 0.0   # 현재 라인 끝 위치
        self._hit  = False
        self._pulling = False
        self._pull_target = None
        self._traveled = 0.0

    def on_start(self, owner, event_bus=None, psys=None):
        self._lx = float(owner.rect.centerx)
        self._ly = float(owner.rect.centery)
        self._lax = self._lx
        self._lay = self._ly
        self._hit     = False
        self._pulling = False
        self._traveled = 0.0

    def get_hitbox(self, owner):
        if not self.active or self._hit: return None
        r = 10
        return pygame.Rect(int(self._lax)-r, int(self._lay)-r, r*2, r*2)

    def on_update(self, owner, event_bus=None, psys=None):
        if not self.active: return
        if self._pulling and self._pull_target:
            t = self._pull_target
            if not t.dead:
                dx = owner.rect.centerx - t.rect.centerx
                dy = owner.rect.centery - t.rect.centery
                dist = max(1, math.sqrt(dx*dx + dy*dy))
                t.vel.x += (dx/dist) * self.PULL_SPEED * 0.15
                t.vel.y += (dy/dist) * self.PULL_SPEED * 0.15
            if psys and self.timer % 3 == 0:
                if self._pull_target and not self._pull_target.dead:
                    mx = (owner.rect.centerx + self._pull_target.rect.centerx) // 2
                    my = (owner.rect.centery + self._pull_target.rect.centery) // 2
                    psys.spawn(mx, my, (255,140,80), count=2, speed=2,
                               gravity=-0.05, life=10, r=3, glow=True)
            return

        if not self._hit:
            self._lax += self.LASH_SPEED * owner.facing
            self._traveled += self.LASH_SPEED
            if psys and int(self._traveled) % 20 < 3:
                psys.spawn(self._lax, self._lay, (255,140,80),
                           count=2, speed=1.5, gravity=0.05, life=8, r=3, glow=True)
            if self._traveled >= self.LASH_LENGTH:
                self._hit = True

    def on_hit(self, owner, target, event_bus, psys=None, fsys=None):
        self._hit         = True
        self._pulling     = True
        self._pull_target = target
        if psys:
            psys.spawn(target.rect.centerx, target.rect.centery,
                       (255,120,60), count=16, speed=6, gravity=0.1, life=18, r=5, glow=True)
        super().on_hit(owner, target, event_bus, psys, fsys)

    def draw_front(self, owner, screen, camera, dr, bob, z):
        if not self.active: return
        ox  = float(owner.rect.centerx); oy = float(owner.rect.centery)
        t_ratio = self.timer / max(1, self.duration)
        alpha   = _alpha(220 * t_ratio)

        if self._pulling and self._pull_target and not self._pull_target.dead:
            ex = float(self._pull_target.rect.centerx)
            ey = float(self._pull_target.rect.centery)
        else:
            ex = self._lax; ey = self._lay

        sox, soy = camera.world_to_screen(ox, oy)
        sex, sey = camera.world_to_screen(ex, ey)

        # 중력 채찍 라인
        segments = 8
        for i in range(segments):
            t1, t2 = i/segments, (i+1)/segments
            x1 = int(sox + (sex-sox)*t1)
            y1 = int(soy + (sey-soy)*t1 + math.sin(t1*math.pi) * 12 * z)
            x2 = int(sox + (sex-sox)*t2)
            y2 = int(soy + (sey-soy)*t2 + math.sin(t2*math.pi) * 12 * z)
            col_ratio = i / segments
            col = (int(255*(1-col_ratio*0.3)), int(120+80*col_ratio), 60)
            pygame.draw.line(screen, (*col, alpha), (x1,y1), (x2,y2), max(2, int(4*z)))

        # 끝 고리
        r = max(4, int(10*z))
        es = pygame.Surface((r*4, r*4), pygame.SRCALPHA)
        pygame.draw.circle(es, (255,160,80,alpha), (r*2,r*2), r)
        pygame.draw.circle(es, (255,220,150,alpha//2), (r*2,r*2), r+4, max(1,int(2*z)))
        screen.blit(es, (sex-r*2, sey-r*2))


# ── E: Event Horizon (블랙홀 — 다단 흡수 후 방출) ───────────────────────────
class EventHorizon(_NormalOnlyMixin, SummonZoneSkill):
    DISPLAY_NAME = "Event Horizon"
    DESCRIPTION  = "Summon a black hole. Pulls enemy in,\nthen violently releases."
    WARN_FRAMES  = 0
    ZONE_W       = 180
    ZONE_H       = 180
    ZONE_COLOR   = (220, 60, 40)
    ZONE_GLOW    = (255, 160, 100)
    COOLDOWN_SEC = 8.0

    PULL_FORCE   = 5.2
    EXPLODE_FRAME = 80

    def __init__(self):
        super().__init__("Event Horizon", damage=32, cooldown=480, duration=130)
        self.charge_value = 1.3
        self._phase       = 0.0
        self._exploded    = False
        self._explode_rings = []

    def on_start(self, owner, event_bus=None, psys=None):
        target = getattr(owner, "_skill_target", None)
        if target and not target.dead and abs(target.rect.centerx - owner.rect.centerx) < 380:
            self._zone_x = target.rect.centerx - owner.facing * 82
            self._zone_y = target.rect.centery - 34
        else:
            self._zone_x = owner.rect.centerx + owner.facing * 200
            self._zone_y = owner.rect.centery
        self._phase     = random.uniform(0, math.pi * 2)
        self._exploded  = False
        self._explode_rings = []
        self.has_hit    = False
        if psys:
            for _ in range(20):
                ang = random.uniform(0, math.pi*2)
                psys.spawn(self._zone_x + math.cos(ang)*60,
                           self._zone_y + math.sin(ang)*60,
                           random.choice(GRAVITY_COLORS),
                           count=1, speed=3, gravity=-0.03, life=20, r=4, glow=True)

    def on_update(self, owner, event_bus=None, psys=None):
        elapsed = self.duration - self.timer
        for ring in self._explode_rings:
            ring["r"]    += ring["speed"]
            ring["alpha"] = max(0, ring["alpha"] - ring["decay"])
        self._explode_rings = [r for r in self._explode_rings if r["alpha"] > 0]
        if self._exploded: return

        target = getattr(owner, "_skill_target", None)
        zone   = self._zone_rect()
        if target and not target.dead:
            dx = self._zone_x - target.rect.centerx
            dy = self._zone_y - target.rect.centery
            dist = max(1, math.sqrt(dx*dx + dy*dy))
            if dist <= 2:
                dx = -owner.facing
                dy = -0.35
                dist = math.sqrt(dx*dx + dy*dy)
            max_pull_dist = self.ZONE_W * 1.55
            if dist <= max_pull_dist:
                proximity = 1.0 - min(1.0, dist / max_pull_dist)
                falloff = 0.25 + proximity * proximity * 1.85
                pull = self.PULL_FORCE * (1 + elapsed / self.EXPLODE_FRAME) * falloff
                target.vel.x += (dx/dist) * pull * 0.42
                target.vel.y += (dy/dist) * pull * 0.34

        if psys and self.timer % 4 == 0:
            ang = random.uniform(0, math.pi*2)
            r   = random.uniform(self.ZONE_W*0.2, self.ZONE_W*0.45)
            psys.spawn(self._zone_x + math.cos(ang)*r,
                       self._zone_y + math.sin(ang)*r,
                       random.choice(GRAVITY_COLORS),
                       count=1, speed=0.5, gravity=0, life=14, r=3, glow=True)

        if elapsed >= self.EXPLODE_FRAME and not self._exploded:
            self._exploded = True
            self.has_hit   = False
            for i in range(6):
                self._explode_rings.append({
                    "r": 8+i*12, "speed": 9+i*3,
                    "alpha": 255-i*30, "decay": 7+i*2,
                    "color": GRAVITY_COLORS[i%len(GRAVITY_COLORS)]
                })
            if target and not target.dead:
                dx  = target.rect.centerx - self._zone_x
                dy  = target.rect.centery - self._zone_y
                dist = max(1, math.sqrt(dx*dx+dy*dy))
                kb  = 22 + target.damage_pct * 0.07
                target.vel.x = (dx/dist) * kb
                target.vel.y = (dy/dist) * kb - 7
            if psys:
                for col in GRAVITY_COLORS:
                    psys.spawn(self._zone_x, self._zone_y, col,
                               count=22, speed=10, gravity=-0.04, life=32, r=7, glow=True)
                psys.spawn(self._zone_x, self._zone_y, (255,255,255),
                           count=14, speed=7, gravity=-0.06, life=22, r=5, glow=True)

    def _zone_rect(self):
        return pygame.Rect(int(self._zone_x) - self.ZONE_W // 2,
                           int(self._zone_y) - self.ZONE_H // 2,
                           self.ZONE_W, self.ZONE_H)

    def get_hitbox(self, owner):
        if not self.active or not self._exploded:
            return None
        return self._zone_rect()

    def on_hit(self, owner, target, event_bus, psys=None, fsys=None):
        dx = target.rect.centerx - self._zone_x
        dy = target.rect.centery - self._zone_y
        dist = max(1, math.sqrt(dx*dx + dy*dy))
        target.vel.x = (dx / dist) * 22
        target.vel.y = (dy / dist) * 14 - 8
        super().on_hit(owner, target, event_bus, psys, fsys)

    def draw_behind(self, owner, screen, camera, dr, bob, z):
        if not self.active: return
        sx, sy = camera.world_to_screen(int(self._zone_x), int(self._zone_y))
        tick   = pygame.time.get_ticks()
        elapsed = self.duration - self.timer
        t       = min(1.0, elapsed / max(1, self.EXPLODE_FRAME))

        for ring in self._explode_rings:
            r_px = int(ring["r"]*z)
            if r_px < 2: continue
            rs = pygame.Surface((r_px*2+6, r_px*2+6), pygame.SRCALPHA)
            pygame.draw.circle(rs, (*ring["color"], _alpha(ring["alpha"])),
                               (r_px+3, r_px+3), r_px, max(1,int(4*z)))
            screen.blit(rs, (sx-r_px-3, sy-r_px-3))
        if self._exploded: return

        base_r = int(self.ZONE_W * 0.5 * z)
        alpha  = _alpha(max(30, 100 * (1-t*0.3)))

        # 어둠 중심
        cs = pygame.Surface((base_r*2+8, base_r*2+8), pygame.SRCALPHA)
        pygame.draw.circle(cs, (8, 2, 20, _alpha(alpha*1.2)), (base_r+4,base_r+4), base_r)
        screen.blit(cs, (sx-base_r-4, sy-base_r-4))

        # 강착 원반 효과 (소용돌이 링)
        for i in range(5):
            r_val = int(base_r * (0.25 + i*0.16))
            rot   = tick * (0.015 - i*0.002) * (-1 if i%2 else 1)
            rs    = pygame.Surface((r_val*2+8, r_val*2+8), pygame.SRCALPHA)
            for seg in range(6):
                start = rot + seg * math.pi / 3
                end   = start + math.pi / 4
                pts   = [(r_val+4 + int(r_val*math.cos(start+k*(end-start)/8)),
                          r_val+4 + int(r_val*math.sin(start+k*(end-start)/8)))
                         for k in range(9)]
                if len(pts)>1:
                    pygame.draw.lines(rs, (*GRAVITY_COLORS[i%len(GRAVITY_COLORS)],
                                           _alpha(alpha - i*12)), False, pts, max(1,int(2*z)))
            screen.blit(rs, (sx-r_val-4, sy-r_val-4))

        # 중심 글로우
        gc = pygame.Surface((base_r, base_r), pygame.SRCALPHA)
        pygame.draw.circle(gc, (255,120,60,_alpha(alpha*0.4)), (base_r//2,base_r//2), base_r//2)
        screen.blit(gc, (sx-base_r//2, sy-base_r//2))


# ── 영역 궁 ──────────────────────────────────────────────────────────────────
class EinsteinDomain(DomainUltimateSkill):
    DISPLAY_NAME          = "Einstein Domain"
    DESCRIPTION           = "Open Einstein's spacetime domain.\nAll skills become stronger."
    DOMAIN_BG_PATH        = "assets/images/Einstein_domain.jpeg"  # 임시 — domain.jpeg 추가 시 교체
    DOMAIN_PARTICLE_COLOR = (255, 140, 80)
    BREAK_HITS            = 5
    CUTSCENE_FRAMES       = 30
    CUTSCENE_ZOOM         = 1.5
    TRANSITION_SPEED      = 0.05
    FREEZE_DURING_TRANSITION = True
    def __init__(self):
        super().__init__(name="Einstein Domain", damage=0, duration=999999)


# ── 강화 Q: Spacetime Rend (시공간 균열 광선) ─────────────────────────────────
class SpacetimeRend(_DomainOnlyMixin, BeamSkill):
    DISPLAY_NAME = "Spacetime Rend"
    DESCRIPTION  = "Domain — Tear spacetime with a gravity beam.\nPulls and launches."
    BEAM_LENGTH  = 420
    BEAM_WIDTH   = 38
    BEAM_COLOR   = (255, 100, 60)
    BEAM_GLOW    = (255, 200, 150)
    COOLDOWN_SEC = 6.0

    def __init__(self):
        super().__init__("Spacetime Rend", damage=44, cooldown=360, duration=30)
        self.charge_value          = 0.0
        self.finisher_charge_value = 2.0

    def on_hit(self, owner, target, event_bus, psys=None, fsys=None):
        # 빔 방향 반대로 강하게 끌어당긴 후 방출
        target.vel.x  = -owner.facing * 16
        target.vel.y -= 5
        super().on_hit(owner, target, event_bus, psys, fsys)

    def draw_front(self, owner, screen, camera, dr, bob, z):
        if not self.active: return
        t     = self.timer / max(1, self.duration)
        alpha = _alpha(220 * t)
        length = int(self.BEAM_LENGTH * z)
        bw    = max(int(6*z), int(self.BEAM_WIDTH * t * z))
        sx    = dr.right - int(6*z) if owner.facing == 1 else dr.left - length + int(6*z)
        by    = dr.centery + bob - bw//2

        # 시공간 균열 효과
        tick = pygame.time.get_ticks()
        for i in range(5):
            offset_y = int(math.sin(tick*0.02 + i*1.2) * 8 * z)
            sf = pygame.Surface((length, bw+20), pygame.SRCALPHA)
            a2 = _alpha(alpha - i*30)
            pygame.draw.rect(sf, (*self.BEAM_COLOR, a2//3),
                             (0, bw//2-i*3+10, length, bw+i*6), border_radius=int(5*z))
            screen.blit(sf, (sx, by - offset_y - 10))

        # 메인 빔
        bs = pygame.Surface((length, bw+20), pygame.SRCALPHA)
        pygame.draw.rect(bs, (*self.BEAM_COLOR, alpha),
                         (0, 10, length, bw), border_radius=int(5*z))
        pygame.draw.rect(bs, (*self.BEAM_GLOW, _alpha(alpha*0.5)),
                         (0, 4, length, bw+12), border_radius=int(7*z))
        pygame.draw.rect(bs, (255,255,255, _alpha(alpha*0.7)),
                         (0, 10+bw//2-int(2*z), length, int(4*z)))
        screen.blit(bs, (sx, by))

        # 중력 왜곡 이펙트 (빔 위아래에 물결)
        for yi in range(-3, 4):
            wave_x = int(sx + tick * 0.3 % length)
            wave_y = by + bw//2 + yi * int(6*z)
            ws = pygame.Surface((8, 8), pygame.SRCALPHA)
            pygame.draw.circle(ws, (255,180,100, _alpha(alpha*0.3)), (4,4), 4)
            screen.blit(ws, (wave_x, wave_y))


# ── 강화 E: Singularity (전장 중력 붕괴) ─────────────────────────────────────
class Singularity(_DomainOnlyMixin, SummonZoneSkill):
    DISPLAY_NAME = "Singularity"
    DESCRIPTION  = "Domain — Collapse the whole stage's gravity.\nMassive area pull and explosion."
    WARN_FRAMES  = 30
    ZONE_W       = 600
    ZONE_H       = 600
    ZONE_COLOR   = (180, 40, 20)
    ZONE_GLOW    = (255, 120, 80)
    COOLDOWN_SEC = 14.0

    PULL_FORCE    = 4.5
    EXPLODE_FRAME = 100

    def __init__(self):
        super().__init__("Singularity", damage=50, cooldown=840, duration=160)
        self.charge_value          = 0.0
        self.finisher_charge_value = 3.0
        self._phase       = 0.0
        self._exploded    = False
        self._explode_rings = []
        self._warp_offset = 0.0

    def on_start(self, owner, event_bus=None, psys=None):
        self._zone_x = owner.rect.centerx
        self._zone_y = owner.rect.centery
        self._phase       = random.uniform(0, math.pi*2)
        self._exploded    = False
        self._explode_rings = []
        self._warp_offset = 0.0
        self.has_hit = False
        if psys:
            for _ in range(40):
                ang = random.uniform(0, math.pi*2)
                r   = random.uniform(50, 250)
                psys.spawn(self._zone_x + math.cos(ang)*r,
                           self._zone_y + math.sin(ang)*r,
                           random.choice(GRAVITY_COLORS),
                           count=1, speed=random.uniform(2,7),
                           gravity=-0.03, life=random.randint(20,40), r=random.randint(4,9), glow=True)

    def on_update(self, owner, event_bus=None, psys=None):
        elapsed = self.duration - self.timer
        self._warp_offset += 0.08
        for ring in self._explode_rings:
            ring["r"]    += ring["speed"]
            ring["alpha"] = max(0, ring["alpha"] - ring["decay"])
        self._explode_rings = [r for r in self._explode_rings if r["alpha"] > 0]
        if self._exploded: return

        target = getattr(owner, "_skill_target", None)
        if target and not target.dead and elapsed > self.WARN_FRAMES:
            dx = self._zone_x - target.rect.centerx
            dy = self._zone_y - target.rect.centery
            dist = max(1, math.sqrt(dx*dx+dy*dy))
            max_pull_dist = self.ZONE_W * 0.65
            if dist <= max_pull_dist:
                proximity = 1.0 - min(1.0, dist / max_pull_dist)
                pull = self.PULL_FORCE * min(2.4, elapsed / self.EXPLODE_FRAME) * (0.35 + proximity * proximity * 2.25)
                target.vel.x += (dx/dist) * pull * 0.42
                target.vel.y += (dy/dist) * pull * 0.32

        if psys and self.timer % 3 == 0:
            ang = random.uniform(0, math.pi*2)
            r   = random.uniform(self.ZONE_W*0.1, self.ZONE_W*0.45)
            psys.spawn(self._zone_x + math.cos(ang)*r,
                       self._zone_y + math.sin(ang)*r,
                       random.choice(GRAVITY_COLORS),
                       count=1, speed=0.8, gravity=0, life=16, r=random.randint(3,7), glow=True)

        if elapsed >= self.EXPLODE_FRAME and not self._exploded:
            self._exploded = True; self.has_hit = True
            for i in range(8):
                self._explode_rings.append({
                    "r": 10+i*18, "speed": 12+i*4,
                    "alpha": 255-i*22, "decay": 5+i*2,
                    "color": GRAVITY_COLORS[i%len(GRAVITY_COLORS)]
                })
            if target and not target.dead:
                dx = target.rect.centerx - self._zone_x
                dy = target.rect.centery - self._zone_y
                dist = max(1, math.sqrt(dx*dx+dy*dy))
                kb = 38 + target.damage_pct * 0.1
                target.vel.x = (dx/dist) * kb * 1.5
                target.vel.y = (dy/dist) * kb * 1.2 - 10
            if psys:
                for col in GRAVITY_COLORS + [(255,255,255)]:
                    psys.spawn(self._zone_x, self._zone_y, col,
                               count=30, speed=14, gravity=-0.04, life=44, r=9, glow=True)

    def draw_behind(self, owner, screen, camera, dr, bob, z):
        if not self.active: return
        sx, sy  = camera.world_to_screen(int(self._zone_x), int(self._zone_y))
        elapsed = self.duration - self.timer
        t       = min(1.0, elapsed / max(1, self.EXPLODE_FRAME))
        tick    = pygame.time.get_ticks()

        for ring in self._explode_rings:
            r_px = int(ring["r"]*z)
            if r_px < 2: continue
            rs = pygame.Surface((r_px*2+8, r_px*2+8), pygame.SRCALPHA)
            pygame.draw.circle(rs, (*ring["color"], _alpha(ring["alpha"])),
                               (r_px+4, r_px+4), r_px, max(2,int(5*z)))
            screen.blit(rs, (sx-r_px-4, sy-r_px-4))
        if self._exploded: return

        base_r = int(self.ZONE_W * 0.5 * z)
        alpha  = _alpha(max(30, 90 * t))

        # 거대 어둠 구
        cs = pygame.Surface((base_r*2+16, base_r*2+16), pygame.SRCALPHA)
        pygame.draw.circle(cs, (5,1,15,_alpha(alpha*1.5)), (base_r+8,base_r+8), base_r)
        screen.blit(cs, (sx-base_r-8, sy-base_r-8))

        # 시공간 왜곡 링 다수
        for i in range(7):
            r_val = int(base_r * (0.15 + i*0.13))
            rot   = tick * (0.012 - i*0.001) * (-1 if i%2 else 1) + self._warp_offset
            rs2   = pygame.Surface((r_val*2+10, r_val*2+10), pygame.SRCALPHA)
            col   = GRAVITY_COLORS[i%len(GRAVITY_COLORS)]
            for seg in range(8):
                sa  = rot + seg * math.pi/4
                ea  = sa + math.pi/5
                pts = [(r_val+5 + int(r_val*math.cos(sa+k*(ea-sa)/10)),
                        r_val+5 + int(r_val*math.sin(sa+k*(ea-sa)/10)))
                       for k in range(11)]
                if len(pts)>1:
                    pygame.draw.lines(rs2, (*col, _alpha(alpha - i*10)),
                                      False, pts, max(1,int(2*z)))
            screen.blit(rs2, (sx-r_val-5, sy-r_val-5))

        # 경보 링 (폭발 임박)
        if t > 0.7:
            warn_r = int(base_r * (0.5 + (t-0.7)/0.3 * 0.5))
            ws = pygame.Surface((warn_r*2+10, warn_r*2+10), pygame.SRCALPHA)
            pygame.draw.circle(ws, (255,100,60,_alpha(200*(t-0.7)/0.3)),
                               (warn_r+5,warn_r+5), warn_r, max(3,int(5*z)))
            screen.blit(ws, (sx-warn_r-5, sy-warn_r-5))


class PhotoelectricBurst(_NormalOnlyMixin, BeamSkill):
    DISPLAY_NAME = "Photoelectric Burst"
    DESCRIPTION = "Fire a photon packet that kicks electrons forward."
    BEAM_LENGTH = 260
    BEAM_WIDTH = 26
    BEAM_COLOR = (255, 210, 90)
    BEAM_GLOW = (255, 245, 185)
    COOLDOWN_SEC = 4.8

    def __init__(self):
        super().__init__("Photoelectric Burst", damage=24, cooldown=288, duration=18)
        self.charge_value = 1.1
        self._cast_facing = 1

    def on_start(self, owner, event_bus=None, psys=None):
        self._cast_facing = owner.facing
        if psys:
            for _ in range(20):
                px = owner.rect.centerx + self._cast_facing * random.randint(18, 72)
                py = owner.rect.centery + random.randint(-24, 24)
                psys.spawn(px, py, random.choice([(255,210,90), (255,245,185), (120,190,255)]),
                           count=1, speed=random.uniform(3, 8), gravity=-0.04,
                           life=random.randint(10, 20), r=random.randint(2, 5), glow=True)

    def get_hitbox(self, owner):
        if not self.active:
            return None
        w = self.BEAM_LENGTH
        h = self.BEAM_WIDTH + 18
        facing = getattr(self, "_cast_facing", owner.facing)
        ox = owner.rect.right - 6 if facing == 1 else owner.rect.left - w + 6
        return pygame.Rect(ox, owner.rect.centery - h//2, w, h)

    def on_hit(self, owner, target, event_bus, psys=None, fsys=None):
        facing = getattr(self, "_cast_facing", owner.facing)
        target.vel.x += facing * 12
        target.vel.y -= 3
        if psys:
            psys.spawn(target.rect.centerx, target.rect.centery, (255,245,185),
                       count=22, speed=8, gravity=-0.05, life=20, r=4, glow=True)
        super().on_hit(owner, target, event_bus, psys, fsys)

    def draw_front(self, owner, screen, camera, dr, bob, z):
        if not self.active:
            return
        facing = getattr(self, "_cast_facing", owner.facing)
        t = self.timer / max(1, self.duration)
        alpha = _alpha(230 * t)
        length = int(self.BEAM_LENGTH * z)
        sx = dr.right - int(6*z) if facing == 1 else dr.left - length + int(6*z)
        sy = dr.centery + bob
        for i in range(7):
            px = sx + (i * length // 7 if facing == 1 else length - i * length // 7)
            off = int(math.sin(pygame.time.get_ticks()*0.025 + i) * 10 * z)
            rr = max(3, int((8 + i % 3 * 2) * z))
            pygame.draw.circle(screen, (255, 220, 110, alpha), (px, sy + off), rr)
            pygame.draw.circle(screen, (255, 250, 210, _alpha(alpha*0.65)), (px, sy + off), max(1, rr//2))


class RelativityFrame(_NormalOnlyMixin, SummonZoneSkill):
    DISPLAY_NAME = "Relativity Frame"
    DESCRIPTION = "Bend local time around the enemy. Slows and snaps them outward."
    WARN_FRAMES = 22
    ZONE_W = 180
    ZONE_H = 150
    ZONE_COLOR = (80, 150, 255)
    ZONE_GLOW = (255, 245, 185)
    COOLDOWN_SEC = 8.5
    SNAP_FRAME = 62

    def __init__(self):
        super().__init__("Relativity Frame", damage=30, cooldown=510, duration=105)
        self.charge_value = 1.35
        self._snapped = False
        self._rings = []

    def on_start(self, owner, event_bus=None, psys=None):
        target = getattr(owner, "_skill_target", None)
        if target and not target.dead:
            self._zone_x = target.rect.centerx
            self._zone_y = target.rect.centery
        else:
            self._zone_x = owner.rect.centerx + owner.facing * 210
            self._zone_y = owner.rect.centery
        self._snapped = False
        self._rings = []
        self.has_hit = False

    def on_update(self, owner, event_bus=None, psys=None):
        elapsed = self.duration - self.timer
        for r in self._rings:
            r["r"] += r["speed"]
            r["a"] = max(0, r["a"] - 10)
        self._rings = [r for r in self._rings if r["a"] > 0]

        target = getattr(owner, "_skill_target", None)
        zone = self.get_hitbox(owner)
        if target and not target.dead and zone and zone.colliderect(target.rect):
            target.vel.x *= 0.68
            target.vel.y *= 0.74
            if psys and self.timer % 5 == 0:
                psys.spawn(target.rect.centerx, target.rect.centery,
                           random.choice([(255,245,185), (80,150,255)]),
                           count=2, speed=1.4, gravity=0, life=12, r=3, glow=True)

        if elapsed >= self.SNAP_FRAME and not self._snapped:
            self._snapped = True
            self.has_hit = False
            self._rings.append({"r": 16, "speed": 10, "a": 230})

    def on_hit(self, owner, target, event_bus, psys=None, fsys=None):
        dx = target.rect.centerx - self._zone_x
        dy = target.rect.centery - self._zone_y
        dist = max(1, math.sqrt(dx*dx + dy*dy))
        target.vel.x = dx / dist * 18
        target.vel.y = dy / dist * 10 - 7
        if psys:
            psys.spawn(self._zone_x, self._zone_y, (255,245,185),
                       count=30, speed=9, gravity=-0.04, life=28, r=5, glow=True)
        super().on_hit(owner, target, event_bus, psys, fsys)

    def get_hitbox(self, owner):
        if not self.active:
            return None
        elapsed = self.duration - self.timer
        if elapsed < self.WARN_FRAMES:
            return None
        return pygame.Rect(int(self._zone_x)-self.ZONE_W//2,
                           int(self._zone_y)-self.ZONE_H//2,
                           self.ZONE_W, self.ZONE_H)

    def draw_behind(self, owner, screen, camera, dr, bob, z):
        if not self.active:
            return
        sx, sy = camera.world_to_screen(int(self._zone_x), int(self._zone_y))
        elapsed = self.duration - self.timer
        warn = elapsed < self.WARN_FRAMES
        alpha = _alpha(95 + 80 * abs(math.sin(elapsed * 0.23))) if warn else _alpha(120 * self.timer / self.duration)
        base = int(self.ZONE_W * 0.5 * z)
        tick = pygame.time.get_ticks()
        for i in range(5):
            rr = max(2, int(base * (0.35 + i*0.18)))
            surf = pygame.Surface((rr*2+8, rr*2+8), pygame.SRCALPHA)
            pygame.draw.circle(surf, (255,245,185,_alpha(alpha - i*12)), (rr+4, rr+4), rr, max(1, int(2*z)))
            wobble = int(math.sin(tick*0.012+i) * 5 * z)
            screen.blit(surf, (sx-rr-4+wobble, sy-rr-4))
        for r in self._rings:
            rr = int(r["r"] * z)
            surf = pygame.Surface((rr*2+8, rr*2+8), pygame.SRCALPHA)
            pygame.draw.circle(surf, (80,150,255,_alpha(r["a"])), (rr+4, rr+4), rr, max(2,int(4*z)))
            screen.blit(surf, (sx-rr-4, sy-rr-4))


class LightConeCascade(_DomainOnlyMixin, PhotoelectricBurst):
    DISPLAY_NAME = "Light Cone Cascade"
    DESCRIPTION = "Domain — fire stacked light-cone photon pulses."
    BEAM_LENGTH = 390
    BEAM_WIDTH = 42
    COOLDOWN_SEC = 5.5

    def __init__(self):
        BeamSkill.__init__(self, "Light Cone Cascade", damage=42, cooldown=330, duration=26)
        self.charge_value = 0.0
        self.finisher_charge_value = 2.1
        self._cast_facing = 1

    def on_hit(self, owner, target, event_bus, psys=None, fsys=None):
        facing = getattr(self, "_cast_facing", owner.facing)
        target.vel.x = facing * 20
        target.vel.y -= 8
        super().on_hit(owner, target, event_bus, psys, fsys)


class TwinParadox(_DomainOnlyMixin, RelativityFrame):
    DISPLAY_NAME = "Twin Paradox"
    DESCRIPTION = "Domain — split the enemy's frame of reference, then snap it shut."
    WARN_FRAMES = 12
    ZONE_W = 320
    ZONE_H = 260
    COOLDOWN_SEC = 12.0
    SNAP_FRAME = 76

    def __init__(self):
        SummonZoneSkill.__init__(self, "Twin Paradox", damage=48, cooldown=720, duration=140)
        self.charge_value = 0.0
        self.finisher_charge_value = 2.8
        self._snapped = False
        self._rings = []


class LightSwordAwakening(_NormalOnlyMixin, Skill):
    DISPLAY_NAME = "Light Sword"
    DESCRIPTION = "Lock Q and turn basic attacks into light-sword slashes."
    COOLDOWN_SEC = 0.0

    def __init__(self):
        super().__init__("Light Sword", damage=0, cooldown=0, duration=24)
        self.charge_value = 0.0

    def on_start(self, owner, event_bus=None, psys=None):
        owner._light_sword_mode = True
        owner._light_sword_domain_mode = False
        owner.attack_cooldown = 0
        self.lock()
        if psys:
            for _ in range(30):
                ang = random.uniform(0, math.pi * 2)
                psys.spawn(owner.rect.centerx + math.cos(ang) * 34,
                           owner.rect.centery + math.sin(ang) * 34,
                           random.choice(LIGHT_COLORS),
                           count=1, speed=random.uniform(3, 9), gravity=-0.04,
                           life=random.randint(16, 30), r=random.randint(3, 7), glow=True)

    def draw_front(self, owner, screen, camera, dr, bob, z):
        if not self.active:
            return
        t = 1.0 - self.timer / max(1, self.duration)
        rr = int((34 + 42 * t) * z)
        if rr <= 1:
            return
        sf = pygame.Surface((rr*2+8, rr*2+8), pygame.SRCALPHA)
        pygame.draw.circle(sf, (255,240,150,_alpha(160*(1-t))), (rr+4, rr+4), rr)
        pygame.draw.circle(sf, (255,255,230,_alpha(220*(1-t))), (rr+4, rr+4), max(2, rr//2), max(2, int(4*z)))
        screen.blit(sf, (dr.centerx-rr-4, dr.centery+bob-rr-4))


class DomainLightSwordAwakening(_DomainOnlyMixin, LightSwordAwakening):
    DISPLAY_NAME = "Photon Saber"
    DESCRIPTION = "Domain — light-sword attacks leave an exploding rift along the slash path."

    def __init__(self):
        Skill.__init__(self, "Photon Saber", damage=0, cooldown=0, duration=30)
        self.charge_value = 0.0
        self.finisher_charge_value = 0.0

    def on_start(self, owner, event_bus=None, psys=None):
        owner._light_sword_mode = True
        owner._light_sword_domain_mode = True
        owner.attack_cooldown = 0
        self.lock()
        if psys:
            for _ in range(42):
                ang = random.uniform(0, math.pi * 2)
                psys.spawn(owner.rect.centerx + math.cos(ang) * 44,
                           owner.rect.centery + math.sin(ang) * 44,
                           random.choice(LIGHT_COLORS),
                           count=1, speed=random.uniform(4, 11), gravity=-0.05,
                           life=random.randint(18, 34), r=random.randint(3, 8), glow=True)


# ── 캐릭터 ───────────────────────────────────────────────────────────────────
class Einstein(Player):
    WEIGHT     = 112; KB_GROWTH = 72;  BASE_KB   = 38
    WALK_SPEED = 5.8; JUMP_POWER = -14.5; MAX_JUMPS = 2
    ATTACK_DMG = 16;  ATK_FRAMES = 24;   ATK_CD    = 40
    HIT_START  = 5;   HIT_END    = 18
    LIGHT_ATK_FRAMES = 18
    LIGHT_ATK_CD = 24
    LIGHT_HIT_START = 4
    LIGHT_HIT_END = 13
    LIGHT_RIFT_EXPLODE_DELAY = 120

    BODY_COLOR    = (225, 55, 55);  TRIM_COLOR  = (145, 20, 20)
    GLOW_COLOR    = (255, 130, 110); DARK_COLOR = (110, 15, 15)
    DISPLAY_NAME  = "Einstein"
    DESCRIPTION   = "Gravity master. Pull, crush, collapse.\nHigh damage, slow but devastating."
    PREVIEW_COLOR = (225, 55, 55)

    SPRITE_PATH   = "assets/images/charactor/Einstein/IDL.png"
    SPRITE_IDLE   = "assets/images/charactor/Einstein/IDL.png"
    SPRITE_JUMP   = "assets/images/charactor/Einstein/jump.png"
    SPRITE_ATTACK = "assets/images/charactor/Einstein/attack.png"
    SPRITE_SKILL  = "assets/images/charactor/Einstein/skill.png"
    SPRITE_SCALE  = 1.25; SPRITE_OFFSET_X = 0; SPRITE_OFFSET_Y = 6

    def __init__(self, x, y, name="Player", player_id=1):
        super().__init__(x, y, name, player_id)
        self.color = self.BODY_COLOR; self.trim_color = self.TRIM_COLOR
        self.glow_color = self.GLOW_COLOR; self.dark_color = self.DARK_COLOR
        self.max_jumps = self.MAX_JUMPS; self.attack_damage = self.ATTACK_DMG
        self._light_sword_mode = False
        self._light_sword_domain_mode = False
        self._light_rifts = []
        self._light_rift_facing = 1
        self._light_rift_origin = (0, 0)

    def _init_skills(self):
        self.skills["skill_Q"]        = LightSwordAwakening()
        self.skills["skill_E"]        = EventHorizon()
        self.skills["skill_R"]        = EinsteinDomain()
        self.skills["skill_Q_domain"] = DomainLightSwordAwakening()
        self.skills["skill_E_domain"] = Singularity()

    def _reset_light_sword_state(self):
        self._light_sword_mode = False
        self._light_sword_domain_mode = False
        self._light_rifts = []
        self.attack_timer = 0
        self.attack_cooldown = 0
        self.has_hit = False

        for key in ("skill_Q", "skill_Q_domain"):
            skill = self.skills.get(key)
            if skill is not None and hasattr(skill, "unlock"):
                skill.unlock()

    def reset_domain_state(self):
        super().reset_domain_state()
        self._reset_light_sword_state()

    def on_domain_closed(self):
        self._reset_light_sword_state()

    def start_attack(self):
        if getattr(self, "_light_sword_mode", False):
            if self.attack_cooldown <= 0:
                self.attack_timer = self.LIGHT_ATK_FRAMES
                self.attack_cooldown = self.LIGHT_ATK_CD
                self.has_hit = False
        else:
            super().start_attack()
        if self.attack_timer == self.LIGHT_ATK_FRAMES and getattr(self, "_light_sword_domain_mode", False):
            self._spawn_light_rift()

    def get_attack_hitbox(self):
        if not getattr(self, "_light_sword_mode", False):
            return super().get_attack_hitbox()
        if not (self.LIGHT_HIT_START <= self.attack_timer <= self.LIGHT_HIT_END):
            return None
        w = int(self.rect.w * 2.65)
        h = int(self.rect.h * 1.85)
        x = self.rect.right - 10 if self.facing == 1 else self.rect.left - w + 10
        return pygame.Rect(x, self.rect.centery - h // 2, w, h)

    def check_attack_collision(self, target, event_bus, psys=None, fsys=None):
        if not getattr(self, "_light_sword_mode", False):
            return super().check_attack_collision(target, event_bus, psys, fsys)
        if self.dead or target.dead or target.invincible > 0:
            return
        hb = self.get_attack_hitbox()
        if hb is not None and not self.has_hit and hb.colliderect(target.rect):
            self.has_hit = True
            damage = self.ATTACK_DMG + (10 if getattr(self, "_light_sword_domain_mode", False) else 6)
            event_bus.emit("attack_hit", {
                "attacker": self,
                "target": target,
                "damage": damage,
                "is_skill": False,
                "particle_system": psys,
                "floater_system": fsys,
            })
            if psys:
                psys.spawn(target.rect.centerx, target.rect.centery, (255, 245, 180),
                           count=18, speed=7, gravity=-0.04, life=20, r=4, glow=True)

        if getattr(self, "_light_sword_domain_mode", False) and not self.has_hit:
            for rift in self._light_rifts:
                if rift["hit"] or not rift["exploded"]:
                    continue
                if rift["rect"].colliderect(target.rect):
                    rift["hit"] = True
                    self.has_hit = True
                    event_bus.emit("attack_hit", {
                        "attacker": self,
                        "target": target,
                        "damage": self.ATTACK_DMG + 12,
                        "is_skill": False,
                        "particle_system": psys,
                        "floater_system": fsys,
                    })
                    break

    def _spawn_light_rift(self):
        self._light_rifts = []
        self._light_rift_facing = self.facing
        self._light_rift_origin = (self.rect.centerx, self.rect.top)
        facing = self.facing
        origin_x, origin_y = self._light_rift_origin
        pivot_x = origin_x + facing * 14
        pivot_y = origin_y + 14
        points = []
        for path_t in (0.18, 0.30, 0.42, 0.54, 0.66, 0.78):
            angle = math.radians(-132 + 264 * path_t)
            path_len = 108
            points.append((
                pivot_x + math.cos(angle) * path_len * facing,
                pivot_y + math.sin(angle) * path_len,
            ))
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        pad = 34
        rect = pygame.Rect(min(xs) - pad, min(ys) - pad,
                           max(xs) - min(xs) + pad * 2,
                           max(ys) - min(ys) + pad * 2)
        sparks = []
        path_segments = max(1, len(points) - 1)
        for _ in range(46):
            seg = random.randrange(path_segments)
            path_t = random.random()
            max_life = random.randint(42, 70)
            sparks.append({
                "seg": seg,
                "t": path_t,
                "path": (seg + path_t) / path_segments,
                "off": random.uniform(-28, 28),
                "speed": random.uniform(0.012, 0.035),
                "life": random.randint(24, max_life),
                "max_life": max_life,
                "size": random.uniform(2.0, 5.5),
                "phase": random.uniform(0, math.pi * 2),
                "color": random.choice([(255,255,245), (255,235,120), (140,210,255)]),
            })

        self._light_rifts.append({
            "points": points,
            "rect": rect,
            "build_timer": self.LIGHT_ATK_FRAMES,
            "max_build_timer": self.LIGHT_ATK_FRAMES,
            "explode_delay": self.LIGHT_RIFT_EXPLODE_DELAY,
            "explosion_timer": 18,
            "exploded": False,
            "hit": False,
            "phase": random.uniform(0, math.pi * 2),
            "sparks": sparks,
        })

    def update(self, dt, platforms, event_bus, psys=None):
        super().update(dt, platforms, event_bus, psys)
        target = getattr(self, "_skill_target", None)
        for rift in self._light_rifts:
            if not rift["exploded"]:
                if rift["build_timer"] > 0:
                    rift["build_timer"] -= 1
                else:
                    rift["explode_delay"] -= 1

                if target and not target.dead and rift["build_timer"] <= 0 and rift["rect"].colliderect(target.rect):
                    cx, cy = rift["rect"].center
                    dx = cx - target.rect.centerx
                    dy = cy - target.rect.centery
                    dist = max(1, math.sqrt(dx*dx + dy*dy))
                    target.vel.x += (dx / dist) * 1.25
                    target.vel.y += (dy / dist) * 0.85

                if rift["build_timer"] <= 0 and rift["explode_delay"] <= 0:
                    rift["exploded"] = True
            else:
                rift["explosion_timer"] -= 1
            for spark in rift.get("sparks", []):
                spark["t"] = (spark["t"] + spark["speed"]) % 1.0
                spark["life"] -= 1
                if spark["life"] <= 0:
                    spark["life"] = spark["max_life"]
                    spark["off"] = random.uniform(-30, 30)
        self._light_rifts = [
            rift for rift in self._light_rifts
            if not rift["exploded"] or rift["explosion_timer"] > 0
        ]

    def draw(self, screen, camera):
        super().draw(screen, camera)
        if self.dead or self.respawning:
            return
        dr = self._get_draw_rect(camera)
        z = camera.zoom
        bob = int(math.sin(self.bob_t) * 2.2 * z) if self.on_ground else 0
        if getattr(self, "_light_sword_mode", False):
            self._draw_light_sword(screen, camera, dr, bob, z)
        if getattr(self, "_light_sword_domain_mode", False):
            self._draw_light_rifts(screen, camera, z)

    def _draw_light_sword(self, screen, camera, dr, bob, z):
        if self.attack_timer > 0:
            prog = 1.0 - self.attack_timer / max(1, self.LIGHT_ATK_FRAMES)
            ease = 1.0 - (1.0 - prog) ** 3
            arc = math.sin(ease * math.pi)
            length = int((82 + 34 * arc) * z)
            pivot_x = dr.centerx + self.facing * int(14 * z)
            pivot_y = dr.top + bob + int(16 * z)
            angle = -132 + 264 * ease
            rad = math.radians(angle)
            tip_x = pivot_x + int(math.cos(rad) * length) * self.facing
            tip_y = pivot_y + int(math.sin(rad) * length)
            trail_t = max(0.0, min(1.0, arc))
            width = max(4, int((6 + 9 * trail_t) * z))

            points = []
            for i in range(7):
                old = max(0.0, ease - i * 0.055)
                old_angle = math.radians(-132 + 264 * old)
                old_len = int((68 + 30 * math.sin(old * math.pi)) * z)
                points.append((
                    pivot_x + int(math.cos(old_angle) * old_len) * self.facing,
                    pivot_y + int(math.sin(old_angle) * old_len),
                ))

            for i in range(len(points) - 1):
                a = _alpha(165 * (1 - i / len(points)))
                pygame.draw.line(screen, (255, 225, 90, a), points[i], points[i+1], max(2, width - i))

            pygame.draw.line(screen, (255, 238, 115), (pivot_x, pivot_y), (tip_x, tip_y),
                             width + max(2, int(3*z)))
            pygame.draw.line(screen, (255, 255, 245), (pivot_x, pivot_y), (tip_x, tip_y),
                             max(2, width // 2))
            pygame.draw.circle(screen, (120, 190, 255), (tip_x, tip_y), max(3, int(7*z)))
        else:
            sx = dr.centerx + self.facing * int(34 * z)
            sy = dr.top + bob + int(18 * z)
            ex = sx + self.facing * int(62 * z)
            ey = sy - int(12 * z)
            pygame.draw.line(screen, (255, 240, 140), (sx, sy), (ex, ey), max(3, int(5*z)))
            pygame.draw.line(screen, (255, 255, 245), (sx, sy), (ex, ey), max(1, int(2*z)))

    def _draw_light_rifts(self, screen, camera, z):
        tick = pygame.time.get_ticks()
        for rift in self._light_rifts:
            pts = [camera.world_to_screen(x, y) for x, y in rift["points"]]
            if len(pts) < 2:
                continue
            if rift["exploded"]:
                t = 1.0 - rift["explosion_timer"] / 18
                cx, cy = camera.world_to_screen(*rift["rect"].center)
                rr = max(8, int((42 + 76 * t) * z))
                sf = pygame.Surface((rr*2+10, rr*2+10), pygame.SRCALPHA)
                pygame.draw.circle(sf, (255, 235, 120, _alpha(130 * (1-t))), (rr+5, rr+5), rr)
                pygame.draw.circle(sf, (255, 255, 245, _alpha(210 * (1-t))), (rr+5, rr+5), max(3, rr//2), max(2, int(4*z)))
                screen.blit(sf, (cx-rr-5, cy-rr-5), special_flags=pygame.BLEND_RGBA_ADD)
                continue

            build = 1.0 - rift["build_timer"] / max(1, rift["max_build_timer"])
            build = max(0.0, min(1.0, build))
            pulse = 0.72 + 0.28 * math.sin(tick * 0.035 + rift["phase"])
            alpha = _alpha(150 + 70 * pulse)
            for spark in rift.get("sparks", []):
                if spark.get("path", 0.0) > build:
                    continue
                seg = min(spark["seg"], len(pts) - 2)
                ax, ay = pts[seg]
                bx, by = pts[seg + 1]
                tx = spark["t"]
                px = ax + (bx - ax) * tx
                py = ay + (by - ay) * tx
                dx = bx - ax
                dy = by - ay
                dist = max(1, math.sqrt(dx*dx + dy*dy))
                nx = -dy / dist
                ny = dx / dist
                flicker = math.sin(tick * 0.04 + spark["phase"]) * 7
                px += nx * (spark["off"] + flicker) * z
                py += ny * (spark["off"] + flicker) * z
                life_ratio = max(0.15, spark["life"] / max(1, spark["max_life"]))
                radius = max(1, int(spark["size"] * z * (0.65 + 0.45 * pulse)))
                color = spark["color"]
                glow = pygame.Surface((radius*6, radius*6), pygame.SRCALPHA)
                c = radius * 3
                pygame.draw.circle(glow, (*color, _alpha(alpha * 0.13 * life_ratio)), (c, c), radius * 3)
                pygame.draw.circle(glow, (*color, _alpha(alpha * 0.62 * life_ratio)), (c, c), radius)
                screen.blit(glow, (int(px)-c, int(py)-c), special_flags=pygame.BLEND_RGBA_ADD)

    def get_char_name(self): return "Einstein"
