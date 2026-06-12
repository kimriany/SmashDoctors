from systems.font_manager import font
"""
Renderer — 배경·플랫폼·HUD 렌더링

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
배경 이미지 교체 방법
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
assets/images/bg_stage_01.png 등 파일을 넣으면 자동으로 사용됩니다.
파일이 없으면 절차적 배경(그라디언트+별+도시)으로 폴백합니다.

스테이지별 배경 파일 이름 규칙:
    stage_01  →  assets/images/bg_stage_01.png
    stage_02  →  assets/images/bg_stage_02.png
    (없으면 assets/images/bg_default.png 시도, 그것도 없으면 절차적 배경)

배경 이미지 해상도는 아무 크기나 괜찮습니다. 자동으로 1280×720에 맞게 스케일됩니다.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
import pygame
import math
import random
import os


# hud.py 상단

SKILL_SLOTS = [
    ("skill_Q", "Q", "Q"),
    ("skill_E", "E", "E"),
    ("skill_R", "ULT", "R"),
]

class Renderer:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.W = screen.get_width()
        self.H = screen.get_height()

        self.font_title = font(56, bold=True)
        self.font_pct   = font(44, bold=True)
        self.font_lg    = font(30, bold=True)
        self.font_md    = font(18, bold=True)
        self.font_sm    = font(13, bold=True)

        # 절차적 배경 캐시 (이미지 없을 때 사용)
        self._proc_bg   = self._bake_proc_bg()
        self._city_surf = self._bake_city()
        self._star_t    = 0.0
        self._pulse_t   = 0.0
        rng = random.Random(77)
        self._stars = [(rng.randint(0,self.W), rng.randint(0, self.H*7//10),
                        rng.uniform(0.3,1.6), rng.uniform(0.2,0.75))
                       for _ in range(130)]

        # 현재 로드된 배경 이미지 (None이면 절차적)
        self._bg_image: pygame.Surface | None = None
        self._stage_id: str = ""

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 배경 이미지 로드
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def load_stage_background(self, stage_id: str):
        """
        스테이지 ID로 배경 이미지를 로드합니다.
        없으면 절차적 배경으로 폴백합니다.

        사용 예:
            renderer.load_stage_background("stage_01")
        """
        if stage_id == self._stage_id:
            return  # 이미 로드됨

        self._stage_id = stage_id
        self._bg_image = None

        candidates = [
            f"assets/images/bg_{stage_id}.png",
            f"assets/images/bg_{stage_id}.jpg",
            f"assets/images/bg_{stage_id}.jpeg",
            "assets/images/bg_default.png",
            "assets/images/bg_default.jpg",
            "assets/images/bg_default.jpeg",
        ]
        for path in candidates:
            if os.path.exists(path):
                try:
                    img = pygame.image.load(path).convert()
                    self._bg_image = pygame.transform.scale(img, (self.W, self.H))
                    print(f"[Renderer] 배경 로드: {path}")
                    return
                except Exception as e:
                    print(f"[Renderer] 배경 로드 실패 ({path}): {e}")

        print(f"[Renderer] 배경 이미지 없음 → 절차적 배경 사용")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 배경 그리기
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def draw_background(self):
        self._star_t  += 0.012
        self._pulse_t += 0.06

        if self._bg_image is not None:
            # ── 이미지 배경 ──
            self.screen.blit(self._bg_image, (0, 0))
        else:
            # ── 절차적 배경 ──
            self.screen.blit(self._proc_bg, (0, 0))
            self.screen.blit(self._city_surf, (0, 0))
            for sx, sy, sr, sa in self._stars:
                fl = sa + math.sin(self._star_t*2.1 + sx*0.01) * 0.18
                c  = int(max(0, min(255, fl*255)))
                pygame.draw.circle(self.screen, (c,c,c), (sx,sy), int(sr))
            # 네온 수평선
            for col, ya in [((40,60,130,40), self.H-78), ((60,90,200,25), self.H-80)]:
                hl = pygame.Surface((self.W, 3), pygame.SRCALPHA)
                hl.fill(col)
                self.screen.blit(hl, (0, ya))

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 절차적 배경 빌드 (캐시)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def _bake_proc_bg(self) -> pygame.Surface:
        sf = pygame.Surface((self.W, self.H))
        for y in range(self.H):
            t = y/self.H
            pygame.draw.line(sf, (int(6+t*14), int(8+t*14), int(20+t*28)), (0,y),(self.W,y))
        return sf

    def _bake_city(self) -> pygame.Surface:
        sf  = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        rng = random.Random(42)
        x   = 0
        while x < self.W:
            bw = rng.randint(42,82); bh = rng.randint(45,140)
            by = self.H - 75 - bh
            pygame.draw.rect(sf, (12,16,36,220), (x,by,bw,bh+75))
            pygame.draw.rect(sf, (18,24,52,120), (x,by,bw,6))
            for wy in range(by+8, by+bh-8, 16):
                for wx in range(x+6, x+bw-8, 11):
                    if rng.random() > 0.52:
                        pygame.draw.rect(sf, (30,55,110,200), (wx,wy,6,8))
            x += bw + rng.randint(2,10)
        return sf

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 플랫폼
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def draw_platforms(self, platforms, camera):
        for p in platforms:
            dr      = camera.apply_rect(p)
            is_main = p.h > 30
            # 아래 글로우
            gs = pygame.Surface((dr.w, 14), pygame.SRCALPHA)
            gc = (70,110,220) if is_main else (50,85,180)
            for gy in range(14):
                a = int(40*(1-gy/14))
                pygame.draw.line(gs, (*gc,a), (0,gy), (dr.w,gy))
            self.screen.blit(gs, (dr.x, dr.y+dr.h))
            # 본체
            pygame.draw.rect(self.screen,
                             (35,50,105) if is_main else (26,40,88),
                             dr, border_radius=6)
            # 상단 네온
            pygame.draw.rect(self.screen,
                             (90,130,230) if is_main else (65,100,195),
                             (dr.x, dr.y, dr.w, 5), border_radius=6)
            pygame.draw.rect(self.screen, (180,210,255),
                             (dr.x+4, dr.y+1, min(60,dr.w-8), 2), border_radius=2)
            # 격자
            for gx in range(dr.x+22, dr.x+dr.w-8, 24):
                pygame.draw.line(self.screen, (55,80,155), (gx,dr.y+5),(gx,dr.y+dr.h-2))
            pygame.draw.rect(self.screen, (65,100,190), dr, 1, border_radius=6)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # HUD
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # HUD
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def draw_hud(self, players):
        self._draw_stocks_center(players)

        PW, PH = 220, 166
        positions = [
            (30, self.H - PH - 12),
            (self.W - PW - 30, self.H - PH - 12)
        ]

        for i, p in enumerate(players):
            self._draw_player_panel(p, positions[i][0], positions[i][1], PW, PH)

    def _draw_player_panel(self, player, px, py, PW=220, PH=166):
        panel = pygame.Surface((PW, PH), pygame.SRCALPHA)

        pygame.draw.rect(panel, (5, 8, 22, 195), (0, 0, PW, PH), border_radius=10)
        pygame.draw.rect(panel, (*player.glow_color, 200), (0, 0, 4, PH), border_radius=10)
        pygame.draw.rect(panel, (*player.glow_color, 70), (0, 0, PW, PH), 1, border_radius=10)

        self.screen.blit(panel, (px, py))

        nm = self.font_md.render(player.name, True, player.glow_color)
        self.screen.blit(nm, (px + 12, py + 8))

        pct = int(player.damage_pct)

        dc = (
            (255, 255, 255) if pct < 60 else
            (255, 210, 60) if pct < 120 else
            (255, 130, 40) if pct < 180 else
            (255, 50, 50)
        )

        if pct >= 150:
            pulse = abs(math.sin(self._pulse_t * 2))
            dc = (min(255, int(dc[0] + 30 * pulse)), dc[1], dc[2])

        self.screen.blit(
            self.font_pct.render(f"{pct}%", True, dc),
            (px + 12, py + 28)
        )

        # 영역전개 / 필살기 충전 디버그 HUD
        self._draw_domain_debug_bars(player, px + 12, py + 74, PW - 24)

        # 입력 슬롯 기준으로 Q/E/ULT 3개만 표시한다.
        self._draw_player_skill_icons(
            player,
            px + 12,
            py + 108,
            PW - 24,
            48
        )

    def _draw_domain_debug_bars(self, player, x, y, w):
        """
        디버깅용 HUD:
        DOMAIN  : 영역전개까지 남은 충전량
        FINISHER: 영역 중 필살기까지 남은 충전량
        """

        def clamp01(v):
            return max(0.0, min(1.0, v))

        def draw_bar(label, value, required, by, color, ready_text=None, locked=False):
            required = max(1.0, float(required))
            value = float(value)
            ratio = clamp01(value / required)
            remain = max(0.0, required - value)

            bar_h = 8
            label_surf = self.font_sm.render(label, True, (190, 190, 215))
            self.screen.blit(label_surf, (x, by - 3))

            bx = x + 64
            bw = w - 64

            pygame.draw.rect(
                self.screen,
                (18, 16, 32),
                (bx, by, bw, bar_h),
                border_radius=4,
            )

            fill_w = int(bw * ratio)
            if fill_w > 0:
                pygame.draw.rect(
                    self.screen,
                    color,
                    (bx, by, fill_w, bar_h),
                    border_radius=4,
                )

            pygame.draw.rect(
                self.screen,
                (80, 80, 110),
                (bx, by, bw, bar_h),
                1,
                border_radius=4,
            )

            if locked:
                text = "LOCK"
                text_col = (255, 110, 110)
            elif ready_text is not None:
                text = ready_text
                text_col = (255, 235, 120)
            else:
                text = f"-{remain:.1f}"
                text_col = (220, 220, 240)

            txt = self.font_sm.render(text, True, text_col)
            self.screen.blit(
                txt,
                (bx + bw - txt.get_width(), by - 11),
            )

        # -----------------------------
        # DOMAIN 게이지
        # -----------------------------
        domain_value = getattr(player, "domain_charge_stack", 0.0)
        domain_required = getattr(player, "domain_charge_required", 8.0)
        domain_active = getattr(player, "domain_active", False)
        domain_ready = getattr(player, "domain_ready", False) or domain_value >= domain_required

        if domain_active:
            domain_text = "ON"
        elif domain_ready:
            domain_text = "READY"
        else:
            domain_text = None

        draw_bar(
            "DOMAIN",
            domain_value,
            domain_required,
            y,
            player.glow_color,
            ready_text=domain_text,
            locked=False,
        )

        # -----------------------------
        # FINISHER 게이지
        # -----------------------------
        fin_value = getattr(player, "finisher_charge_stack", 0.0)
        fin_required = getattr(player, "finisher_charge_required", 5.0)
        fin_ready = getattr(player, "finisher_ready", False) or fin_value >= fin_required
        fin_locked = getattr(player, "finisher_locked", False)

        if not domain_active:
            fin_text = "OFF"
            fin_color = (80, 80, 95)
        elif fin_locked:
            fin_text = None
            fin_color = (180, 70, 70)
        elif fin_ready:
            fin_text = "READY"
            fin_color = (255, 210, 80)
        else:
            fin_text = None
            fin_color = (255, 180, 80)

        draw_bar(
            "FINISH",
            fin_value,
            fin_required,
            y + 18,
            fin_color,
            ready_text=fin_text,
            locked=fin_locked,
        )

    def _draw_player_skill_icons(self, player, x, y, area_w, icon_h):
        skills = self._get_ordered_player_skills(player)

        n = len(SKILL_SLOTS)
        gap = 6
        icon_w = (area_w - gap * (n - 1)) // n

        for i in range(n):
            ix = x + i * (icon_w + gap)
            iy = y

            if i < len(skills):
                sk_key, label, skill = skills[i]
            else:
                sk_key, label, skill = None, "—", None

            is_ult = sk_key in ("skill_R", "skill_U", "ultimate", "ult", "U")

            if is_ult:
                frame_col = (220, 180, 60)
                glow_col = (255, 210, 80)
            else:
                frame_col = player.glow_color
                glow_col = player.glow_color

            self._draw_one_skill_icon_frame(
                player,
                skill,
                label,
                ix,
                iy,
                icon_w,
                icon_h,
                frame_col,
                glow_col,
                is_ult
            )

    def _draw_one_skill_icon_frame(
            self,
            player,
            skill,
            label,
            ix,
            iy,
            iw,
            ih,
            frame_col,
            glow_col,
            is_ult=False
    ):
        # 그림자
        shadow = pygame.Surface((iw + 6, ih + 6), pygame.SRCALPHA)
        pygame.draw.rect(
            shadow,
            (0, 0, 0, 120),
            (3, 3, iw, ih),
            border_radius=8
        )
        self.screen.blit(shadow, (ix - 3, iy - 3))

        # 바깥 액자
        outer_col = (42, 34, 58) if not is_ult else (62, 48, 22)
        pygame.draw.rect(
            self.screen,
            outer_col,
            (ix, iy, iw, ih),
            border_radius=8
        )

        # 안쪽 배경
        inner_rect = pygame.Rect(ix + 3, iy + 3, iw - 6, ih - 6)
        pygame.draw.rect(
            self.screen,
            (18, 16, 32),
            inner_rect,
            border_radius=6
        )

        # 액자 테두리
        pygame.draw.rect(
            self.screen,
            frame_col,
            (ix, iy, iw, ih),
            2,
            border_radius=8
        )

        # 은은한 내부 하이라이트
        pygame.draw.rect(
            self.screen,
            (*glow_col, 70),
            (ix + 3, iy + 3, iw - 6, 2),
            border_radius=4
        )

        # 슬롯 라벨
        label_col = (235, 200, 80) if is_ult else (185, 185, 225)
        label_surf = self.font_sm.render(str(label), True, label_col)
        label_surf = pygame.transform.smoothscale(
            label_surf,
            (
                min(label_surf.get_width(), iw - 8),
                label_surf.get_height()
            )
        ) if label_surf.get_width() > iw - 8 else label_surf

        self.screen.blit(
            label_surf,
            (ix + iw // 2 - label_surf.get_width() // 2, iy + 2)
        )

        # 스킬 없음
        if skill is None:
            empty = self.font_sm.render("—", True, (70, 70, 90))
            self.screen.blit(
                empty,
                (ix + iw // 2 - empty.get_width() // 2,
                 iy + ih // 2 - empty.get_height() // 2)
            )
            return

        # 아이콘 그리기
        icon_size = min(iw - 12, ih - 22)
        icon_x = ix + iw // 2 - icon_size // 2
        icon_y = iy + 16

        if hasattr(skill, "draw_icon"):
            skill.draw_icon(self.screen, icon_x, icon_y, icon_size)
        else:
            # draw_icon이 없는 스킬용 fallback
            pygame.draw.circle(
                self.screen,
                glow_col,
                (ix + iw // 2, iy + ih // 2 + 4),
                icon_size // 2
            )
            first = getattr(skill, "name", "?")[0]
            t = self.font_sm.render(first, True, (255, 255, 255))
            self.screen.blit(
                t,
                (ix + iw // 2 - t.get_width() // 2,
                 iy + ih // 2 + 4 - t.get_height() // 2)
            )

        # 사용 가능 여부 / 쿨타임 계산
        state = self._get_skill_hud_state(player, skill)

        if state["usable"]:
            return

        # 전체를 살짝 어둡게
        dim = pygame.Surface((iw, ih), pygame.SRCALPHA)
        pygame.draw.rect(
            dim,
            (0, 0, 0, 70),
            (0, 0, iw, ih),
            border_radius=8
        )

        # 쿨타임이면 남은 비율만큼만 진하게 덮음
        if state["reason"] == "cooldown":
            ratio = state["cooldown_ratio"]

            cover_h = int(ih * ratio)
            pygame.draw.rect(
                dim,
                (0, 0, 0, 145),
                (0, ih - cover_h, iw, cover_h),
                border_radius=8
            )

            self.screen.blit(dim, (ix, iy))

            # ── 쿨타임 가속 이펙트 ──
            cd_accel = getattr(player, "_cd_accel_active", False)
            if cd_accel:
                t_ms  = pygame.time.get_ticks()
                pulse = abs(math.sin(t_ms * 0.008))

                # 테두리 황금 글로우 (펄스)
                glow_sf = pygame.Surface((iw + 8, ih + 8), pygame.SRCALPHA)
                glow_a  = int(160 + 80 * pulse)
                pygame.draw.rect(glow_sf, (255, 220, 60, glow_a),
                                 (0, 0, iw + 8, ih + 8), 2, border_radius=10)
                self.screen.blit(glow_sf, (ix - 4, iy - 4))

                # 우상단 쿨타임 가속 배지
                badge_fnt = self.font_sm
                accel_mult = float(getattr(player, "_cd_accel_mult", 1.5))
                accel_label = f"×{accel_mult:g}"
                badge_txt = badge_fnt.render(accel_label, True, (255, 230, 80))
                bw, bh = badge_txt.get_width() + 6, badge_txt.get_height() + 2
                badge_bg = pygame.Surface((bw, bh), pygame.SRCALPHA)
                pygame.draw.rect(badge_bg, (80, 60, 0, 200),
                                 (0, 0, bw, bh), border_radius=4)
                badge_bg.blit(badge_txt, (3, 1))
                self.screen.blit(badge_bg, (ix + iw - bw + 2, iy - bh + 2))

                # 쿨타임 텍스트를 황금색으로
                txt = self.font_sm.render(state["text"], True, (255, 230, 80))
            else:
                txt = self.font_sm.render(state["text"], True, (245, 245, 255))

            self.screen.blit(
                txt,
                (ix + iw // 2 - txt.get_width() // 2,
                 iy + ih // 2 - txt.get_height() // 2)
            )

        else:
            # 피로도 초과, 궁극기 게이지 부족 등
            pygame.draw.rect(
                dim,
                (0, 0, 0, 150),
                (0, 0, iw, ih),
                border_radius=8
            )
            self.screen.blit(dim, (ix, iy))

            txt = self.font_sm.render(state["text"], True, (230, 120, 120))
            self.screen.blit(
                txt,
                (ix + iw // 2 - txt.get_width() // 2,
                 iy + ih // 2 - txt.get_height() // 2)
            )

    def _get_ordered_player_skills(self, player):
        skills = getattr(player, "skills", {}) or {}
        domain_active = getattr(player, "domain_active", False)
        ordered = []

        for sk_key, slot_name, key_hint in SKILL_SLOTS:
            display_key = sk_key

            if domain_active:
                domain_key = sk_key + "_domain"
                if domain_key in skills:
                    display_key = domain_key

            ordered.append((display_key, slot_name, skills.get(display_key)))

        return ordered

    def _short_skill_label(self, key):
        key = str(key)

        table = {
            "skill_Q": "Q",
            "skill_Q_domain": "Q",
            "skill_W": "W",
            "skill_W_domain": "W",
            "skill_E": "E",
            "skill_E_domain": "E",
            "skill_R": "ULT",
            "skill_R_domain": "ULT",
            "skill_U": "ULT",
            "move": "MOV",
            "cc": "CC",
            "beam": "BEAM",
            "ultimate": "ULT",
            "ult": "ULT",
        }

        return table.get(key, key[-3:].upper())

    def _get_skill_hud_state(self, player, skill):
        fps = getattr(self, "FPS", 60)

        cd_left = max(0, int(getattr(skill, "current_cooldown", 0)))
        cd_max = int(getattr(skill, "cooldown", 0) or 0)

        if cd_left > 0:
            if cd_max > 0:
                ratio = max(0.0, min(1.0, cd_left / cd_max))
            else:
                ratio = 1.0

            sec = cd_left / fps

            return {
                "usable": False,
                "reason": "cooldown",
                "cooldown_ratio": ratio,
                "text": f"{sec:.1f}s"
            }

        # 피로도 시스템이 "사용하면 fatigue가 증가"하는 방식일 때
        cost = int(getattr(skill, "fatigue_cost", 0) or 0)
        fatigue = int(getattr(player, "fatigue", 0) or 0)
        max_fatigue = int(getattr(player, "max_fatigue", 100) or 100)

        if cost > 0 and fatigue + cost > max_fatigue:
            return {
                "usable": False,
                "reason": "fatigue",
                "cooldown_ratio": 1.0,
                "text": "FAT"
            }

        # 스킬 자체에 can_use가 있으면 그것도 반영
        can_use = getattr(skill, "can_use", None)

        if callable(can_use):
            try:
                ok = can_use(player)
            except TypeError:
                try:
                    ok = can_use()
                except Exception:
                    ok = True
            except Exception:
                ok = True

            if not ok:
                return {
                    "usable": False,
                    "reason": "locked",
                    "cooldown_ratio": 1.0,
                    "text": "NO"
                }

        return {
            "usable": True,
            "reason": None,
            "cooldown_ratio": 0.0,
            "text": ""
        }

    def _draw_fatigue_bar(self, player, px, py):
        bx, by, bw, bh = px+12, py+80, 176, 16
        ratio = player.fatigue / player.max_fatigue

        self.screen.blit(self.font_sm.render("FATIGUE", True, (160,130,210)), (bx, by-16))
        pygame.draw.rect(self.screen, (15,10,30), (bx-1,by-1,bw+2,bh+2), border_radius=5)
        pygame.draw.rect(self.screen, (30,20,55), (bx,by,bw,bh), border_radius=4)

        if ratio > 0:
            fw = int(bw*ratio)
            if ratio < 0.5:
                bar_c=(120,60,220); glow_c=(150,80,240)
            elif ratio < 0.85:
                bar_c=(200,80,180); glow_c=(230,100,200)
            else:
                p = abs(math.sin(self._pulse_t*3))
                bar_c=(int(200+55*p),30,60); glow_c=(255,int(60*p),80)

            pygame.draw.rect(self.screen, bar_c,  (bx,by,fw,bh), border_radius=4)
            pygame.draw.rect(self.screen, glow_c, (bx,by,fw,3),  border_radius=4)
            for seg in range(1,4):
                sx2 = bx+int(bw*seg*0.25)
                pygame.draw.line(self.screen,(15,10,30),(sx2,by),(sx2,by+bh),1)

        pygame.draw.rect(self.screen,(100,60,180),(bx,by,bw,bh),1,border_radius=4)
        if ratio >= 0.99:
            warn = abs(math.sin(self._pulse_t*3))
            self.screen.blit(
                self.font_sm.render("MAX!", True, (255,int(80+100*warn),int(60*warn))),
                (bx+bw+4, by))

    def _draw_stocks_center(self, players):
        cx  = self.W//2
        bar = pygame.Surface((220,38), pygame.SRCALPHA)
        bar.fill((0,0,0,130))
        pygame.draw.rect(bar,(60,80,160,80),bar.get_rect(),1,border_radius=8)
        self.screen.blit(bar,(cx-110,8))
        for i, p in enumerate(players):
            bx = cx + (-95 if i==0 else 15)
            for s in range(3):
                filled = s < p.stocks
                cc = (bx+s*28, 28)
                pygame.draw.circle(self.screen, p.color if filled else (38,38,48), cc, 10)
                pygame.draw.circle(self.screen, p.glow_color if filled else (70,70,80), cc, 10, 2)
                if filled:
                    pygame.draw.circle(self.screen,(255,255,255),(cc[0]-3,cc[1]-3),3)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 오버레이
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def draw_title_screen(self):
        ov = pygame.Surface((self.W,self.H), pygame.SRCALPHA)
        ov.fill((0,0,0,195)); self.screen.blit(ov,(0,0))

        t = self.font_title.render("⚡ SMASH DOCTORS", True, (255,255,255))
        s = self.font_md.render("SCIENCE SMASH  ·  v2.0", True, (110,140,210))
        self.screen.blit(t,(self.W//2-t.get_width()//2, 130))
        self.screen.blit(s,(self.W//2-s.get_width()//2, 200))

        rows=[("PLAYER 1 — Blue","A/D 이동  W 점프  F 공격  G 스킬",(110,175,255)),
              ("PLAYER 2 — Red", "←/→ 이동  ↑ 점프  L 공격  ; 스킬",(255,110,110))]
        for i,(nm,ctrl,col) in enumerate(rows):
            ns=self.font_md.render(nm,True,col); cs=self.font_sm.render(ctrl,True,(200,200,225))
            by=305+i*70
            self.screen.blit(ns,(self.W//2-ns.get_width()//2,by))
            self.screen.blit(cs,(self.W//2-cs.get_width()//2,by+26))

        tip=self.font_sm.render("화면 밖으로 날아가면 실점  |  스톡 3개 소진 시 패배",True,(140,140,160))
        self.screen.blit(tip,(self.W//2-tip.get_width()//2,460))
        st=self.font_lg.render("PRESS  ENTER  TO  START",True,(255,240,90))
        self.screen.blit(st,(self.W//2-st.get_width()//2,510))

    def draw_win_screen(self, winner_name, winner_color):
        ov=pygame.Surface((self.W,self.H),pygame.SRCALPHA)
        ov.fill((0,0,0,215)); self.screen.blit(ov,(0,0))
        wt=self.font_title.render(f"{winner_name}  WINS!", True, winner_color)
        rt=self.font_md.render("ENTER 다시 선택   ESC 종료", True, (170,170,195))
        self.screen.blit(wt,(self.W//2-wt.get_width()//2,240))
        self.screen.blit(rt,(self.W//2-rt.get_width()//2,340))
