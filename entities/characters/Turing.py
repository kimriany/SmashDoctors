"""
Turing — 암호 해독과 계산 자동화로 상대를 제압

일반 스킬:
  Q / ;  Enigma Decrypt    — 에니그마 해독 빔, 명중 시 상대 스킬 쿨타임 강제 증가
  E / '  Bombe Machine     — 자동 추적 폭탄, 계산된 경로로 상대에게 접근

영역 전개 중:
  Q / ;  Turing Complete   — 완전한 계산 광선, 다단히트 + 쿨타임 완전 리셋
  E / '  Decidability Trap — 거대 계산 격자, 내부 적 완전 정지
"""
from entities.player import Player
from systems.skill import Skill, BeamSkill, ProjectileSkill, SummonZoneSkill, DomainUltimateSkill
import pygame
import math
import random


class _DomainOnlyMixin:
    def can_activate(self, owner): return getattr(owner, "domain_active", False)

class _NormalOnlyMixin:
    def can_activate(self, owner): return not getattr(owner, "domain_active", False)

def _alpha(v): return max(0, min(255, int(v)))

BIT_COLORS  = [(80, 235, 190), (120, 200, 255), (60, 160, 140), (200, 255, 240)]
CODE_CHARS  = ["0","1","{}","[]","//","()","&&","||","==","!=","NP","++"]


