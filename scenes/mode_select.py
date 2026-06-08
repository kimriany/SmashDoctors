from systems.font_manager import font
"""
Mode Select — 게임 시작 시 가장 먼저 표시되는 모드 선택창

STORY MODE : 추후 구현 예정 (현재 비활성)
PVP MODE   : 캐릭터 선택 → 스테이지 선택 → 대전
"""
import pygame
import math
import random


class ModeSelect:
    """
    result : "pvp" | "story" | None
    done   : True 이면 선택 완료
    """

    MODES = [
        {
            "id":    "pvp",
            "title": "PVP",
            "sub":   "2 Player Battle",
            "desc":  ["Fight against a friend locally.", "Choose your character and stage."],
            "color": (60, 130, 230),
            "glow":  (120, 190, 255),
            "icon":  "⚔",
            "enabled": True,
        },
        {
            "id":    "story",
            "title": "STORY",
            "sub":   "Coming Soon",
            "desc":  ["Story mode is under construction.", "Stay tuned for future updates."],
            "color": (120, 80, 180),
            "glow":  (180, 140, 255),
            "icon":  "📖",
            "enabled": True,
        },
    ]

    CARD_W = 340
    CARD_H = 400
    CARD_GAP = 60

    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.W = screen.get_width()
        self.H = screen.get_height()

        self.font_title = font(52, bold=True)
        self.font_mode  = font(44, bold=True)
        self.font_sub   = font(18, bold=True)
        self.font_desc  = font(14)
        self.font_sm    = font(13, bold=True)
        self.font_guide = font(13)

        self.cursor  = 0   # 현재 선택 인덱스 (enabled만 이동)
        self.done    = False
        self.result  = None
        self._t      = 0.0

        # 배경 별
        rng = random.Random(99)
        self._stars = [
            (rng.randint(0, self.W), rng.randint(0, self.H),
             rng.uniform(0.3, 1.6), rng.uniform(0.15, 0.7))
            for _ in range(140)
        ]
        self._bg = self._bake_bg()

        total_w = len(self.MODES) * self.CARD_W + (len(self.MODES)-1) * self.CARD_GAP
        self._x0 = (self.W - total_w) // 2

    # ── 배경 빌드 ────────────────────────────────────────────────
    def _bake_bg(self) -> pygame.Surface:
        sf = pygame.Surface((self.W, self.H))
        for y in range(self.H):
            t = y / self.H
            pygame.draw.line(sf,
                             (int(4+t*10), int(6+t*10), int(16+t*24)),
                             (0, y), (self.W, y))
        return sf

    # ── 이벤트 ──────────────────────────────────────────────────
    def handle_event(self, event: pygame.event.Event):
        if event.type != pygame.KEYDOWN:
            return
        k = event.key

        enabled = [i for i, m in enumerate(self.MODES) if m["enabled"]]

        if k in (pygame.K_a, pygame.K_LEFT, pygame.K_d, pygame.K_RIGHT):
            # enabled 항목 안에서만 이동
            if self.cursor in enabled:
                idx = enabled.index(self.cursor)
                if k in (pygame.K_d, pygame.K_RIGHT):
                    self.cursor = enabled[(idx + 1) % len(enabled)]
                else:
                    self.cursor = enabled[(idx - 1) % len(enabled)]

        elif k in (pygame.K_RETURN, pygame.K_f, pygame.K_SPACE):
            mode = self.MODES[self.cursor]
            if mode["enabled"]:
                self.result = mode["id"]
                self.done   = True

    def update(self):
        self._t += 0.03

    # ── draw ────────────────────────────────────────────────────
    def draw(self):
        self.screen.blit(self._bg, (0, 0))

        # 별
        for sx, sy, sr, sa in self._stars:
            fl = sa + math.sin(self._t * 2.2 + sx * 0.01) * 0.18
            c  = int(max(0, min(255, fl * 255)))
            pygame.draw.circle(self.screen, (c, c, c), (sx, sy), int(sr))

        self._draw_title()

        for i, mode in enumerate(self.MODES):
            self._draw_card(i, mode)

        self._draw_guide()

    def _draw_title(self):
        t = self.font_title.render("SMASH  DOCTORS", True, (255, 255, 255))
        self.screen.blit(t, (self.W//2 - t.get_width()//2, 38))
        s = self.font_sub.render("SELECT MODE", True, (130, 150, 220))
        self.screen.blit(s, (self.W//2 - s.get_width()//2, 102))
        pygame.draw.line(self.screen, (70, 100, 220),
                         (self.W//2 - 180, 126), (self.W//2 + 180, 126), 2)

    def _card_rect(self, i) -> pygame.Rect:
        x = self._x0 + i * (self.CARD_W + self.CARD_GAP)
        return pygame.Rect(x, (self.H - self.CARD_H)//2 + 20, self.CARD_W, self.CARD_H)

    def _draw_card(self, i, mode):
        r       = self._card_rect(i)
        col     = mode["color"]
        glw     = mode["glow"]
        sel     = (i == self.cursor)
        enabled = mode["enabled"]

        # 선택 카드 위로 떠오르는 애니메이션
        off = -int(abs(math.sin(self._t * 2.0)) * 12) if sel else 0
        rx, ry = r.x, r.y + off

        # ── 카드 배경 ──
        card = pygame.Surface((self.CARD_W, self.CARD_H), pygame.SRCALPHA)
        for cy in range(self.CARD_H):
            ratio = cy / self.CARD_H
            a = int(40 + ratio * 30) if enabled else int(15 + ratio * 10)
            pygame.draw.line(card, (*col, a), (0, cy), (self.CARD_W, cy))

        # 테두리
        bw  = 3 if sel else 1
        bc  = (*glw, 220 if sel else 60)
        pygame.draw.rect(card, bc, (0, 0, self.CARD_W, self.CARD_H),
                         bw, border_radius=18)
        self.screen.blit(card, (rx, ry))

        # 비활성 dim 오버레이
        if not enabled:
            dim = pygame.Surface((self.CARD_W, self.CARD_H), pygame.SRCALPHA)
            pygame.draw.rect(dim, (0, 0, 0, 120),
                             (0, 0, self.CARD_W, self.CARD_H), border_radius=18)
            self.screen.blit(dim, (rx, ry))

        # ── 아이콘 ──
        icon_sf = font(72).render(mode["icon"], True,
                                                           glw if enabled else (80, 80, 100))
        self.screen.blit(icon_sf, (rx + self.CARD_W//2 - icon_sf.get_width()//2,
                                   ry + 55))

        # 아이콘 아래 글로우 원
        if enabled:
            g_r = 55 + int(math.sin(self._t * 3) * 6) if sel else 50
            gs  = pygame.Surface((g_r*2, g_r*2), pygame.SRCALPHA)
            pygame.draw.circle(gs, (*glw, 35 if sel else 20), (g_r, g_r), g_r)
            self.screen.blit(gs, (rx + self.CARD_W//2 - g_r,
                                  ry + 55 + icon_sf.get_height()//2 - g_r))

        # ── 모드 타이틀 ──
        tc = glw if enabled else (80, 80, 100)
        title_sf = self.font_mode.render(mode["title"], True, tc)
        self.screen.blit(title_sf, (rx + self.CARD_W//2 - title_sf.get_width()//2,
                                    ry + 170))

        # ── 부제 ──
        sub_sf = self.font_sub.render(mode["sub"], True,
                                      (200, 200, 220) if enabled else (80, 80, 90))
        self.screen.blit(sub_sf, (rx + self.CARD_W//2 - sub_sf.get_width()//2,
                                  ry + 222))

        # ── 구분선 ──
        line_col = (*glw, 80) if enabled else (50,50,60,80)
        pygame.draw.line(self.screen, line_col,
                         (rx + 30, ry + 255), (rx + self.CARD_W - 30, ry + 255), 1)

        # ── 설명 텍스트 ──
        for li, line in enumerate(mode["desc"]):
            lc = (175, 175, 200) if enabled else (65, 65, 75)
            ls = self.font_desc.render(line, True, lc)
            self.screen.blit(ls, (rx + self.CARD_W//2 - ls.get_width()//2,
                                  ry + 270 + li * 22))

        # ── 선택 화살표 (선택된 enabled 카드) ──
        if sel and enabled:
            acx = rx + self.CARD_W // 2
            tip = ry - 30 - int(abs(math.sin(self._t * 3.5)) * 9)
            pygame.draw.polygon(self.screen, glw,
                                [(acx, tip), (acx-13, tip+18), (acx+13, tip+18)])

        # ── COMING SOON 뱃지 ──
        if not enabled:
            badge_sf = self.font_sm.render("COMING SOON", True, (150, 130, 200))
            bw2 = badge_sf.get_width() + 20
            bs  = pygame.Surface((bw2, 26), pygame.SRCALPHA)
            pygame.draw.rect(bs, (60, 40, 100, 180), bs.get_rect(), border_radius=8)
            pygame.draw.rect(bs, (120, 90, 180, 180), bs.get_rect(), 1, border_radius=8)
            bs.blit(badge_sf, (10, 5))
            self.screen.blit(bs, (rx + self.CARD_W//2 - bw2//2, ry + self.CARD_H - 50))

    def _draw_guide(self):
        lines = [
            "A / D  or  ← / →   select mode",
            "ENTER / F / SPACE   confirm",
        ]
        for i, txt in enumerate(lines):
            sf = self.font_guide.render(txt, True, (130, 130, 160))
            self.screen.blit(sf, (self.W//2 - sf.get_width()//2,
                                  self.H - 50 + i * 20))
