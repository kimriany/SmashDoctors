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
class EnigmaDecrypt(_NormalOnlyMixin, BeamSkill):
    """
    전방에 암호 해독 빔 발사.
    명중 시:
    - 상대 스킬 쿨타임 최대 +90프레임 강제 증가 (디버프)
    - 코드 파편이 흩어지는 이펙트
    """
    DISPLAY_NAME = "Enigma Decrypt"
    DESCRIPTION  = "Fire a cipher beam.\nHit enemy's skill cooldowns are extended."
    BEAM_LENGTH  = 340
    BEAM_WIDTH   = 22
    BEAM_COLOR   = (80, 235, 190)
    BEAM_GLOW    = (180, 255, 230)
    COOLDOWN_SEC = 5.0

    CD_PENALTY   = 90   # 쿨타임 증가 프레임

    def __init__(self):
        super().__init__("Enigma Decrypt", damage=20, cooldown=300, duration=24)
        self.charge_value = 1.1
        self._code_sparks = []   # 코드 파편 이펙트

    def on_hit(self, owner, target, event_bus, psys=None, fsys=None):
        # 상대 스킬 쿨타임 강제 증가
        for sk in target.skills.values():
            if sk.current_cooldown > 0:
                sk.current_cooldown = min(sk.cooldown, sk.current_cooldown + self.CD_PENALTY)
        target.vel.x += owner.facing * 5
        if psys:
            for _ in range(20):
                ang = random.uniform(0, math.pi * 2)
                psys.spawn(target.rect.centerx + math.cos(ang)*20,
                           target.rect.centery + math.sin(ang)*20,
                           random.choice(BIT_COLORS),
                           count=1, speed=random.uniform(4,9),
                           gravity=0.05, life=random.randint(14,26), r=random.randint(3,6), glow=True)
        super().on_hit(owner, target, event_bus, psys, fsys)

    def draw_front(self, owner, screen, camera, dr, bob, z):
        if not self.active: return
        t     = self.timer / max(1, self.duration)
        alpha = _alpha(220 * t)
        length = int(self.BEAM_LENGTH * z)
        bw    = max(int(4*z), int(self.BEAM_WIDTH * t * z))
        sx    = dr.right - int(6*z) if owner.facing == 1 else dr.left - length + int(6*z)
        by    = dr.centery + bob - bw//2
        tick  = pygame.time.get_ticks()

        # 메인 빔
        bs = pygame.Surface((length, bw+16), pygame.SRCALPHA)
        pygame.draw.rect(bs, (*self.BEAM_COLOR, alpha), (0, 8, length, bw), border_radius=int(4*z))
        pygame.draw.rect(bs, (*self.BEAM_GLOW, _alpha(alpha*0.4)), (0, 4, length, bw+8), border_radius=int(6*z))
        # 중앙 흰 줄기
        pygame.draw.rect(bs, (255,255,255,_alpha(alpha*0.7)),
                         (0, 8+bw//2-int(2*z), length, int(3*z)))

        # 코드 스트림 (빔 위에 흐르는 이진 문자)
        fnt = pygame.font.SysFont(None, max(8, int(14*z)), bold=True)
        char_spacing = max(12, int(28*z))
        for i in range(length // char_spacing):
            cx2 = i * char_spacing + int((tick * 0.15) % char_spacing)
            char = CODE_CHARS[(i + int(tick*0.02)) % len(CODE_CHARS)]
            cs  = fnt.render(char, True, (200, 255, 240))
            cs.set_alpha(_alpha(alpha * 0.55))
            bs.blit(cs, (cx2, 1))

        screen.blit(bs, (sx, by))


# ── E: Bombe Machine (자동 추적 폭탄) ───────────────────────────────────────
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
class TuringComplete(_DomainOnlyMixin, BeamSkill):
    """
    영역 강화 Q — 완전한 계산.
    다단히트 빔 + 명중 시 상대 스킬 쿨타임 완전 리셋(최대로 증가)
    """
    DISPLAY_NAME = "Turing Complete"
    DESCRIPTION  = "Domain — Multi-hit beam.\nFully resets all enemy skill cooldowns."
    BEAM_LENGTH  = 440
    BEAM_WIDTH   = 34
    BEAM_COLOR   = (40, 200, 150)
    BEAM_GLOW    = (100, 255, 210)
    COOLDOWN_SEC = 7.0
    MULTI_HITS   = 4
    HIT_INTERVAL = 5

    def __init__(self):
        super().__init__("Turing Complete", damage=18, cooldown=420, duration=32)
        self.charge_value          = 0.0
        self.finisher_charge_value = 2.0
        self._hit_count  = 0
        self._hit_timer  = 0

    def on_update(self, owner, event_bus=None, psys=None):
        self._hit_timer += 1
        if self._hit_timer >= self.HIT_INTERVAL and self._hit_count < self.MULTI_HITS:
            self._hit_timer  = 0
            self._hit_count += 1
            self.has_hit     = False   # 다단 히트

    def on_hit(self, owner, target, event_bus, psys=None, fsys=None):
        # 마지막 히트에서 쿨타임 완전 리셋
        if self._hit_count >= self.MULTI_HITS:
            for sk in target.skills.values():
                if sk.cooldown:
                    sk.current_cooldown = sk.cooldown
        if psys:
            psys.spawn(target.rect.centerx, target.rect.centery,
                       (80,235,190), count=16, speed=6, gravity=0, life=20, r=5, glow=True)
        super().on_hit(owner, target, event_bus, psys, fsys)

    def draw_front(self, owner, screen, camera, dr, bob, z):
        if not self.active: return
        t     = self.timer / max(1, self.duration)
        alpha = _alpha(220 * t)
        length = int(self.BEAM_LENGTH * z)
        bw    = max(int(6*z), int(self.BEAM_WIDTH * t * z))
        sx    = dr.right - int(6*z) if owner.facing == 1 else dr.left - length + int(6*z)
        by    = dr.centery + bob - bw//2
        tick  = pygame.time.get_ticks()

        bs = pygame.Surface((length, bw+20), pygame.SRCALPHA)
        # 메인 빔
        pygame.draw.rect(bs,(*self.BEAM_COLOR,alpha),(0,10,length,bw),border_radius=int(5*z))
        pygame.draw.rect(bs,(*self.BEAM_GLOW,_alpha(alpha*0.4)),(0,5,length,bw+10),border_radius=int(7*z))
        # 다단히트 펄스 링
        pulse_x = int((tick * 0.3) % length)
        ps2 = pygame.Surface((bw*3+8, bw*3+8), pygame.SRCALPHA)
        pygame.draw.circle(ps2,(*self.BEAM_GLOW,_alpha(alpha*0.6)),
                           (bw*3//2+4,bw*3//2+4), int(bw*1.2))
        bs.blit(ps2,(pulse_x-bw*3//2-4, 10+bw//2-bw*3//2-4))
        # 코드 스트림
        fnt = pygame.font.SysFont(None, max(8,int(13*z)), bold=True)
        for i in range(length//int(max(1,24*z))+1):
            cx2 = i*int(max(1,24*z)) + int((tick*0.2)%max(1,24*z))
            char = CODE_CHARS[(i+int(tick*0.03))%len(CODE_CHARS)]
            cs  = fnt.render(char,True,(200,255,240))
            cs.set_alpha(_alpha(alpha*0.5))
            bs.blit(cs,(cx2,2))
        screen.blit(bs,(sx,by))


# ── 강화 E: Decidability Trap (계산 격자 정지장) ─────────────────────────────
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
        self.skills["skill_Q"]        = EnigmaDecrypt()
        self.skills["skill_E"]        = BombeMachine()
        self.skills["skill_R"]        = TuringDomain()
        self.skills["skill_Q_domain"] = TuringComplete()
        self.skills["skill_E_domain"] = DecidabilityTrap()

    def get_char_name(self): return "Turing"