# ── Q: Enigma Decrypt (에니그마 해독 빔) ─────────────────────────────────────
class CipherStrike(_NormalOnlyMixin, Skill):
    """
    튜링 Q — Cipher Strike (암호 펀치)

    전방으로 강타. 빔이 아닌 근접 타격.
    명중 시:
    - 화면에 암호 코드 파편 폭발 (시각 이펙트)
    - 상대의 모든 스킬 쿨타임 +120프레임 강제 증가
    - 상대 이동방향 반전 (짧은 혼란)

    공격 자체는 강하지 않지만 쿨타임 증가로
    상대 스킬 사이클을 완전히 망가뜨림.
    """
    DISPLAY_NAME  = "Cipher Strike"
    DESCRIPTION   = "Punch that encrypts the enemy's skills.\nAll skill cooldowns greatly extended."
    COOLDOWN_SEC  = 5.0

    HIT_FRAME    = 7
    ATK_FRAMES   = 22
    CD_PENALTY   = 120   # 쿨타임 증가 프레임

    def __init__(self):
        super().__init__("Cipher Strike", damage=22, cooldown=300, duration=22)
        self.charge_value = 1.1
        self._code_burst  = []   # 코드 파편 이펙트 위치

    def on_start(self, owner, event_bus=None, psys=None):
        self._code_burst = []
        if psys:
            psys.spawn(owner.rect.centerx + owner.facing * 30,
                       owner.rect.centery,
                       (80,235,190), count=8, speed=4, gravity=0, life=12, r=4, glow=True)

    def get_hitbox(self, owner):
        if not self.active: return None
        elapsed = self.duration - self.timer
        if elapsed < self.HIT_FRAME or elapsed > self.HIT_FRAME + 8:
            return None
        w = int(owner.rect.w * 2.0)
        h = int(owner.rect.h * 1.4)
        x = owner.rect.right - 8 if owner.facing == 1 else owner.rect.left - w + 8
        return pygame.Rect(x, owner.rect.centery - h//2, w, h)

    def on_update(self, owner, event_bus=None, psys=None):
        elapsed = self.duration - self.timer
        # 타격 프레임 이펙트
        if elapsed == self.HIT_FRAME and psys:
            cx = owner.rect.centerx + owner.facing * int(owner.rect.w * 0.8)
            cy = owner.rect.centery
            for _ in range(22):
                ang = random.uniform(-math.pi*0.6, math.pi*0.6) + (0 if owner.facing==1 else math.pi)
                psys.spawn(cx + math.cos(ang)*10, cy + math.sin(ang)*10,
                           random.choice(BIT_COLORS),
                           count=1, speed=random.uniform(5,11),
                           gravity=0.1, life=random.randint(12,22), r=random.randint(3,6), glow=True)

        # 코드 파편 이펙트 업데이트
        for c in self._code_burst:
            c["x"] += c["vx"]; c["y"] += c["vy"]
            c["vy"] += 0.3; c["vx"] *= 0.92
            c["life"] -= 1

        self._code_burst = [c for c in self._code_burst if c["life"] > 0]

    def on_hit(self, owner, target, event_bus, psys=None, fsys=None):
        # 쿨타임 증가 디버프
        for sk in target.skills.values():
            if sk.cooldown:
                sk.current_cooldown = min(sk.cooldown, sk.current_cooldown + self.CD_PENALTY)

        # 이동방향 반전 (혼란)
        target.vel.x = -target.vel.x * 0.6
        target.vel.y -= 3

        # 코드 파편 스폰
        for _ in range(16):
            ang = random.uniform(0, math.pi*2)
            spd = random.uniform(4, 9)
            self._code_burst.append({
                "x": float(target.rect.centerx),
                "y": float(target.rect.centery),
                "vx": math.cos(ang)*spd, "vy": math.sin(ang)*spd - 2,
                "char": random.choice(CODE_CHARS),
                "col": random.choice(BIT_COLORS),
                "life": random.randint(18, 32),
                "max_life": 30,
            })

        if psys:
            psys.spawn(target.rect.centerx, target.rect.centery,
                       (80,235,190), count=20, speed=7, gravity=0.1, life=20, r=5, glow=True)
            psys.spawn(target.rect.centerx, target.rect.centery,
                       (255,255,255), count=8, speed=5, gravity=0, life=12, r=3, glow=True)

        super().on_hit(owner, target, event_bus, psys, fsys)

    def draw_front(self, owner, screen, camera, dr, bob, z):
        # 타격 이펙트 (주먹 궤적)
        if self.active:
            elapsed = self.duration - self.timer
            if self.HIT_FRAME - 3 <= elapsed <= self.HIT_FRAME + 6:
                t2 = (elapsed - (self.HIT_FRAME-3)) / 9
                cx = dr.centerx + dr.w//2 * owner.facing
                cy = dr.centery + bob
                r2 = int(dr.w * 0.6 * z)
                alpha = _alpha(220 * (1 - abs(t2*2-1)*0.5))
                # 충격파 원
                for ri in range(3):
                    rr = int(r2 * (t2*(1+ri*0.5)+0.2))
                    if rr < 2: continue
                    rs = pygame.Surface((rr*2+4,rr*2+4),pygame.SRCALPHA)
                    pygame.draw.circle(rs,
                        (*BIT_COLORS[ri%len(BIT_COLORS)], _alpha(alpha*(1-ri*0.25))),
                        (rr+2,rr+2), rr, max(1,int(3*z)))
                    screen.blit(rs,(cx-rr-2, cy-rr-2))
                # 암호 부호 (충격)
                fnt = pygame.font.SysFont(None, max(10,int(18*z)), bold=True)
                for i, char in enumerate(["ENCRYPT","!","##","??"]):
                    offset_x = owner.facing * int((r2*0.4 + i*r2*0.25)*t2)
                    offset_y = int(math.sin(i*1.3) * r2 * 0.5 * t2)
                    cs = fnt.render(char, True, BIT_COLORS[i%len(BIT_COLORS)])
                    cs.set_alpha(_alpha(alpha*0.8))
                    screen.blit(cs, (cx + offset_x - cs.get_width()//2,
                                     cy + offset_y - cs.get_height()//2))

        # 코드 파편
        fnt2 = pygame.font.SysFont(None, max(8,int(13*z)), bold=True)
        for c in self._code_burst:
            cx2, cy2 = camera.world_to_screen(c["x"], c["y"])
            a = _alpha(200 * c["life"] / c["max_life"])
            cs = fnt2.render(c["char"], True, c["col"])
            cs.set_alpha(a)
            screen.blit(cs, (cx2 - cs.get_width()//2, cy2 - cs.get_height()//2))


class BombeMachine(_NormalOnlyMixin, Skill):
    """
    체스판처럼 계산된 경로로 상대에게 접근하는 추적 폭탄.

    - 발동 시 상대 위치 계산 후 경로 확정
    - L자 경로로 이동 (먼저 수평 → 수직)
    - 3회 경로 전환 후 폭발
    """
    DISPLAY_NAME = "Bombe Machine"
    DESCRIPTION  = "Deploy a tracking bomb on a calculated path.\nMoves in L-shapes to the target."
    COOLDOWN_SEC = 7.0

    BOMB_SPEED  = 7.0
    SEGMENTS    = 3   # 경로 전환 횟수

    def __init__(self):
        super().__init__("Bombe Machine", damage=32, cooldown=420, duration=120)
        self.charge_value = 1.3
        self._bx = 0.0; self._by = 0.0
        self._path       = []   # [(tx,ty), ...] 경로 웨이포인트
        self._path_idx   = 0
        self._alive      = True
        self._exploding  = False
        self._explode_t  = 0
        self._spin       = 0.0

    def on_start(self, owner, event_bus=None, psys=None):
        self._bx = float(owner.rect.centerx + owner.facing * 30)
        self._by = float(owner.rect.centery)
        self._alive     = True
        self._exploding = False
        self._explode_t = 0
        self._spin      = 0.0
        self.has_hit    = False

        # 경로 계산 (상대 위치)
        target = getattr(owner, "_skill_target", None)
        if target and not target.dead:
            tx, ty = float(target.rect.centerx), float(target.rect.centery)
        else:
            tx = self._bx + owner.facing * 300
            ty = self._by
        # L자 경로: 3구간
        mx = (self._bx + tx) / 2
        self._path = [
            (mx, self._by),        # 수평 이동
            (mx, ty - 80),         # 수직 이동 (약간 위)
            (tx, ty),              # 목표 도착
        ]
        self._path_idx = 0
        if psys:
            psys.spawn(self._bx, self._by, (80,235,190),
                       count=10, speed=3, gravity=0, life=14, r=4, glow=True)

    def get_hitbox(self, owner):
        if not self._alive: return None
        r = 28 if self._exploding else 14
        return pygame.Rect(int(self._bx)-r, int(self._by)-r, r*2, r*2)

    def on_update(self, owner, event_bus=None, psys=None):
        if not self._alive: return
        if self._exploding:
            self._explode_t += 1
            if self._explode_t > 22: self._alive = False
            return
        self._spin += 6.0

        if self._path_idx >= len(self._path):
            self._trigger_explosion(owner, event_bus, psys)
            return

        # 현재 웨이포인트로 이동
        wx, wy = self._path[self._path_idx]
        dx, dy = wx - self._bx, wy - self._by
        dist   = math.sqrt(dx*dx + dy*dy)
        if dist < self.BOMB_SPEED:
            self._bx = wx; self._by = wy
            self._path_idx += 1
        else:
            self._bx += (dx/dist) * self.BOMB_SPEED
            self._by += (dy/dist) * self.BOMB_SPEED

        if psys and self.timer % 4 == 0:
            psys.spawn(self._bx, self._by, random.choice(BIT_COLORS),
                       count=1, speed=1.5, gravity=0, life=10, r=3, glow=True)

    def _trigger_explosion(self, owner, event_bus, psys):
        self._exploding = True
        self.has_hit    = False
        if psys:
            for col in BIT_COLORS + [(255,255,255)]:
                psys.spawn(self._bx, self._by, col,
                           count=14, speed=8, gravity=0.05, life=26, r=6, glow=True)

    def on_hit(self, owner, target, event_bus, psys=None, fsys=None):
        target.vel.x += owner.facing * 7
        target.vel.y -= 5
        super().on_hit(owner, target, event_bus, psys, fsys)

    def draw_front(self, owner, screen, camera, dr, bob, z):
        if not self._alive: return
        sx, sy = camera.world_to_screen(self._bx, self._by)

        if self._exploding:
            t = self._explode_t / 22
            for col, rr, aa in [(BIT_COLORS[0], int(36*(1+t*3)*z), 160),
                                  (BIT_COLORS[2], int(28*(1+t*2)*z), 200),
                                  ((255,255,255), int(18*(1+t)*z),   240)]:
                if rr < 2: continue
                es = pygame.Surface((rr*2+4,rr*2+4),pygame.SRCALPHA)
                pygame.draw.circle(es,(*col,_alpha(aa*(1-t))),(rr+2,rr+2),rr)
                screen.blit(es,(sx-rr-2,sy-rr-2))
            return

        r   = max(5, int(14*z))
        ang = math.radians(self._spin)

        # 경로 라인 (반투명)
        if self._path_idx < len(self._path):
            pts = [(self._bx, self._by)] + self._path[self._path_idx:]
            for i in range(len(pts)-1):
                p1x, p1y = camera.world_to_screen(pts[i][0], pts[i][1])
                p2x, p2y = camera.world_to_screen(pts[i+1][0], pts[i+1][1])
                pygame.draw.line(screen, (*BIT_COLORS[i%len(BIT_COLORS)], 60),
                                 (p1x,p1y), (p2x,p2y), max(1,int(2*z)))

        # 본체 (회전 정육각형)
        bs  = pygame.Surface((r*4,r*4),pygame.SRCALPHA)
        bc  = r*2
        pts2 = [(bc+int(r*1.2*math.cos(ang+k*math.pi/3)),
                 bc+int(r*1.2*math.sin(ang+k*math.pi/3)))
                for k in range(6)]
        pygame.draw.polygon(bs,(*BIT_COLORS[0],100),pts2)
        pygame.draw.polygon(bs,(*BIT_COLORS[0],220),pts2,max(2,int(3*z)))
        pygame.draw.circle(bs,(255,255,255,200),(bc,bc),max(2,r//4))
        # 깜빡이는 LED (계산 중)
        blink = int(pygame.time.get_ticks() * 0.008) % 2
        led_col = (80,235,190) if blink else (200,255,240)
        pygame.draw.circle(bs,led_col,(bc+r//2,bc-r//2),max(2,int(3*z)))
        screen.blit(bs,(sx-bc,sy-bc))


# ── 영역 궁 ──────────────────────────────────────────────────────────────────
class TuringDomain(DomainUltimateSkill):
    DISPLAY_NAME          = "Turing Domain"
    DESCRIPTION           = "Open Turing's universal machine domain."
    DOMAIN_BG_PATH        = "assets/images/charactor/Turing/Turing_domain.jpeg"
    DOMAIN_PARTICLE_COLOR = (80, 235, 190)
    BREAK_HITS            = 5
    CUTSCENE_FRAMES       = 30
    CUTSCENE_ZOOM         = 1.45
    TRANSITION_SPEED      = 0.055
    FREEZE_DURING_TRANSITION = True
    def __init__(self):
        super().__init__(name="Turing Domain", damage=0, duration=999999)


# ── 강화 Q: Turing Complete (완전한 계산 광선) ────────────────────────────────
class TuringComplete(_DomainOnlyMixin, Skill):
    """
    강화 Q — Turing Complete

    더 강하고 광역인 암호 펀치.
    - 피해 2배, 범위 1.8배
    - 명중 시 상대 모든 스킬 쿨타임 최대치로 강제 증가
    - 코드 폭발 이펙트 + 화면 전체에 암호 비
    """
    DISPLAY_NAME  = "Turing Complete"
    DESCRIPTION   = "Domain — Massive cipher punch.\nFully maxes all enemy skill cooldowns."
    COOLDOWN_SEC  = 6.0
    HIT_FRAME     = 6
    ATK_FRAMES    = 26

    def __init__(self):
        super().__init__("Turing Complete", damage=44, cooldown=360, duration=26)
        self.charge_value          = 0.0
        self.finisher_charge_value = 2.2
        self._code_burst = []

    def on_start(self, owner, event_bus=None, psys=None):
        self._code_burst = []
        if psys:
            for _ in range(14):
                ang = random.uniform(0, math.pi*2)
                psys.spawn(owner.rect.centerx + math.cos(ang)*40,
                           owner.rect.centery + math.sin(ang)*40,
                           random.choice(BIT_COLORS),
                           count=1, speed=random.uniform(4,9),
                           gravity=0, life=random.randint(14,24), r=random.randint(4,8), glow=True)

    def get_hitbox(self, owner):
        if not self.active: return None
        elapsed = self.duration - self.timer
        if elapsed < self.HIT_FRAME or elapsed > self.HIT_FRAME + 12:
            return None
        w = int(owner.rect.w * 3.2)
        h = int(owner.rect.h * 2.0)
        x = owner.rect.right - 10 if owner.facing == 1 else owner.rect.left - w + 10
        return pygame.Rect(x, owner.rect.centery - h//2, w, h)

    def on_update(self, owner, event_bus=None, psys=None):
        elapsed = self.duration - self.timer
        if elapsed == self.HIT_FRAME and psys:
            cx = owner.rect.centerx + owner.facing * int(owner.rect.w * 1.2)
            cy = owner.rect.centery
            for _ in range(32):
                ang = random.uniform(-math.pi*0.7, math.pi*0.7) + (0 if owner.facing==1 else math.pi)
                psys.spawn(cx+math.cos(ang)*15, cy+math.sin(ang)*15,
                           random.choice(BIT_COLORS),
                           count=1, speed=random.uniform(6,14),
                           gravity=0.12, life=random.randint(16,28), r=random.randint(4,8), glow=True)
        for c in self._code_burst:
            c["x"]+=c["vx"]; c["y"]+=c["vy"]
            c["vy"]+=0.3; c["vx"]*=0.9; c["life"]-=1
        self._code_burst = [c for c in self._code_burst if c["life"]>0]

    def on_hit(self, owner, target, event_bus, psys=None, fsys=None):
        # 모든 스킬 쿨타임 최대치로
        for sk in target.skills.values():
            if sk.cooldown:
                sk.current_cooldown = sk.cooldown
        target.vel.x = -target.vel.x * 0.5
        target.vel.y -= 5
        for _ in range(24):
            ang = random.uniform(0, math.pi*2)
            spd = random.uniform(5, 12)
            self._code_burst.append({
                "x": float(target.rect.centerx), "y": float(target.rect.centery),
                "vx": math.cos(ang)*spd, "vy": math.sin(ang)*spd-3,
                "char": random.choice(CODE_CHARS), "col": random.choice(BIT_COLORS),
                "life": random.randint(22,38), "max_life": 35,
            })
        if psys:
            psys.spawn(target.rect.centerx, target.rect.centery,
                       (80,235,190), count=28, speed=9, gravity=0.1, life=26, r=7, glow=True)
            psys.spawn(target.rect.centerx, target.rect.centery,
                       (255,255,255), count=12, speed=6, gravity=0, life=16, r=4, glow=True)
        super().on_hit(owner, target, event_bus, psys, fsys)

    def draw_front(self, owner, screen, camera, dr, bob, z):
        if self.active:
            elapsed = self.duration - self.timer
            if self.HIT_FRAME - 4 <= elapsed <= self.HIT_FRAME + 10:
                t2 = (elapsed-(self.HIT_FRAME-4)) / 14
                cx = dr.centerx + dr.w//2 * owner.facing
                cy = dr.centery + bob
                r2 = int(dr.w * 1.2 * z)
                alpha = _alpha(240 * (1-abs(t2*2-1)*0.4))
                for ri in range(4):
                    rr = int(r2*(t2*(1+ri*0.4)+0.15))
                    if rr < 2: continue
                    rs = pygame.Surface((rr*2+4,rr*2+4),pygame.SRCALPHA)
                    pygame.draw.circle(rs,
                        (*BIT_COLORS[ri%len(BIT_COLORS)], _alpha(alpha*(1-ri*0.2))),
                        (rr+2,rr+2), rr, max(2,int(4*z)))
                    screen.blit(rs,(cx-rr-2,cy-rr-2))
                fnt = pygame.font.SysFont(None, max(10,int(22*z)),bold=True)
                for i,char in enumerate(["HALT","NULL","ENCRYPT","!!"]):
                    ox2 = owner.facing*int((r2*0.5+i*r2*0.28)*t2)
                    oy2 = int(math.sin(i*1.5)*r2*0.6*t2)
                    cs  = fnt.render(char,True,BIT_COLORS[i%len(BIT_COLORS)])
                    cs.set_alpha(_alpha(alpha))
                    screen.blit(cs,(cx+ox2-cs.get_width()//2,cy+oy2-cs.get_height()//2))
        fnt2 = pygame.font.SysFont(None,max(8,int(14*z)),bold=True)
        for c in self._code_burst:
            cx2,cy2 = camera.world_to_screen(c["x"],c["y"])
            a = _alpha(200*c["life"]/c["max_life"])
            cs = fnt2.render(c["char"],True,c["col"]); cs.set_alpha(a)
            screen.blit(cs,(cx2-cs.get_width()//2,cy2-cs.get_height()//2))


class DecidabilityTrap(_DomainOnlyMixin, SummonZoneSkill):
    """
    영역 강화 E — 정지 문제.
    넓은 계산 격자로 상대를 완전히 가둔다.
    구역 안에서 상대 이동속도 거의 0에 수렴.
    탈출 시 폭발 피해.
    """
    DISPLAY_NAME = "Decidability Trap"
    DESCRIPTION  = "Domain — A massive grid that nearly halts all movement.\nExplodes on escape."
    WARN_FRAMES  = 18
    ZONE_W       = 480
    ZONE_H       = 360
    ZONE_COLOR   = (40, 180, 140)
    ZONE_GLOW    = (100, 255, 210)
    COOLDOWN_SEC = 11.0

    HALT_SLOW    = 0.40   # 이동속도 배율
    ESCAPE_DMG   = 22     # 탈출 시 피해

    def __init__(self):
        super().__init__("Decidability Trap", damage=18, cooldown=660, duration=160)
        self.charge_value          = 0.0
        self.finisher_charge_value = 2.5
        self._grid_t   = 0.0
        self._was_inside = False   # 이전 프레임 내부 여부

    def on_start(self, owner, event_bus=None, psys=None):
        self._zone_x = owner.rect.centerx + owner.facing * 260
        self._zone_y = owner.rect.centery
        self._grid_t   = 0.0
        self._was_inside = False
        self.has_hit     = False
        if psys:
            for _ in range(28):
                psys.spawn(self._zone_x + random.uniform(-200,200),
                           self._zone_y + random.uniform(-150,150),
                           random.choice(BIT_COLORS),
                           count=1, speed=random.uniform(2,6),
                           gravity=0, life=random.randint(18,30), r=random.randint(3,7), glow=True)

    def on_update(self, owner, event_bus=None, psys=None):
        self._grid_t += 0.05
        elapsed = self.duration - self.timer
        if elapsed < self.WARN_FRAMES: return

        target = getattr(owner, "_skill_target", None)
        zone   = self.get_hitbox(owner)
        if target and not target.dead:
            in_zone = bool(zone and zone.colliderect(target.rect))
            # 구역 안: 거의 정지
            if in_zone:
                target.vel.x *= self.HALT_SLOW
                target.vel.y *= 0.80
                self._was_inside = True
                if psys and self.timer % 8 == 0:
                    psys.spawn(target.rect.centerx, target.rect.top-8,
                               (80,235,190), count=3, speed=1.5, gravity=-0.04, life=12, r=3, glow=True)
            # 탈출 감지 → 폭발 피해
            elif self._was_inside and not in_zone:
                self._was_inside = False
                self.has_hit = False
                if event_bus:
                    event_bus.emit("attack_hit", {
                        "attacker": owner, "target": target,
                        "damage": self.ESCAPE_DMG, "is_skill": True,
                        "particle_system": psys, "floater_system": None,
                    })
                if psys:
                    psys.spawn(target.rect.centerx, target.rect.centery,
                               (80,235,190), count=18, speed=6, gravity=0, life=18, r=5, glow=True)

        if psys and self.timer % 5 == 0:
            cx = self._zone_x + random.uniform(-self.ZONE_W*0.42, self.ZONE_W*0.42)
            cy = self._zone_y + random.uniform(-self.ZONE_H*0.42, self.ZONE_H*0.42)
            psys.spawn(cx,cy,random.choice(BIT_COLORS),count=1,speed=0.8,gravity=0,life=14,r=3,glow=True)

    def get_hitbox(self, owner):
        if not self.active: return None
        elapsed = self.duration - self.timer
        if elapsed < self.WARN_FRAMES: return None
        return pygame.Rect(int(self._zone_x)-self.ZONE_W//2,
                           int(self._zone_y)-self.ZONE_H//2,
                           self.ZONE_W, self.ZONE_H)

    def on_hit(self, owner, target, event_bus, psys=None, fsys=None):
        if psys:
            psys.spawn(target.rect.centerx, target.rect.centery,
                       (80,235,190), count=20, speed=5, gravity=0, life=20, r=5, glow=True)
        super().on_hit(owner, target, event_bus, psys, fsys)

    def draw_behind(self, owner, screen, camera, dr, bob, z):
        if not self.active: return
        zx,zy   = int(self._zone_x), int(self._zone_y)
        sx,sy   = camera.world_to_screen(zx, zy)
        elapsed = self.duration - self.timer
        warn    = elapsed < self.WARN_FRAMES
        t       = self.timer / max(1, self.duration)
        alpha   = _alpha(80+120*abs(math.sin(elapsed*0.3))) if warn else _alpha(120*t)
        zw,zh   = int(self.ZONE_W*z), int(self.ZONE_H*z)
        tick    = pygame.time.get_ticks()

        # 배경
        bg = pygame.Surface((zw+8,zh+8),pygame.SRCALPHA)
        pygame.draw.rect(bg,(*self.ZONE_COLOR,_alpha(alpha*0.2)),(4,4,zw,zh),border_radius=8)
        pygame.draw.rect(bg,(*self.ZONE_GLOW,alpha),(4,4,zw,zh),max(2,int(3*z)),border_radius=8)
        screen.blit(bg,(sx-zw//2-4,sy-zh//2-4))

        # 격자 라인
        cols,rows = 10,8
        for c in range(cols+1):
            gx = sx-zw//2+int(c*zw/cols)
            a2 = _alpha(alpha*(0.25+0.35*abs(math.sin(self._grid_t+c*0.5))))
            pygame.draw.line(screen,(*BIT_COLORS[c%len(BIT_COLORS)],a2),
                             (gx,sy-zh//2),(gx,sy+zh//2),max(1,int(1*z)))
        for r2 in range(rows+1):
            gy = sy-zh//2+int(r2*zh/rows)
            a2 = _alpha(alpha*(0.25+0.35*abs(math.sin(self._grid_t+r2*0.7))))
            pygame.draw.line(screen,(*BIT_COLORS[r2%len(BIT_COLORS)],a2),
                             (sx-zw//2,gy),(sx+zw//2,gy),max(1,int(1*z)))

        # 격자 교차점 이진 문자
        fnt = pygame.font.SysFont(None, max(8,int(12*z)), bold=True)
        for ci in range(0,cols+1,2):
            for ri in range(0,rows+1,2):
                gx = sx-zw//2+int(ci*zw/cols)
                gy = sy-zh//2+int(ri*zh/rows)
                char = "1" if (ci+ri+int(self._grid_t*4))%2==0 else "0"
                csf  = fnt.render(char,True,BIT_COLORS[(ci+ri)%len(BIT_COLORS)])
                csf.set_alpha(_alpha(alpha*0.65))
                screen.blit(csf,(gx-csf.get_width()//2,gy-csf.get_height()//2))


# ── 캐릭터 ───────────────────────────────────────────────────────────────────
class Turing(Player):
    WEIGHT     = 96;  KB_GROWTH = 80;  BASE_KB   = 30
    WALK_SPEED = 6.5; JUMP_POWER = -15.5; MAX_JUMPS = 2
    ATTACK_DMG = 13;  ATK_FRAMES = 18;   ATK_CD    = 28
    HIT_START  = 3;   HIT_END    = 14

    BODY_COLOR    = (40, 180, 140);  TRIM_COLOR  = (20, 100, 80)
    GLOW_COLOR    = (80, 235, 190);  DARK_COLOR  = (15, 70, 55)
    DISPLAY_NAME  = "Turing"
    DESCRIPTION   = "Cipher breaker. Decrypt, track, and halt.\nDisrupt enemy skills."
    PREVIEW_COLOR = (40, 180, 140)

    SPRITE_PATH   = "assets/images/charactor/Turing/IDL.png"
    SPRITE_IDLE   = "assets/images/charactor/Turing/IDL.png"
    SPRITE_JUMP   = "assets/images/charactor/Turing/jump.png"
    SPRITE_ATTACK = "assets/images/charactor/Turing/attack.png"
    SPRITE_SKILL  = "assets/images/charactor/Turing/skill.png"
    SPRITE_SCALE  = 1.25; SPRITE_OFFSET_X = 0; SPRITE_OFFSET_Y = 6

    def __init__(self, x, y, name="Player", player_id=1):
        super().__init__(x, y, name, player_id)
        self.color = self.BODY_COLOR; self.trim_color = self.TRIM_COLOR
        self.glow_color = self.GLOW_COLOR; self.dark_color = self.DARK_COLOR
        self.max_jumps = self.MAX_JUMPS; self.attack_damage = self.ATTACK_DMG

    def _init_skills(self):
        self.skills["skill_Q"]        = CipherStrike()
        self.skills["skill_E"]        = BombeMachine()
        self.skills["skill_R"]        = TuringDomain()
        self.skills["skill_Q_domain"] = TuringComplete()
        self.skills["skill_E_domain"] = DecidabilityTrap()

    def get_char_name(self): return "Turing"