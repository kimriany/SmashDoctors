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

    PULL_FORCE   = 2.5
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
            self._zone_x = target.rect.centerx
            self._zone_y = target.rect.centery
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
        zone   = self.get_hitbox(owner)
        if target and not target.dead and zone and zone.colliderect(target.rect):
            dx = self._zone_x - target.rect.centerx
            dy = self._zone_y - target.rect.centery
            dist = max(1, math.sqrt(dx*dx + dy*dy))
            pull = self.PULL_FORCE * (1 + elapsed / self.EXPLODE_FRAME)
            target.vel.x += (dx/dist) * pull * 0.25
            target.vel.y += (dy/dist) * pull * 0.25

        if psys and self.timer % 4 == 0:
            ang = random.uniform(0, math.pi*2)
            r   = random.uniform(self.ZONE_W*0.2, self.ZONE_W*0.45)
            psys.spawn(self._zone_x + math.cos(ang)*r,
                       self._zone_y + math.sin(ang)*r,
                       random.choice(GRAVITY_COLORS),
                       count=1, speed=0.5, gravity=0, life=14, r=3, glow=True)

        if elapsed >= self.EXPLODE_FRAME and not self._exploded:
            self._exploded = True
            self.has_hit   = True
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
    DOMAIN_BG_PATH        = "assets/images/charactor/Einstein/IDL.png"  # 임시 — domain.jpeg 추가 시 교체
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
            pull = self.PULL_FORCE * min(2.0, elapsed / self.EXPLODE_FRAME)
            target.vel.x += (dx/dist) * pull * 0.3
            target.vel.y += (dy/dist) * pull * 0.2

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


# ── 캐릭터 ───────────────────────────────────────────────────────────────────
class Einstein(Player):
    WEIGHT     = 112; KB_GROWTH = 72;  BASE_KB   = 38
    WALK_SPEED = 5.8; JUMP_POWER = -14.5; MAX_JUMPS = 2
    ATTACK_DMG = 16;  ATK_FRAMES = 24;   ATK_CD    = 40
    HIT_START  = 5;   HIT_END    = 18

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

    def _init_skills(self):
        self.skills["skill_Q"]        = GravityLash()
        self.skills["skill_E"]        = EventHorizon()
        self.skills["skill_R"]        = EinsteinDomain()
        self.skills["skill_Q_domain"] = SpacetimeRend()
        self.skills["skill_E_domain"] = Singularity()

    def get_char_name(self): return "Einstein"