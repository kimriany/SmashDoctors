"""
Schrodinger — 원자 궤도와 파동 간섭으로 공간을 제어하는 콤보 캐릭터.

일반 스킬:
  Q / ;  Atomic Wave       — ProjectileSkill, 사인파로 이동하는 원자 발사체
  E / '  Interference Well — SummonZoneSkill, 파동 간섭 필드
  R / /  Superposition     — schrodinger_domain.png 영역 전개

영역 전개 중 강화 스킬:
  Q / ;  Quantum Packet    — 더 빠르고 강한 파동 발사체
  E / '  Probability Cloud — 넓은 다단 파동 필드
"""
from entities.player import Player
from systems.skill import ProjectileSkill, SummonZoneSkill, DomainUltimateSkill, DashSkill, Skill
import pygame
import math
import random


DOMAIN_BG = "assets/images/charactor/Schrödinger/schrodinger_domain.png"
ATOM_COLORS = (
    (90, 210, 255),
    (160, 120, 255),
    (235, 245, 255),
    (80, 255, 210),
)


def _alpha(value):
    return max(0, min(255, int(value)))


def _apply_cd_accel(owner, source_skill, mult):
    extra = max(0.0, mult - 1.0)
    if extra <= 0:
        owner._cd_accel_active = False
        owner._cd_accel_mult = 1.0
        return

    source_skill._cd_accum = getattr(source_skill, "_cd_accum", 0.0) + extra
    bonus = int(source_skill._cd_accum)
    if bonus >= 1:
        source_skill._cd_accum -= bonus
        for sk in owner.skills.values():
            if sk is not source_skill and sk.current_cooldown > 0:
                sk.current_cooldown = max(0, sk.current_cooldown - bonus)
    owner._cd_accel_active = True
    owner._cd_accel_mult = mult


class _DomainOnlyMixin:
    def can_activate(self, owner): return getattr(owner, "domain_active", False)

class _NormalOnlyMixin:
    def can_activate(self, owner): return not getattr(owner, "domain_active", False)

def _alpha(v): return max(0, min(255, int(v)))

# 슈뢰딩거 고양이 실험 테마 색상
CAT_COLORS = ((200, 80, 255), (140, 60, 220), (255, 200, 80), (100, 220, 200), (255, 120, 180))
BOX_COLOR  = (80, 60, 40)
POISON_COL = (80, 220, 80)


