"""
Turing — 에니그마 해독기와 계산 가능성의 경계

일반 스킬:
  Q / ;  Enigma Bomb       — 암호 기어가 회전하는 폭탄 투척. 맞으면 암호 링 생성, 링 안 스킬 방해
  E / '  Halting Problem   — 정지 문제 격자 소환. 진입 시 0.5초 완전 경직 후 폭발

영역 전개 중:
  Q / ;  Colossus Bomb     — 콜로서스 에너지 폭탄. 대형 폭발 + 3회 연쇄 충격파
  E / '  Universal Machine — 전장 격자 전개. 상대의 모든 행동 계산 후 지속 피해 + 이동 제한
"""
from entities.player import Player
from systems.skill import Skill, SummonZoneSkill, ProjectileSkill, BeamSkill, DomainUltimateSkill
import pygame
import math
import random


class _DomainOnlyMixin:
    def can_activate(self, owner): return getattr(owner, "domain_active", False)

class _NormalOnlyMixin:
    def can_activate(self, owner): return not getattr(owner, "domain_active", False)

def _alpha(v): return max(0, min(255, int(v)))

BIT_COLORS  = [(80,235,190),(120,200,255),(60,160,140),(200,255,240)]
GEAR_COL    = (180,160,100)
CODE_CHARS  = ["0","1","{}","[]","//","()","&&","||","==","!=","NP","++","KEY","ENC"]