# ══════════════════════════════════════════════════════
#  Q — Dead Cat  (독 주입기 투척)
# ══════════════════════════════════════════════════════
class CatBox(_NormalOnlyMixin, Skill):
    """
    슈뢰딩거 Q — Cat's Box (고양이 상자)

    상대에게 상자를 씌운다.
    상자 안에서 고양이는 죽어있기도 살아있기도 한 상태.

    [상자 닫힌 동안 — 3초]:
    - 상대는 이동 가능하지만 공격 스킬 사용 불가 (관측 전 상태)
    - 상대 이동속도 30% 감소

    [상자가 열리는 순간 — 랜덤]:
    - 50% DEAD  : 독가스 폭발. 피해 + 슬로우 3초
    - 50% ALIVE : 무사 탈출. 대신 슈뢰딩거 모든 스킬 쿨타임 즉시 리셋
    """
    DISPLAY_NAME  = "Cat's Box"
    DESCRIPTION   = "Trap enemy in a box. Skills sealed inside.\n50% poison gas / 50% free reset."
    COOLDOWN_SEC  = 7.0

    BOX_DURATION  = 180   # 3초
    SLOW_MULT     = 0.70
    POISON_DMG    = 28
    CAST_RANGE    = 380

    def __init__(self):
        super().__init__("Cat's Box", damage=0, cooldown=420, duration=220)
        self.charge_value   = 1.2
        self._target        = None
        self._box_timer     = 0
        self._box_active    = False
        self._opened        = False
        self._result        = None
        self._open_t        = 0
        self._box_x         = 0.0
        self._box_y         = 0.0

    def on_start(self, owner, event_bus=None, psys=None):
        target = getattr(owner, "_skill_target", None)
        if not target or target.dead:
            return
        dist = abs(target.rect.centerx - owner.rect.centerx)
        if dist > self.CAST_RANGE:
            return
        self._target      = target
        self._box_timer   = self.BOX_DURATION
        self._box_active  = True
        self._opened      = False
        self._result      = None
        self._open_t      = 0
        self.has_hit      = False
        # 봉인 부여
        target._cat_boxed       = True
        target._cat_box_timer   = self.BOX_DURATION
        target._cat_box_source  = owner
        if psys:
            for _ in range(16):
                ang = random.uniform(0, math.pi*2)
                psys.spawn(target.rect.centerx + math.cos(ang)*40,
                           target.rect.centery + math.sin(ang)*40,
                           CAT_COLORS[0], count=1, speed=random.uniform(3,8),
                           gravity=-0.03, life=random.randint(14,24), r=random.randint(3,6), glow=True)

    def on_update(self, owner, event_bus=None, psys=None):
        if not self._box_active: return
        t = self._target
        if t is None or t.dead:
            self._box_active = False
            return

        if self._opened:
            self._open_t += 1
            if self._open_t > 28:
                self._box_active = False
                if hasattr(t, "_cat_boxed"): del t._cat_boxed
            return

        self._box_timer -= 1
        self._box_x = float(t.rect.centerx)
        self._box_y = float(t.rect.centery)

        # 이동 제한
        t.vel.x *= self.SLOW_MULT

        # 스킬 사용 봉인 (skill_Q, skill_E만)
        for sk_key in ("skill_Q", "skill_E"):
            if sk_key in t.skills:
                sk = t.skills[sk_key]
                if sk.active:
                    pass  # 발동 중인 건 유지
                # can_use를 막는 방식 대신 current_cooldown 리셋
        t._cat_box_timer = self._box_timer

        if psys and self._box_timer % 12 == 0:
            psys.spawn(t.rect.centerx + random.uniform(-30,30),
                       t.rect.centery + random.uniform(-30,30),
                       BOX_COLOR, count=1, speed=0.5, gravity=-0.01, life=12, r=3)

        if self._box_timer <= 0:
            self._trigger_open(owner, t, event_bus, psys)

    def _trigger_open(self, owner, target, event_bus, psys):
        self._opened = True
        self._result = "dead" if random.random() < 0.5 else "alive"
        if hasattr(target, "_cat_boxed"): del target._cat_boxed
        if hasattr(target, "_cat_box_timer"): del target._cat_box_timer

        if self._result == "dead":
            # 독가스 폭발
            target._poison_slow       = True
            target._poison_slow_timer = 180
            if psys:
                for _ in range(26):
                    ang = random.uniform(0, math.pi*2)
                    psys.spawn(target.rect.centerx+math.cos(ang)*20,
                               target.rect.centery+math.sin(ang)*20,
                               POISON_COL, count=1, speed=random.uniform(4,10),
                               gravity=-0.02, life=random.randint(18,30), r=random.randint(4,8), glow=True)
            if event_bus:
                event_bus.emit("attack_hit", {"attacker":owner,"target":target,
                    "damage":self.POISON_DMG,"is_skill":True,
                    "particle_system":psys,"floater_system":None})
        else:
            # ALIVE — 슈뢰딩거 쿨타임 전부 리셋
            for sk in owner.skills.values():
                sk.current_cooldown = 0
            if psys:
                for col in list(ATOM_COLORS) + [(255,255,255)]:
                    psys.spawn(owner.rect.centerx, owner.rect.centery, col,
                               count=10, speed=6, gravity=-0.04, life=20, r=5, glow=True)

    def get_hitbox(self, owner): return None

    def draw_behind(self, owner, screen, camera, dr, bob, z):
        if not self._box_active or self._target is None: return
        t   = self._target
        tx  = float(t.rect.centerx); ty = float(t.rect.centery)
        sx, sy = camera.world_to_screen(int(tx), int(ty))
        tick   = pygame.time.get_ticks()

        if self._opened:
            ot = self._open_t / 28
            col = POISON_COL if self._result == "dead" else (255,230,80)
            for ri in range(3):
                rr = int((50+ri*20)*z*(1+ot*3))
                if rr < 2: continue
                es = pygame.Surface((rr*2+4,rr*2+4),pygame.SRCALPHA)
                pygame.draw.circle(es,(*col,_alpha((180-ri*40)*(1-ot))),(rr+2,rr+2),rr)
                screen.blit(es,(sx-rr-2,sy-rr-2))
            from systems.font_manager import font as _fnt
            fnt = _fnt(max(12,int(20*z)),bold=True)
            lbl_text = "DEAD." if self._result=="dead" else "ALIVE!"
            lbl_col  = POISON_COL if self._result=="dead" else (255,230,80)
            lbl = fnt.render(lbl_text, True, lbl_col)
            lbl.set_alpha(_alpha(240*(1-ot)))
            screen.blit(lbl,(sx-lbl.get_width()//2, sy-int(50*z)-int(ot*24)))
            return

        bw = bh = int(90*z)
        t_ratio = self._box_timer / self.BOX_DURATION
        alpha   = _alpha(200)
        pulse   = abs(math.sin(self._box_timer*0.1))

        # 나무 상자
        bs = pygame.Surface((bw+8,bh+8),pygame.SRCALPHA)
        pygame.draw.rect(bs,(*BOX_COLOR,_alpha(alpha*0.65)),(4,4,bw,bh),border_radius=4)
        pygame.draw.rect(bs,(140,110,60,alpha),(4,4,bw,bh),max(2,int(3*z)),border_radius=4)
        # 나무결
        for yi in range(0,bh,max(1,int(14*z))):
            pygame.draw.line(bs,(100,80,40,_alpha(alpha*0.35)),(4,4+yi),(4+bw,4+yi),1)
        # 타이머 바
        bar_w = int(bw*t_ratio)
        if bar_w>0:
            pygame.draw.rect(bs,(*CAT_COLORS[0],180),(4,bh+2,bar_w,4),border_radius=2)
        # 물음표
        from systems.font_manager import font as _fnt
        fnt = _fnt(max(12,int(24*z)),bold=True)
        qlbl = fnt.render("?",True,CAT_COLORS[0])
        qlbl.set_alpha(_alpha(180*(0.5+0.5*pulse)))
        bs.blit(qlbl,(bw//2+4-qlbl.get_width()//2,bh//2+4-qlbl.get_height()//2))
        screen.blit(bs,(sx-bw//2-4,sy-bh//2-4))

        # 초 카운트
        secs = math.ceil(self._box_timer/60)
        cnt  = _fnt(max(10,int(14*z)),bold=True).render(f"{secs}s",True,(200,160,255))
        cnt.set_alpha(alpha)
        screen.blit(cnt,(sx-cnt.get_width()//2,sy-int(bh*0.5*z)-22))


class QuantumLeap(_NormalOnlyMixin, Skill):
    """
    슈뢰딩거 E — Quantum Leap (양자 도약)

    상대 위치로 순간이동한다.
    도착 직후 주변에 '확률 필드'를 0.8초간 생성:
    - 필드 안에서 슈뢰딩거의 모든 스킬 쿨타임 즉시 0으로
    - 필드 안에 있는 상대는 강하게 튕김 + 피해
    - 이동 직후 0.3초 무적
    """
    DISPLAY_NAME  = "Quantum Leap"
    DESCRIPTION   = "Leap to the enemy instantly.\nField on arrival resets all cooldowns."
    COOLDOWN_SEC  = 8.0

    FIELD_RADIUS  = 100
    FIELD_DURATION = 50
    FIELD_DMG     = 22

    def __init__(self):
        super().__init__("Quantum Leap", damage=self.FIELD_DMG, cooldown=480, duration=80)
        self.charge_value   = 1.3
        self._field_active  = False
        self._field_timer   = 0
        self._field_x       = 0.0
        self._field_y       = 0.0
        self._reset_done    = False
        self._push_done     = False

    def on_start(self, owner, event_bus=None, psys=None):
        target = getattr(owner, "_skill_target", None)
        self._field_active = False
        self._field_timer  = 0
        self._reset_done   = False
        self._push_done    = False
        self.has_hit       = False

        if target and not target.dead:
            # 상대 뒤쪽으로 이동
            side = -target.facing if hasattr(target,"facing") else -owner.facing
            dest_x = target.rect.centerx + side * 70
            dest_y = target.rect.y
        else:
            dest_x = owner.rect.centerx + owner.facing * 260
            dest_y = owner.rect.y

        self._field_x = float(owner.rect.centerx + (dest_x - owner.rect.centerx) * 0.5)
        self._field_y = float(owner.rect.centery)
        owner.rect.x  = int(dest_x - owner.rect.w//2)
        owner.rect.y  = int(dest_y)
        owner.vel     = pygame.math.Vector2(0, 0)
        owner.invincible = 18
        owner.facing     = -side if hasattr(target,"facing") else owner.facing

        # 도착 이펙트
        self._field_active = True
        self._field_timer  = self.FIELD_DURATION
        self._field_x      = float(owner.rect.centerx)
        self._field_y      = float(owner.rect.centery)
        if psys:
            for _ in range(22):
                ang = random.uniform(0, math.pi*2)
                psys.spawn(owner.rect.centerx+math.cos(ang)*30,
                           owner.rect.centery+math.sin(ang)*30,
                           random.choice(ATOM_COLORS),
                           count=1, speed=random.uniform(4,10),
                           gravity=-0.04, life=random.randint(16,28), r=random.randint(3,7), glow=True)

    def on_update(self, owner, event_bus=None, psys=None):
        if not self._field_active: return
        self._field_timer -= 1

        # 쿨타임 즉시 리셋 (첫 프레임)
        if not self._reset_done:
            self._reset_done = True
            for sk_key, sk in owner.skills.items():
                if sk_key != "skill_E":   # 본인 제외
                    sk.current_cooldown = 0

        # 상대 밀치기 (한 번)
        if not self._push_done:
            target = getattr(owner, "_skill_target", None)
            if target and not target.dead:
                dx = target.rect.centerx - self._field_x
                dy = target.rect.centery  - self._field_y
                dist = math.sqrt(dx*dx+dy*dy)
                if dist < self.FIELD_RADIUS:
                    self._push_done = True
                    target.vel.x = (dx/max(1,dist)) * 11
                    target.vel.y = (dy/max(1,dist)) * 11 - 5
                    if event_bus:
                        event_bus.emit("attack_hit",{"attacker":owner,"target":target,
                            "damage":self.FIELD_DMG,"is_skill":True,
                            "particle_system":psys,"floater_system":None})

        if psys and self._field_timer % 6 == 0:
            ang = random.uniform(0, math.pi*2)
            r   = random.uniform(20, self.FIELD_RADIUS*0.8)
            psys.spawn(self._field_x+math.cos(ang)*r,
                       self._field_y+math.sin(ang)*r,
                       random.choice(ATOM_COLORS),
                       count=1, speed=1.2, gravity=-0.02, life=12, r=3, glow=True)

        if self._field_timer <= 0:
            self._field_active = False

    def get_hitbox(self, owner): return None

    def draw_front(self, owner, screen, camera, dr, bob, z):
        if not self._field_active: return
        sx, sy  = camera.world_to_screen(int(self._field_x), int(self._field_y))
        t_ratio = self._field_timer / self.FIELD_DURATION
        alpha   = _alpha(200 * t_ratio)
        r       = int(self.FIELD_RADIUS * z)
        tick    = pygame.time.get_ticks()

        # 확률 필드 원
        fs = pygame.Surface((r*2+8,r*2+8),pygame.SRCALPHA)
        pygame.draw.circle(fs,(*ATOM_COLORS[0],_alpha(alpha*0.25)),(r+4,r+4),r)
        pygame.draw.circle(fs,(*ATOM_COLORS[0],alpha),(r+4,r+4),r,max(2,int(3*z)))
        # 수렴 링
        for ri in range(3):
            inner = int(r*(0.3+ri*0.25)*(1-t_ratio*0.5))
            pygame.draw.circle(fs,(*ATOM_COLORS[ri+1],_alpha(alpha*(0.4-ri*0.1))),(r+4,r+4),inner,max(1,int(2*z)))
        screen.blit(fs,(sx-r-4,sy-r-4))

        # RESET 텍스트
        from systems.font_manager import font as _fnt
        fnt = _fnt(max(10,int(16*z)),bold=True)
        lbl = fnt.render("COOLDOWN RESET",True,(220,180,255))
        lbl.set_alpha(_alpha(alpha*1.2))
        screen.blit(lbl,(sx-lbl.get_width()//2,sy-r-24))


class DiracBox(_DomainOnlyMixin, Skill):
    """
    강화 Q — Dirac Box

    더 크고 오래 지속되는 상자.
    열릴 때 무조건 폭발 (랜덤 없음).
    추가로 상대 스킬 전체 봉인.
    """
    DISPLAY_NAME  = "Dirac Box"
    DESCRIPTION   = "Domain — A bigger box. Always explodes.\nSeals all skills inside."
    COOLDOWN_SEC  = 8.0

    BOX_DURATION  = 240   # 4초
    SLOW_MULT     = 0.55
    EXPLODE_DMG   = 42
    CAST_RANGE    = 440
    SEAL_DURATION = 240

    def __init__(self):
        super().__init__("Dirac Box", damage=0, cooldown=480, duration=280)
        self.charge_value=0.0; self.finisher_charge_value=2.2
        self._target=None; self._box_timer=0
        self._box_active=False; self._opened=False; self._open_t=0

    def on_start(self, owner, event_bus=None, psys=None):
        target = getattr(owner,"_skill_target",None)
        if not target or target.dead: return
        if abs(target.rect.centerx-owner.rect.centerx)>self.CAST_RANGE: return
        self._target=target; self._box_timer=self.BOX_DURATION
        self._box_active=True; self._opened=False; self._open_t=0
        self.has_hit=False
        # 스킬 봉인
        for sk in target.skills.values():
            sk._dirac_sealed=True
            if sk.current_cooldown < self.SEAL_DURATION:
                sk.current_cooldown = self.SEAL_DURATION
        target._cat_boxed=True; target._cat_box_timer=self.BOX_DURATION
        if psys:
            for _ in range(24):
                ang=random.uniform(0,math.pi*2)
                psys.spawn(target.rect.centerx+math.cos(ang)*55,target.rect.centery+math.sin(ang)*55,
                           random.choice(CAT_COLORS),count=1,speed=random.uniform(4,10),
                           gravity=-0.03,life=random.randint(16,28),r=random.randint(4,8),glow=True)

    def on_update(self, owner, event_bus=None, psys=None):
        if not self._box_active: return
        t=self._target
        if t is None or t.dead:
            self._cleanup(t); self._box_active=False; return

        if self._opened:
            self._open_t+=1
            if self._open_t>32:
                self._box_active=False; self._cleanup(t)
            return

        self._box_timer-=1; t.vel.x*=self.SLOW_MULT
        t._cat_box_timer=self._box_timer

        if psys and self._box_timer%10==0:
            psys.spawn(t.rect.centerx+random.uniform(-50,50),
                       t.rect.centery+random.uniform(-50,50),
                       BOX_COLOR,count=1,speed=0.5,gravity=-0.01,life=14,r=4)
        if self._box_timer<=0:
            self._opened=True
            self._cleanup(t)
            if event_bus:
                event_bus.emit("attack_hit",{"attacker":owner,"target":t,
                    "damage":self.EXPLODE_DMG,"is_skill":True,"particle_system":psys,"floater_system":None})
            t.vel.x=owner.facing*12; t.vel.y=-9
            if psys:
                for col in list(CAT_COLORS)+[(255,255,255),POISON_COL]:
                    psys.spawn(t.rect.centerx,t.rect.centery,col,count=22,speed=10,gravity=-0.03,life=30,r=8,glow=True)

    def _cleanup(self, t):
        if t:
            for sk in t.skills.values():
                if hasattr(sk,"_dirac_sealed"): del sk._dirac_sealed
            if hasattr(t,"_cat_boxed"): del t._cat_boxed
            if hasattr(t,"_cat_box_timer"): del t._cat_box_timer

    def get_hitbox(self, owner): return None

    def draw_behind(self, owner, screen, camera, dr, bob, z):
        if not self._box_active or self._target is None: return
        t=self._target
        sx,sy=camera.world_to_screen(t.rect.centerx,t.rect.centery)
        tick=pygame.time.get_ticks()

        if self._opened:
            ot=self._open_t/32
            for ri,(col,aa) in enumerate([(CAT_COLORS[0],160),(POISON_COL,200),((255,255,255),240)]):
                rr=int((60+ri*25)*z*(1+ot*3.5))
                if rr<2: continue
                es=pygame.Surface((rr*2+4,rr*2+4),pygame.SRCALPHA)
                pygame.draw.circle(es,(*col,_alpha(aa*(1-ot))),(rr+2,rr+2),rr)
                screen.blit(es,(sx-rr-2,sy-rr-2))
            from systems.font_manager import font as _fnt
            fnt=_fnt(max(12,int(22*z)),bold=True)
            lbl=fnt.render("COLLAPSE!",True,(220,130,255))
            lbl.set_alpha(_alpha(240*(1-ot)))
            screen.blit(lbl,(sx-lbl.get_width()//2,sy-int(60*z)-int(ot*28)))
            return

        bw=bh=int(120*z)
        t_ratio=self._box_timer/self.BOX_DURATION
        alpha=_alpha(220)
        pulse=abs(math.sin(self._box_timer*0.08))

        bs=pygame.Surface((bw+8,bh+8),pygame.SRCALPHA)
        pygame.draw.rect(bs,(*BOX_COLOR,_alpha(alpha*0.7)),(4,4,bw,bh),border_radius=5)
        pygame.draw.rect(bs,(180,140,70,alpha),(4,4,bw,bh),max(3,int(4*z)),border_radius=5)
        for yi in range(0,bh,max(1,int(16*z))):
            pygame.draw.line(bs,(110,90,45,_alpha(alpha*0.35)),(4,4+yi),(4+bw,4+yi),1)
        bar_w=int(bw*t_ratio)
        if bar_w>0:
            pygame.draw.rect(bs,(220,80,255,200),(4,bh+2,bar_w,5),border_radius=2)
        from systems.font_manager import font as _fnt
        fnt=_fnt(max(12,int(28*z)),bold=True)
        qlbl=fnt.render("!",True,(255,80,80))
        qlbl.set_alpha(_alpha(200*(0.4+0.6*pulse)))
        bs.blit(qlbl,(bw//2+4-qlbl.get_width()//2,bh//2+4-qlbl.get_height()//2))
        screen.blit(bs,(sx-bw//2-4,sy-bh//2-4))
        secs=math.ceil(self._box_timer/60)
        from systems.font_manager import font as _fnt
        cnt=_fnt(max(10,int(14*z)),bold=True).render(f"{secs}s",True,(220,130,255))
        cnt.set_alpha(alpha); screen.blit(cnt,(sx-cnt.get_width()//2,sy-int(bh*0.5*z)-24))


class CatsCurse(_DomainOnlyMixin, Skill):
    """
    강화 E — Cat's Curse (고양이의 저주)

    상대에게 슈뢰딩거 저주를 건다.
    5초간:
    - 슈뢰딩거가 받는 피해의 70%를 상대도 같이 받음
    - 상대가 스킬을 쓸수록 자기 자신이 더 다침 (스킬 역류)
    종료 시 저주 폭발 피해.
    """
    DISPLAY_NAME  = "Cat's Curse"
    DESCRIPTION   = "Domain — Link quantum fates.\nDamage you take is reflected back."
    COOLDOWN_SEC  = 10.0

    CURSE_DURATION = 300   # 5초
    REFLECT_RATIO  = 0.70
    SKILL_BACKLASH = 8     # 스킬 사용 시 역류 피해
    FINAL_DMG      = 24
    CAST_RANGE     = 420

    def __init__(self):
        super().__init__("Cat's Curse", damage=10, cooldown=600, duration=340)
        self.charge_value=0.0; self.finisher_charge_value=2.5
        self._curse_target=None; self._curse_timer=0
        self._link_active=False; self._last_hp=0.0
        self._final_done=False

    def on_start(self, owner, event_bus=None, psys=None):
        target=getattr(owner,"_skill_target",None)
        if not target or target.dead: return
        if abs(target.rect.centerx-owner.rect.centerx)>self.CAST_RANGE: return
        self._curse_target=target; self._curse_timer=self.CURSE_DURATION
        self._link_active=True; self._last_hp=owner.damage_pct
        self._final_done=False; self.has_hit=False
        if event_bus:
            event_bus.emit("attack_hit",{"attacker":owner,"target":target,
                "damage":self.damage,"is_skill":True,"particle_system":psys,"floater_system":None})
        if psys:
            for _ in range(18):
                ang=random.uniform(0,math.pi*2)
                psys.spawn(target.rect.centerx+math.cos(ang)*40,target.rect.centery+math.sin(ang)*40,
                           CAT_COLORS[0],count=1,speed=random.uniform(3,8),
                           gravity=-0.03,life=random.randint(14,24),r=random.randint(3,6),glow=True)

    def on_update(self, owner, event_bus=None, psys=None):
        if not self._link_active: return
        self._curse_timer-=1
        t=self._curse_target
        if t is None or t.dead:
            self._link_active=False; return

        # 피해 반사
        curr=owner.damage_pct
        delta=curr-self._last_hp
        if delta>0 and event_bus:
            refl=delta*self.REFLECT_RATIO
            if refl>=0.5:
                event_bus.emit("attack_hit",{"attacker":owner,"target":t,
                    "damage":refl,"is_skill":True,"particle_system":psys,"floater_system":None})
            if psys and refl>=1:
                psys.spawn(t.rect.centerx,t.rect.centery,CAT_COLORS[0],count=5,speed=4,gravity=-0.03,life=12,r=4,glow=True)
        self._last_hp=curr

        # 연결선 파티클
        if psys and self._curse_timer%8==0:
            t_r=random.uniform(0.1,0.9)
            mx=owner.rect.centerx+(t.rect.centerx-owner.rect.centerx)*t_r
            my=owner.rect.centery+(t.rect.centery-owner.rect.centery)*t_r
            psys.spawn(mx,my,random.choice(ATOM_COLORS),count=1,speed=1.5,gravity=0,life=10,r=3,glow=True)

        if self._curse_timer<=0 and not self._final_done:
            self._final_done=True; self._link_active=False
            if event_bus:
                event_bus.emit("attack_hit",{"attacker":owner,"target":t,
                    "damage":self.FINAL_DMG,"is_skill":True,"particle_system":psys,"floater_system":None})
            t.vel.x+=owner.facing*9; t.vel.y-=7
            if psys:
                for col in list(CAT_COLORS)+[(255,255,255)]:
                    psys.spawn(t.rect.centerx,t.rect.centery,col,count=18,speed=8,gravity=-0.03,life=26,r=7,glow=True)

    def get_hitbox(self, owner): return None

    def draw_front(self, owner, screen, camera, dr, bob, z):
        if not self._link_active or not self._curse_target: return
        t=self._curse_target
        if t.dead: return
        t_ratio=self._curse_timer/self.CURSE_DURATION
        alpha=_alpha(180*t_ratio)
        tick=pygame.time.get_ticks()
        sox,soy=camera.world_to_screen(owner.rect.centerx,owner.rect.centery)
        stx,sty=camera.world_to_screen(t.rect.centerx,t.rect.centery)

        # 저주 연결선
        ls=pygame.Surface(screen.get_size(),pygame.SRCALPHA)
        for ray in range(2):
            for i in range(12):
                t1=i/12; t2=(i+1)/12
                w=math.sin(t1*math.pi*2+tick*0.007+ray*0.8)*10*z
                x1=int(sox+(stx-sox)*t1); y1=int(soy+(sty-soy)*t1+w)
                x2=int(sox+(stx-sox)*t2); y2=int(soy+(sty-soy)*t2+math.sin(t2*math.pi*2+tick*0.007+ray*0.8)*10*z)
                pygame.draw.line(ls,(*CAT_COLORS[ray%len(CAT_COLORS)],_alpha(alpha*0.5)),(x1,y1),(x2,y2),max(1,int(2*z)))
        screen.blit(ls,(0,0))

        # 저주 링 (타겟)
        r=max(4,int(32*z))
        pulse=abs(math.sin(tick*0.005))
        rs=pygame.Surface((r*2+8,r*2+8),pygame.SRCALPHA)
        pygame.draw.circle(rs,(200,40,220,_alpha(alpha*0.35)),(r+4,r+4),r)
        pygame.draw.circle(rs,(220,80,255,_alpha(alpha*(0.6+0.3*pulse))),(r+4,r+4),r,max(2,int(3*z)))
        screen.blit(rs,(stx-r-4,sty-r-4))

        from systems.font_manager import font as _fnt
        fnt=_fnt(max(10,int(13*z)),bold=True)
        secs=math.ceil(self._curse_timer/60)
        lbl=fnt.render(f"CURSED {secs}s",True,(220,80,255))
        lbl.set_alpha(alpha); screen.blit(lbl,(stx-lbl.get_width()//2,sty-r-22))


class SchrodingerDomain(DomainUltimateSkill):
    DISPLAY_NAME = "Superposition Domain"
    DESCRIPTION = "Open Schrodinger's quantum domain."
    DOMAIN_BG_PATH = DOMAIN_BG
    DOMAIN_PARTICLE_COLOR = (170, 120, 255)
    BREAK_HITS = 5
    CUTSCENE_FRAMES = 32
    CUTSCENE_ZOOM = 1.46
    TRANSITION_SPEED = 0.055
    FREEZE_DURING_TRANSITION = True

    def __init__(self):
        super().__init__(name="Superposition Domain", damage=0, duration=999999)



class Schrödinger(Player):
    WEIGHT = 96
    KB_GROWTH = 78
    BASE_KB = 30
    WALK_SPEED = 6.2
    JUMP_POWER = -15.0
    MAX_JUMPS = 2
    ATTACK_DMG = 9
    ATK_FRAMES = 16
    ATK_CD = 26
    HIT_START = 3
    HIT_END = 13

    BODY_COLOR = (155, 60, 220)
    TRIM_COLOR = (90, 20, 140)
    GLOW_COLOR = (210, 130, 255)
    DARK_COLOR = (60, 10, 100)
    DISPLAY_NAME = "Schrödinger"
    DESCRIPTION = (
        "Atom and wave combo fighter.\n"
        "Domain strengthens probability skills."
    )
    PREVIEW_COLOR = (155, 60, 220)
    SKILL_NAME = "Atomic Wave"

    SPRITE_PATH = "assets/images/charactor/Schrödinger/IDL.png"
    SPRITE_IDLE = "assets/images/charactor/Schrödinger/IDL.png"
    SPRITE_JUMP = "assets/images/charactor/Schrödinger/jump.png"
    SPRITE_ATTACK = "assets/images/charactor/Schrödinger/attack.png"
    SPRITE_SKILL = "assets/images/charactor/Schrödinger/skill.png"

    SPRITE_SCALE = 1.25
    SPRITE_OFFSET_X = 0
    SPRITE_OFFSET_Y = 6

    SKILL_DEFS_META = {
        "basic": ("Atomic Wave", "ProjectileSkill", 18, 22, 3.5),
        "cc": ("Quantum Collapse Zone", "SummonZoneSkill", 22, 0, 9.0),
        "enhance": ("Superposition Domain", "DomainUltimateSkill", 0, 0, 0.0),
    }

    def __init__(self, x, y, name="Player", player_id=1):
        super().__init__(x, y, name, player_id)
        self.color = self.BODY_COLOR
        self.trim_color = self.TRIM_COLOR
        self.glow_color = self.GLOW_COLOR
        self.dark_color = self.DARK_COLOR
        self.max_jumps = self.MAX_JUMPS
        self.attack_damage = self.ATTACK_DMG

    def _init_skills(self):
        self.skills["skill_Q"]        = CatBox()
        self.skills["skill_E"]        = QuantumLeap()
        self.skills["skill_R"]        = SchrodingerDomain()
        self.skills["skill_Q_domain"] = DiracBox()
        self.skills["skill_E_domain"] = CatsCurse()

    def use_skill(self, skill_key: str, event_bus=None, psys=None) -> bool:
        domain_key = skill_key + "_domain"
        if domain_key in self.skills:
            domain_skill = self.skills[domain_key]
            if domain_skill.can_use(self):
                if self.active_skill is not None and self.active_skill is not domain_skill:
                    self.active_skill.on_end(self)
                domain_skill.use(self, event_bus, psys)
                self.active_skill = domain_skill
                return True

        skill = self.skills.get(skill_key)
        if skill and skill.can_use(self):
            if self.active_skill is not None and self.active_skill is not skill:
                self.active_skill.on_end(self)
            skill.use(self, event_bus, psys)
            self.active_skill = skill
            return True

        return False

    def get_char_name(self):
        return "Schrödinger"