# ══════════════════════════════════════════════════════
#  Q — Enigma Bomb  (암호 기어 폭탄)
# ══════════════════════════════════════════════════════
class HackVirus(_NormalOnlyMixin, Skill):
    """
    튜링 Q — Hack Virus (바이러스 해킹)

    짧은 사거리의 전기 충격을 쏜다.
    명중 시 바이러스를 주입:
    - 즉각 피해
    - 3초간 상대 스킬 랜덤 1개 완전 봉인 (사용 불가)
    - 화면에 해킹 글리치 이펙트 (코드 파편 + 화면 노이즈)
    """
    DISPLAY_NAME  = "Hack Virus"
    DESCRIPTION   = "Inject a virus — deals damage and seals a random skill."
    COOLDOWN_SEC  = 4.5

    HIT_RANGE     = 240
    CHARGE_FRAMES = 10   # 선딜 (내부 카운터 기반)
    HIT_FRAMES    = 14
    SEAL_DURATION = 180  # 3초
    GLITCH_COUNT  = 18

    def __init__(self):
        # duration을 충분히 크게 — 내부 카운터로 단계 관리
        super().__init__("Hack Virus", damage=24, cooldown=270, duration=60)
        self.charge_value = 1.0
        self._frame       = 0   # 내부 프레임 카운터
        self._glitches    = []

    @property
    def _phase(self):
        if self._frame < self.CHARGE_FRAMES:
            return "charge"
        elif self._frame < self.CHARGE_FRAMES + self.HIT_FRAMES:
            return "hit"
        return "done"

    def on_start(self, owner, event_bus=None, psys=None):
        self._frame    = 0
        self._glitches = []
        self.has_hit   = False
        if psys:
            psys.spawn(owner.rect.centerx + owner.facing*20, owner.rect.centery,
                       (80,235,190), count=8, speed=3, gravity=0, life=10, r=4, glow=True)

    def get_hitbox(self, owner):
        if self._phase != "hit": return None
        w = self.HIT_RANGE
        h = int(owner.rect.h * 1.2)
        x = owner.rect.right - 8 if owner.facing == 1 else owner.rect.left - w + 8
        return pygame.Rect(x, owner.rect.centery - h//2, w, h)

    def on_update(self, owner, event_bus=None, psys=None):
        self._frame += 1

        # 글리치 파편
        for g in self._glitches:
            g["x"]+=g["vx"]; g["y"]+=g["vy"]
            g["vy"]+=0.2; g["vx"]*=0.94; g["life"]-=1
        self._glitches = [g for g in self._glitches if g["life"] > 0]

        phase = self._phase
        if phase == "charge":
            if psys and self._frame % 3 == 0:
                psys.spawn(owner.rect.centerx + owner.facing*random.randint(10,50),
                           owner.rect.centery + random.randint(-20,20),
                           random.choice(BIT_COLORS), count=1, speed=2, gravity=0, life=8, r=3, glow=True)

        elif phase == "hit":
            if psys and self._frame % 2 == 0:
                cx = owner.rect.centerx + owner.facing * int(self.HIT_RANGE*0.6)
                cy = owner.rect.centery + random.randint(-30,30)
                psys.spawn(cx, cy, random.choice(BIT_COLORS),
                           count=2, speed=3, gravity=0, life=8, r=3, glow=True)

    def on_hit(self, owner, target, event_bus, psys=None, fsys=None):
        self._hitting = False

        # 랜덤 스킬 봉인
        sealable = [k for k,s in target.skills.items()
                    if "domain" not in k and k != "skill_R"
                    and not getattr(s, "_hacked", False)]
        if sealable:
            seal_key = random.choice(sealable)
            sk = target.skills[seal_key]
            sk._hacked       = True
            sk._hack_timer   = self.SEAL_DURATION
            sk.current_cooldown = max(sk.current_cooldown, self.SEAL_DURATION)

        # 넉백
        target.vel.x = owner.facing * 8
        target.vel.y = -4

        # 글리치 파편 폭발
        for _ in range(self.GLITCH_COUNT):
            ang = random.uniform(0, math.pi*2)
            spd = random.uniform(4, 11)
            self._glitches.append({
                "x": float(target.rect.centerx),
                "y": float(target.rect.centery),
                "vx": math.cos(ang)*spd, "vy": math.sin(ang)*spd - 2,
                "char": random.choice(CODE_CHARS),
                "col": random.choice(BIT_COLORS),
                "life": random.randint(20,38), "max_life": 32,
            })

        if psys:
            psys.spawn(target.rect.centerx, target.rect.centery,
                       (80,235,190), count=22, speed=7, gravity=0.1, life=20, r=5, glow=True)
            psys.spawn(target.rect.centerx, target.rect.centery,
                       (255,255,255), count=10, speed=5, gravity=0, life=12, r=3, glow=True)

        if event_bus:
            event_bus.emit("attack_hit", {"attacker":owner,"target":target,
                "damage":self.damage,"is_skill":True,
                "particle_system":psys,"floater_system":None})

    def draw_front(self, owner, screen, camera, dr, bob, z):
        tick = pygame.time.get_ticks()

        # 전기 방전 빔
        if self._phase == "hit":
            t_prog = (self._frame - self.CHARGE_FRAMES) / self.HIT_FRAMES
            sx  = dr.right - 8 if owner.facing==1 else dr.left + 8
            sy  = dr.centery + bob
            ex  = sx + owner.facing * int(self.HIT_RANGE * z)
            length = int(self.HIT_RANGE * z)

            # 지글재글 전기선 3중
            for ray in range(3):
                pts = [(sx, sy)]
                steps = 14
                for i in range(1, steps+1):
                    px = sx + owner.facing * int(length * i/steps)
                    py = sy + int(math.sin(i*1.3 + tick*0.02 + ray*1.0) * 14*z)
                    pts.append((px, py))
                if len(pts) > 1:
                    col = BIT_COLORS[ray % len(BIT_COLORS)]
                    pygame.draw.lines(screen, (*col, _alpha(180 - ray*40)),
                                      False, pts, max(1,int((3-ray)*z)))

            # 임팩트 원
            rs = pygame.Surface((int(40*z)+8,int(40*z)+8),pygame.SRCALPHA)
            rr = int(20*z)
            pygame.draw.circle(rs,(80,235,190,_alpha(160*(1-t_prog))),(rr+4,rr+4),rr)
            screen.blit(rs,(ex-rr-4,sy-rr-4))

        # 차지 원
        elif self._phase == "charge":
            t_ch = self._frame / self.CHARGE_FRAMES
            r2   = max(4, int(18*t_ch*z))
            cs   = pygame.Surface((r2*2+8,r2*2+8),pygame.SRCALPHA)
            pygame.draw.circle(cs,(80,235,190,_alpha(160*t_ch)),(r2+4,r2+4),r2,max(1,int(2*z)))
            screen.blit(cs,(dr.centerx+owner.facing*30-r2-4, dr.centery+bob-r2-4))

        # 글리치 파편 (코드 텍스트)
        fnt = pygame.font.SysFont(None, max(8,int(13*z)), bold=True)
        for g in self._glitches:
            gsx,gsy = camera.world_to_screen(g["x"],g["y"])
            a = _alpha(200*g["life"]/g["max_life"])
            cs = fnt.render(g["char"], True, g["col"])
            cs.set_alpha(a)
            screen.blit(cs,(gsx-cs.get_width()//2,gsy-cs.get_height()//2))


class HaltingProblem(_NormalOnlyMixin, SummonZoneSkill):
    """
    전방에 정지 문제 격자를 소환.
    경고(1초) 후 격자 활성화.
    상대가 격자에 닿는 순간 0.5초 완전 경직(정지).
    경직 해제 후 폭발 피해.
    """
    DISPLAY_NAME  = "Halting Problem"
    DESCRIPTION   = "Summon a halt grid — enemy freezes on contact.\\nThen explodes."
    WARN_FRAMES   = 40
    ZONE_W        = 160
    ZONE_H        = 200
    ZONE_COLOR    = (60, 200, 160)
    ZONE_GLOW     = (120, 255, 210)
    COOLDOWN_SEC  = 8.0

    FREEZE_FRAMES = 30   # 0.5초 경직
    EXPLODE_DMG   = 36

    def __init__(self):
        super().__init__("Halting Problem", damage=0, cooldown=480, duration=140)
        self.charge_value = 1.3
        self._phase       = 0.0
        self._frozen      = False   # 상대가 경직 중인가
        self._freeze_timer = 0
        self._freeze_target = None
        self._exploded    = False

    def on_start(self, owner, event_bus=None, psys=None):
        target = getattr(owner, "_skill_target", None)
        if target and not target.dead and abs(target.rect.centerx-owner.rect.centerx) < 380:
            self._zone_x = target.rect.centerx
        else:
            self._zone_x = owner.rect.centerx + owner.facing * 220
        self._zone_y      = owner.rect.centery
        self._phase       = random.uniform(0, math.pi*2)
        self._frozen      = False
        self._freeze_timer = 0
        self._freeze_target = None
        self._exploded    = False
        self.has_hit      = False
        if psys:
            for _ in range(16):
                psys.spawn(self._zone_x + random.uniform(-60,60),
                           self._zone_y + random.uniform(-80,80),
                           random.choice(BIT_COLORS), count=1, speed=3,
                           gravity=0, life=16, r=4, glow=True)

    def on_update(self, owner, event_bus=None, psys=None):
        elapsed = self.duration - self.timer

        # 경직 처리
        if self._frozen and self._freeze_target:
            self._freeze_timer -= 1
            t = self._freeze_target
            t.vel.x = 0; t.vel.y = 0   # 완전 정지
            if self._freeze_timer <= 0:
                self._frozen = False
                if not self._exploded:
                    self._exploded = True
                    self.has_hit   = False
                    if event_bus:
                        event_bus.emit("attack_hit",{"attacker":owner,"target":t,
                            "damage":self.EXPLODE_DMG,"is_skill":True,
                            "particle_system":psys,"floater_system":None})
                    t.vel.x = owner.facing * 14
                    t.vel.y = -10
                    if psys:
                        for col in BIT_COLORS+[(255,255,255)]:
                            psys.spawn(t.rect.centerx, t.rect.centery, col,
                                       count=16, speed=8, gravity=-0.03, life=24, r=6, glow=True)
            return

        if elapsed <= self.WARN_FRAMES: return

        # 격자 활성 - 진입 감지
        target = getattr(owner, "_skill_target", None)
        zone   = self.get_hitbox(owner)
        if target and not target.dead and zone and zone.colliderect(target.rect) and not self._frozen:
            self._frozen        = True
            self._freeze_timer  = self.FREEZE_FRAMES
            self._freeze_target = target
            if psys:
                psys.spawn(target.rect.centerx, target.rect.centery,
                           (120,255,210), count=18, speed=5, gravity=0, life=18, r=5, glow=True)

        if psys and self.timer % 6 == 0:
            cx = self._zone_x + random.uniform(-self.ZONE_W*0.45, self.ZONE_W*0.45)
            cy = self._zone_y + random.uniform(-self.ZONE_H*0.45, self.ZONE_H*0.45)
            psys.spawn(cx, cy, random.choice(BIT_COLORS), count=1, speed=0.8, gravity=0, life=12, r=3, glow=True)

    def get_hitbox(self, owner):
        if not self.active: return None
        elapsed = self.duration - self.timer
        if elapsed < self.WARN_FRAMES: return None
        return pygame.Rect(int(self._zone_x)-self.ZONE_W//2,
                           int(self._zone_y)-self.ZONE_H//2,
                           self.ZONE_W, self.ZONE_H)

    def on_hit(self, owner, target, event_bus, psys=None, fsys=None):
        pass  # on_update에서 직접 처리

    def draw_behind(self, owner, screen, camera, dr, bob, z):
        if not self.active: return
        sx, sy = camera.world_to_screen(int(self._zone_x), int(self._zone_y))
        elapsed = self.duration - self.timer
        warn    = elapsed < self.WARN_FRAMES
        t       = self.timer / max(1, self.duration)
        alpha   = _alpha(80+130*abs(math.sin(elapsed*0.25))) if warn else _alpha(130*t)
        zw, zh  = int(self.ZONE_W*z), int(self.ZONE_H*z)
        tick    = pygame.time.get_ticks()

        # 배경
        bg = pygame.Surface((zw+8, zh+8), pygame.SRCALPHA)
        pygame.draw.rect(bg,(*self.ZONE_COLOR,_alpha(alpha*0.2)),(4,4,zw,zh),border_radius=4)
        pygame.draw.rect(bg,(*self.ZONE_GLOW,alpha),(4,4,zw,zh),max(2,int(3*z)),border_radius=4)
        screen.blit(bg,(sx-zw//2-4,sy-zh//2-4))

        # 격자
        cols, rows = 6, 8
        for c in range(cols+1):
            gx = sx-zw//2+int(c*zw/cols)
            a2 = _alpha(alpha*(0.3+0.3*abs(math.sin(tick*0.004+c*0.6))))
            pygame.draw.line(screen,(*BIT_COLORS[c%len(BIT_COLORS)],a2),
                             (gx,sy-zh//2),(gx,sy+zh//2),max(1,int(1*z)))
        for r2 in range(rows+1):
            gy = sy-zh//2+int(r2*zh/rows)
            a2 = _alpha(alpha*(0.3+0.3*abs(math.sin(tick*0.004+r2*0.8))))
            pygame.draw.line(screen,(*BIT_COLORS[r2%len(BIT_COLORS)],a2),
                             (sx-zw//2,gy),(sx+zw//2,gy),max(1,int(1*z)))

        # HALT 텍스트
        fnt = pygame.font.SysFont(None,max(10,int(16*z)),bold=True)
        lbl = fnt.render("HALT?",True,(120,255,210))
        lbl.set_alpha(_alpha(alpha)); screen.blit(lbl,(sx-lbl.get_width()//2,sy-lbl.get_height()//2))

        # 경직 중 강조
        if self._frozen and self._freeze_target:
            tx2,ty2 = camera.world_to_screen(self._freeze_target.rect.centerx,
                                             self._freeze_target.rect.centery)
            fr = max(4,int(28*z))
            fs = pygame.Surface((fr*2+8,fr*2+8),pygame.SRCALPHA)
            pulse = abs(math.sin(tick*0.015))
            pygame.draw.rect(fs,(*self.ZONE_GLOW,_alpha(200*(0.5+0.5*pulse))),
                             (0,0,fr*2+8,fr*2+8),max(2,int(3*z)))
            screen.blit(fs,(tx2-fr-4,ty2-fr-4))
            fl = fnt.render("HALTED",True,(120,255,210))
            fl.set_alpha(_alpha(200)); screen.blit(fl,(tx2-fl.get_width()//2,ty2-fr-24))


# ══════════════════════════════════════════════════════
#  영역 궁
# ══════════════════════════════════════════════════════
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


# ══════════════════════════════════════════════════════
#  강화 Q — Colossus Bomb  (콜로서스 연쇄 폭탄)
# ══════════════════════════════════════════════════════
class DecryptionBlitz(_DomainOnlyMixin, Skill):
    """
    강화 Q — Decryption Blitz

    콜로서스(튜링의 해독 기계) 에너지로 강화된 분석 돌진.
    일반 Q보다:
    - 3배 더 빠른 돌진
    - 명중 시 모든 스킬 봉인 (랜덤 1개가 아닌 전부)
    - 봉인 지속 5초
    - 돌진 후 자리에 폭발 발생
    """
    DISPLAY_NAME  = "Decryption Blitz"
    DESCRIPTION   = "Domain — Blitz dash seals ALL enemy skills.\nExplosion on impact."
    COOLDOWN_SEC  = 7.0

    DASH_SPEED    = 32.0
    DASH_FRAMES   = 8
    SEAL_DURATION = 300   # 5초

    def __init__(self):
        super().__init__("Decryption Blitz", damage=42, cooldown=420, duration=26)
        self.charge_value          = 0.0
        self.finisher_charge_value = 2.0
        self._dashing   = True
        self._dash_timer = 0
        self._exp_x      = 0.0
        self._exp_y      = 0.0
        self._exploding  = False
        self._exp_t      = 0

    def on_start(self, owner, event_bus=None, psys=None):
        self._dashing    = True
        self._dash_timer = 0
        self._exploding  = False
        self._exp_t      = 0
        self.has_hit     = False
        target = getattr(owner, "_skill_target", None)
        if target and not target.dead:
            dx = target.rect.centerx - owner.rect.centerx
            dy = target.rect.centery  - owner.rect.centery
            dist = max(1, math.sqrt(dx*dx+dy*dy))
            owner.vel.x = (dx/dist) * self.DASH_SPEED
            owner.vel.y = (dy/dist) * self.DASH_SPEED * 0.4
        else:
            owner.vel.x = owner.facing * self.DASH_SPEED
        owner.invincible = self.DASH_FRAMES + 6
        if psys:
            for _ in range(18):
                ang = random.uniform(0, math.pi*2)
                psys.spawn(owner.rect.centerx+math.cos(ang)*30,
                           owner.rect.centery+math.sin(ang)*30,
                           random.choice(BIT_COLORS+[GEAR_COL]),
                           count=1, speed=random.uniform(4,10),
                           gravity=0, life=random.randint(14,24), r=random.randint(4,8), glow=True)

    def get_hitbox(self, owner):
        if not self._dashing: return None
        w = int(owner.rect.w * 2.4)
        h = int(owner.rect.h * 1.8)
        x = owner.rect.right-10 if owner.facing==1 else owner.rect.left-w+10
        return pygame.Rect(x, owner.rect.centery-h//2, w, h)

    def on_update(self, owner, event_bus=None, psys=None):
        if self._dashing:
            self._dash_timer += 1
            if self._dash_timer >= self.DASH_FRAMES:
                self._dashing = False
                owner.vel.x *= 0.15; owner.vel.y *= 0.15
            if psys and self._dash_timer % 2 == 0:
                psys.spawn(owner.rect.centerx-owner.vel.x*2,
                           owner.rect.centery-owner.vel.y*2,
                           random.choice(BIT_COLORS), count=3, speed=3, gravity=0, life=8, r=5, glow=True)
        if self._exploding:
            self._exp_t += 1
            if self._exp_t > 20: self._exploding = False

    def on_hit(self, owner, target, event_bus, psys=None, fsys=None):
        self._dashing    = False
        self._exploding  = True
        self._exp_t      = 0
        self._exp_x      = float(target.rect.centerx)
        self._exp_y      = float(target.rect.centery)
        owner.vel.x *= 0.15; owner.vel.y *= 0.15

        # 모든 스킬 봉인
        for k,s in target.skills.items():
            if "domain" not in k and k != "skill_R":
                s._sealed       = True
                s._seal_timer   = self.SEAL_DURATION
                s.current_cooldown = max(s.current_cooldown, self.SEAL_DURATION)

        target.vel.x = owner.facing * 16; target.vel.y = -9

        if psys:
            for col in BIT_COLORS+[GEAR_COL,(255,255,255)]:
                psys.spawn(target.rect.centerx, target.rect.centery,
                           col, count=20, speed=11, gravity=0.05, life=28, r=8, glow=True)
        if event_bus:
            event_bus.emit("attack_hit",{"attacker":owner,"target":target,
                "damage":self.damage,"is_skill":True,"particle_system":psys,"floater_system":None})

    def draw_front(self, owner, screen, camera, dr, bob, z):
        if self._dashing:
            for i in range(5):
                ax = dr.centerx - int(owner.vel.x*(i+1)*0.25)
                ay = dr.centery - int(owner.vel.y*(i+1)*0.25) + bob
                tr = pygame.Surface((dr.w,dr.h),pygame.SRCALPHA)
                pygame.draw.rect(tr,(*BIT_COLORS[i%len(BIT_COLORS)],_alpha(100-i*18)),(0,0,dr.w,dr.h),border_radius=6)
                screen.blit(tr,(ax-dr.w//2,ay-dr.h//2))

        if self._exploding:
            t = self._exp_t / 20
            esx,esy = camera.world_to_screen(int(self._exp_x),int(self._exp_y))
            for col,rr,aa in [(GEAR_COL,int(60*(1+t*3)*z),150),
                               (BIT_COLORS[0],int(40*(1+t*2)*z),200),
                               ((255,255,255),int(24*(1+t)*z),250)]:
                if rr<2: continue
                es = pygame.Surface((rr*2+4,rr*2+4),pygame.SRCALPHA)
                pygame.draw.circle(es,(*col,_alpha(aa*(1-t))),(rr+2,rr+2),rr)
                screen.blit(es,(esx-rr-2,esy-rr-2))


class UniversalMachine(_DomainOnlyMixin, SummonZoneSkill):
    """
    전장 전체에 계산 격자를 전개.
    상대의 위치를 매 10f마다 '계산'하여:
    - 격자 내 이동 제한 (이동속도 50%)
    - 계산 완료 시 해당 위치로 에너지 수렴 피해
    - 특수: 상대가 이동할수록 '계산 횟수' 증가 → 후반에 더 강한 수렴
    5초 지속, 최대 6회 계산.
    """
    DISPLAY_NAME  = "Universal Machine"
    DESCRIPTION   = "Domain — Compute the enemy's every move.\\nMore they move, more they suffer."
    WARN_FRAMES   = 20
    ZONE_W        = 700
    ZONE_H        = 500
    ZONE_COLOR    = (40, 180, 140)
    ZONE_GLOW     = (100, 255, 210)
    COOLDOWN_SEC  = 14.0   # 쿨타임 증가 (기존 12초)

    CALC_INTERVAL  = 70    # 계산 간격 프레임 (기존 50 → 70)
    MAX_CALCS      = 4     # 최대 4회 (기존 6)
    BASE_CALC_DMG  = 7     # 기본 피해 (기존 10)
    MOVE_SLOW      = 0.65  # 이동속도 배율 (기존 0.50, 덜 강하게)

    def __init__(self):
        super().__init__("Universal Machine", damage=0, cooldown=720, duration=320)
        self.charge_value          = 0.0
        self.finisher_charge_value = 3.0
        self._phase       = 0.0
        self._grid_t      = 0.0
        self._calc_timer  = 0
        self._calc_count  = 0
        self._calc_targets= []   # [(sx,sy, timer)] 수렴 이펙트
        self._last_target_pos = None
        self._move_count  = 0    # 상대가 얼마나 이동했는지

    def on_start(self, owner, event_bus=None, psys=None):
        self._zone_x      = owner.rect.centerx
        self._zone_y      = owner.rect.centery
        self._phase       = random.uniform(0,math.pi*2)
        self._grid_t      = 0.0
        self._calc_timer  = 0
        self._calc_count  = 0
        self._calc_targets= []
        self._move_count  = 0
        self._last_target_pos = None
        self.has_hit      = False
        if psys:
            for _ in range(32):
                psys.spawn(self._zone_x+random.uniform(-300,300),
                           self._zone_y+random.uniform(-200,200),
                           random.choice(BIT_COLORS),
                           count=1, speed=random.uniform(2,6),
                           gravity=0, life=random.randint(20,36), r=random.randint(3,8), glow=True)

    def on_update(self, owner, event_bus=None, psys=None):
        self._grid_t += 0.04
        elapsed = self.duration - self.timer
        if elapsed < self.WARN_FRAMES: return

        target = getattr(owner, "_skill_target", None)
        zone   = self.get_hitbox(owner)

        if target and not target.dead:
            # 이동 감지
            cur_pos = (target.rect.centerx, target.rect.centery)
            if self._last_target_pos:
                dx = cur_pos[0]-self._last_target_pos[0]
                dy = cur_pos[1]-self._last_target_pos[1]
                if abs(dx)+abs(dy) > 8:
                    self._move_count += 1
            self._last_target_pos = cur_pos

            # 이동 제한
            if zone and zone.colliderect(target.rect):
                target.vel.x *= self.MOVE_SLOW

            # 계산 타이밍
            self._calc_timer += 1
            if self._calc_timer >= self.CALC_INTERVAL and self._calc_count < self.MAX_CALCS:
                self._calc_timer  = 0
                self._calc_count += 1
                # 이동 누적에 따라 피해 증가
                bonus = min(self._move_count // 15, 2)   # 이동 누적 보너스 약화
                dmg   = self.BASE_CALC_DMG + self._calc_count * 3 + bonus * 3
                self._calc_targets.append({
                    "tx": float(target.rect.centerx),
                    "ty": float(target.rect.centery),
                    "timer": 20, "dmg": dmg,
                })
                self._move_count = max(0, self._move_count - 8)
                if psys:
                    psys.spawn(target.rect.centerx, target.rect.centery,
                               (120,255,210), count=12, speed=5, gravity=0, life=18, r=5, glow=True)

        # 수렴 이펙트 처리
        for ct in self._calc_targets:
            ct["timer"] -= 1
            if ct["timer"] == 0 and target and not target.dead and event_bus:
                event_bus.emit("attack_hit",{"attacker":owner,"target":target,
                    "damage":ct["dmg"],"is_skill":True,"particle_system":psys,"floater_system":None})
                if psys:
                    psys.spawn(ct["tx"],ct["ty"],random.choice(BIT_COLORS),
                               count=14,speed=7,gravity=0,life=20,r=6,glow=True)
        self._calc_targets = [ct for ct in self._calc_targets if ct["timer"] > 0]

        if psys and self.timer % 4 == 0:
            cx = self._zone_x+random.uniform(-self.ZONE_W*0.45,self.ZONE_W*0.45)
            cy = self._zone_y+random.uniform(-self.ZONE_H*0.45,self.ZONE_H*0.45)
            psys.spawn(cx,cy,random.choice(BIT_COLORS),count=1,speed=0.6,gravity=0,life=14,r=3,glow=True)

    def get_hitbox(self, owner):
        if not self.active: return None
        elapsed = self.duration - self.timer
        if elapsed < self.WARN_FRAMES: return None
        return pygame.Rect(int(self._zone_x)-self.ZONE_W//2,
                           int(self._zone_y)-self.ZONE_H//2,
                           self.ZONE_W, self.ZONE_H)

    def on_hit(self, owner, target, event_bus, psys=None, fsys=None): pass

    def draw_behind(self, owner, screen, camera, dr, bob, z):
        if not self.active: return
        sx,sy   = camera.world_to_screen(int(self._zone_x), int(self._zone_y))
        elapsed = self.duration - self.timer
        warn    = elapsed < self.WARN_FRAMES
        t       = self.timer / max(1, self.duration)
        alpha   = _alpha(60+110*abs(math.sin(elapsed*0.25))) if warn else _alpha(100*t)
        zw,zh   = int(self.ZONE_W*z), int(self.ZONE_H*z)
        tick    = pygame.time.get_ticks()

        # 배경
        bg = pygame.Surface((zw+8,zh+8),pygame.SRCALPHA)
        pygame.draw.rect(bg,(*self.ZONE_COLOR,_alpha(alpha*0.18)),(4,4,zw,zh),border_radius=6)
        pygame.draw.rect(bg,(*self.ZONE_GLOW,_alpha(alpha*0.7)),(4,4,zw,zh),max(2,int(3*z)),border_radius=6)
        screen.blit(bg,(sx-zw//2-4,sy-zh//2-4))

        # 격자
        cols,rows = 12,9
        for c in range(cols+1):
            gx = sx-zw//2+int(c*zw/cols)
            a2 = _alpha(alpha*(0.22+0.28*abs(math.sin(self._grid_t+c*0.5))))
            pygame.draw.line(screen,(*BIT_COLORS[c%len(BIT_COLORS)],a2),
                             (gx,sy-zh//2),(gx,sy+zh//2),max(1,int(1*z)))
        for r2 in range(rows+1):
            gy = sy-zh//2+int(r2*zh/rows)
            a2 = _alpha(alpha*(0.22+0.28*abs(math.sin(self._grid_t+r2*0.7))))
            pygame.draw.line(screen,(*BIT_COLORS[r2%len(BIT_COLORS)],a2),
                             (sx-zw//2,gy),(sx+zw//2,gy),max(1,int(1*z)))

        # 계산 카운터
        from systems.font_manager import font as _fnt
        fnt = _fnt(max(10,int(14*z)),bold=True)
        calc_lbl = fnt.render(f"CALC {self._calc_count}/{self.MAX_CALCS}", True, (120,255,210))
        calc_lbl.set_alpha(_alpha(alpha*1.2))
        screen.blit(calc_lbl,(sx-calc_lbl.get_width()//2,sy-zh//2-22))

        # 이동 누적 표시
        if self._move_count > 0:
            mv_lbl = fnt.render(f"MOVE ×{min(self._move_count,99)}", True, (255,200,80))
            mv_lbl.set_alpha(_alpha(alpha))
            screen.blit(mv_lbl,(sx-mv_lbl.get_width()//2,sy-zh//2-40))

        # 수렴 이펙트
        for ct in self._calc_targets:
            ctx,cty = camera.world_to_screen(ct["tx"],ct["ty"])
            ct_t    = 1 - ct["timer"]/20
            r2      = int(60*z*ct_t)
            if r2 < 2: continue
            rs = pygame.Surface((r2*2+8,r2*2+8),pygame.SRCALPHA)
            pygame.draw.circle(rs,(120,255,210,_alpha(200*(1-ct_t))),(r2+4,r2+4),r2,max(2,int(4*z)))
            screen.blit(rs,(ctx-r2-4,cty-r2-4))


# ══════════════════════════════════════════════════════
#  캐릭터
# ══════════════════════════════════════════════════════
class Turing(Player):
    WEIGHT     = 96;  KB_GROWTH = 80;  BASE_KB   = 30
    WALK_SPEED = 6.5; JUMP_POWER = -15.5; MAX_JUMPS = 2
    ATTACK_DMG = 13;  ATK_FRAMES = 18;   ATK_CD    = 28
    HIT_START  = 3;   HIT_END    = 14

    BODY_COLOR    = (40, 180, 140);  TRIM_COLOR  = (20, 100, 80)
    GLOW_COLOR    = (80, 235, 190);  DARK_COLOR  = (15, 70, 55)
    DISPLAY_NAME  = "Turing"
    DESCRIPTION   = "Cipher master. Enigma bombs, halt grids.\\nDisrupt and compute."
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
        self.skills["skill_Q"]        = HackVirus()
        self.skills["skill_E"]        = HaltingProblem()
        self.skills["skill_R"]        = TuringDomain()
        self.skills["skill_Q_domain"] = DecryptionBlitz()
        self.skills["skill_E_domain"] = UniversalMachine()

    def get_char_name(self): return "Turing"