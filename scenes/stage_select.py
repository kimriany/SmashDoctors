from systems.font_manager import font
"""
스테이지 선택창
A/D(P1) 또는 ←/→(P2) 로 선택, ENTER 또는 F/L 로 확정
"""
import pygame
import math
import random
import json
import os

from systems.stage_loader import StageLoader


# ── 스테이지 메타데이터 ────────────────────────────────────────
STAGES = [
    {
        "id":    "stage_01",
        "path":  "data/stages/stage_01.json",
        "name":  "Lab Battlefield",
        "sub":   "기본 전장 · 균형잡힌 플랫폼",
        "theme": (50, 80, 180),
        "tag":   "BALANCED",

    },
    {
        "id":    "stage_02",
        "path":  "data/stages/stage_02.json",
        "name":  "Vertical Lab",
        "sub":   "높은 구조 · 공중전 유리",
        "theme": (40, 160, 100),
        "tag":   "AERIAL",
    },
    {
        "id":    "stage_03",
        "path":  "data/stages/stage_03.json",
        "name":  "The Abyss",
        "sub":   "발판 적음 · 생존이 관건",
        "theme": (140, 40, 200),
        "tag":   "SURVIVAL",
    },
    {
        "id":    "stage_04",
        "path":  "data/stages/stage_04.json",
        "name":  "Flat Zone",
        "sub":   "넓은 지형 · 횡이동 대전",
        "theme": (200, 120, 30),
        "tag":   "GROUND",
    },
]

CARD_W   = 260
CARD_H   = 340
CARD_GAP = 26


class StageSelect:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.W = screen.get_width()
        self.H = screen.get_height()

        self.font_title = font(42, bold=True)
        self.font_lg    = font(22, bold=True)
        self.font_md    = font(15, bold=True)
        self.font_sm    = font(12, bold=True)

        self.cursor  = 0     # 현재 선택 인덱스
        self.done    = False
        self.result  = None  # 선택된 stage dict
        self._t      = 0.0

        total_w  = len(STAGES) * CARD_W + (len(STAGES) - 1) * CARD_GAP
        self._x0 = (self.W - total_w) // 2

        rng = random.Random(77)
        self._stars = [
            (rng.randint(0, self.W), rng.randint(0, self.H),
             rng.uniform(0.3, 1.5), rng.uniform(0.2, 0.7))
            for _ in range(110)
        ]
        self._bg = self._bake_bg()
        self._preview_bg_cache = {}

        # 스테이지 플랫폼 미리보기 캐시
        self._platform_cache = {}
        for s in STAGES:
            try:
                data = StageLoader(s["path"]).load()
                self._platform_cache[s["id"]] = data["platforms"]
            except Exception:
                self._platform_cache[s["id"]] = []

    def _bake_bg(self) -> pygame.Surface:
        sf = pygame.Surface((self.W, self.H))
        for y in range(self.H):
            t = y / self.H
            pygame.draw.line(sf,
                             (int(5+t*10), int(7+t*10), int(18+t*25)),
                             (0, y), (self.W, y))
        return sf

    # ── 이벤트 ────────────────────────────────────────────────
    def handle_event(self, event: pygame.event.Event):
        if event.type != pygame.KEYDOWN:
            return
        k = event.key
        n = len(STAGES)

        if k in (pygame.K_a, pygame.K_LEFT):
            self.cursor = (self.cursor - 1) % n
        elif k in (pygame.K_d, pygame.K_RIGHT):
            self.cursor = (self.cursor + 1) % n
        elif k in (pygame.K_RETURN, pygame.K_f, pygame.K_l):
            self.result = STAGES[self.cursor]
            self.done   = True

    def update(self):
        self._t += 0.035

    # ── draw ──────────────────────────────────────────────────
    def draw(self):
        self.screen.blit(self._bg, (0, 0))

        # 별
        for sx, sy, sr, sa in self._stars:
            fl = sa + math.sin(self._t * 2.1 + sx * 0.01) * 0.16
            c  = int(max(0, min(255, fl * 255)))
            pygame.draw.circle(self.screen, (c, c, c), (sx, sy), int(sr))

        # 선택된 스테이지 배경 컬러 워시
        self._draw_bg_wash()

        self._draw_title()

        for i, stage in enumerate(STAGES):
            self._draw_card(i, stage)

        self._draw_detail_panel()
        self._draw_guide()

    def _draw_bg_wash(self):
        col = STAGES[self.cursor]["theme"]
        sf  = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        for y in range(self.H):
            a = int(18 * (1 - y / self.H))
            pygame.draw.line(sf, (*col, a), (0, y), (self.W, y))
        self.screen.blit(sf, (0, 0))

    def _load_preview_bg(self, stage_id: str, size: tuple[int, int]):
        """
        stage_01 -> assets/images/bg_stage_01.png
        없으면 assets/images/bg_default.png
        그것도 없으면 None
        """
        key = (stage_id, size)

        if key in self._preview_bg_cache:
            return self._preview_bg_cache[key]

        candidates = [
            f"assets/images/bg_{stage_id}.png",
            f"assets/images/bg_{stage_id}.jpg",
            f"assets/images/bg_{stage_id}.jpeg",
            "assets/images/bg_default.png",
            "assets/images/bg_default.jpg",
            "assets/images/bg_default.jpeg",
        ]

        for path in candidates:
            if not os.path.exists(path):
                continue

            try:
                img = pygame.image.load(path).convert()
                img = pygame.transform.smoothscale(img, size)
                self._preview_bg_cache[key] = img
                return img
            except pygame.error:
                pass

        self._preview_bg_cache[key] = None
        return None

    def _draw_title(self):
        t = self.font_title.render("STAGE  SELECT", True, (255, 255, 255))
        self.screen.blit(t, (self.W//2 - t.get_width()//2, 34))
        lx = self.W//2 - 180
        pygame.draw.line(self.screen, (70, 100, 220), (lx, 86), (lx+360, 86), 2)

    def _card_rect(self, i) -> pygame.Rect:
        x = self._x0 + i * (CARD_W + CARD_GAP)
        return pygame.Rect(x, 118, CARD_W, CARD_H)

    def _draw_card(self, i, stage):
        r      = self._card_rect(i)
        col    = stage["theme"]
        glw    = tuple(min(255, c + 80) for c in col)
        sel    = (i == self.cursor)
        off    = -int(abs(math.sin(self._t * 2.2)) * 10) if sel else 0
        rx, ry = r.x, r.y + off

        # ── 카드 배경 ──
        card = pygame.Surface((CARD_W, CARD_H), pygame.SRCALPHA)
        for cy in range(CARD_H):
            ratio = cy / CARD_H
            a = int(35 + ratio * 25)
            pygame.draw.line(card, (*col, a), (0, cy), (CARD_W, cy))
        bw = 3 if sel else 1
        pygame.draw.rect(card, (*glw, 200 if sel else 50),
                         (0, 0, CARD_W, CARD_H), bw, border_radius=14)
        self.screen.blit(card, (rx, ry))

        # ── 플랫폼 미리보기 ──
        self._draw_stage_preview(stage["id"], rx, ry, col, glw, sel)

        # ── 스테이지 이름 ──
        nm = self.font_lg.render(stage["name"], True, (255, 255, 255))
        self.screen.blit(nm, (rx + CARD_W//2 - nm.get_width()//2,
                               ry + 195))

        # ── 구분선 ──
        pygame.draw.line(self.screen, (*glw, 100),
                         (rx+16, ry+218), (rx+CARD_W-16, ry+218), 1)

        # ── 부제 ──
        sub = self.font_sm.render(stage["sub"], True, (190, 190, 215))
        self.screen.blit(sub, (rx + CARD_W//2 - sub.get_width()//2,
                                ry + 225))

        # ── 태그 뱃지 ──
        tag = self.font_sm.render(stage["tag"], True, glw)
        tbg = pygame.Surface((tag.get_width()+16, 20), pygame.SRCALPHA)
        pygame.draw.rect(tbg, (*col, 160), tbg.get_rect(), border_radius=6)
        pygame.draw.rect(tbg, (*glw, 200), tbg.get_rect(), 1, border_radius=6)
        tbg.blit(tag, (8, 3))
        self.screen.blit(tbg, (rx + CARD_W//2 - tbg.get_width()//2,
                                ry + 248))

        # ── 넘버 ──
        num = self.font_sm.render(f"0{i+1}", True, (*glw, ))
        self.screen.blit(num, (rx + 10, ry + 10))

        # ── 선택 화살표 ──
        if sel:
            acx = rx + CARD_W//2
            tip = ry - 32 - int(abs(math.sin(self._t * 3.5)) * 8)
            pygame.draw.polygon(self.screen, glw,
                                [(acx, tip), (acx-12, tip+16), (acx+12, tip+16)])

    def _draw_stage_preview(self, stage_id, rx, ry, col, glw, sel):
        """플랫폼 배치를 썸네일로 렌더링."""
        PW, PH = CARD_W - 24, 160
        px, py = rx + 12, ry + 24

        # 배경 박스
        bg_img = self._load_preview_bg(stage_id, (PW, PH))

        if bg_img is not None:
            self.screen.blit(bg_img, (px, py))

            shade = pygame.Surface((PW, PH), pygame.SRCALPHA)
            shade.fill((0, 0, 0, 70))
            self.screen.blit(shade, (px, py))

            pygame.draw.rect(self.screen, (*col, 100), (px, py, PW, PH), 1, border_radius=8)

        else:
            bg = pygame.Surface((PW, PH), pygame.SRCALPHA)
            pygame.draw.rect(bg, (8, 10, 24, 200), (0, 0, PW, PH), border_radius=8)
            pygame.draw.rect(bg, (*col, 80), (0, 0, PW, PH), 1, border_radius=8)
            self.screen.blit(bg, (px, py))

        # 스테이지 전체 범위 → 썸네일 좌표 변환
        plats = self._platform_cache.get(stage_id, [])
        if not plats:
            no = self.font_sm.render("NO DATA", True, (100,100,120))
            self.screen.blit(no, (px + PW//2 - no.get_width()//2, py + PH//2 - 8))
            return

        min_x = min(p.x for p in plats)
        max_x = max(p.x + p.w for p in plats)
        min_y = min(p.y for p in plats)
        max_y = max(p.y + p.h for p in plats)
        sw    = max(max_x - min_x, 1)
        sh    = max(max_y - min_y, 1)

        margin = 10
        scale  = min((PW - margin*2) / sw, (PH - margin*2) / sh) * 0.92

        def to_screen(wx, wy):
            tx = px + margin + int((wx - min_x) * scale)
            ty = py + margin + int((wy - min_y) * scale)
            return tx, ty

        for p in plats:
            sx, sy   = to_screen(p.x, p.y)
            pw_s     = max(4, int(p.w * scale))
            ph_s     = max(3, int(p.h * scale))
            is_main  = p.h > 30
            bc = tuple(min(255, c + (20 if is_main else 0)) for c in col)
            tc = tuple(min(255, c + 80) for c in col)
            pygame.draw.rect(self.screen, bc, (sx, sy, pw_s, ph_s), border_radius=3)
            pygame.draw.rect(self.screen, tc, (sx, sy, pw_s, 3),    border_radius=3)

        # 스폰 위치 점
        for sp_x, sp_y, sp_col in [(260, 300, (110,185,255)), (880, 300, (255,130,110))]:
            sx, sy = to_screen(sp_x, sp_y)
            if px <= sx <= px+PW and py <= sy <= py+PH:
                pygame.draw.circle(self.screen, sp_col, (sx, sy), 5)
                pygame.draw.circle(self.screen, (255,255,255), (sx, sy), 5, 1)

    def _draw_detail_panel(self):
        """하단 선택 스테이지 상세 패널."""
        s   = STAGES[self.cursor]
        col = s["theme"]
        glw = tuple(min(255, c+80) for c in col)

        pw, ph = 500, 68
        px = self.W//2 - pw//2
        py = 118 + CARD_H + 14

        panel = pygame.Surface((pw, ph), pygame.SRCALPHA)
        pygame.draw.rect(panel, (5, 8, 22, 195), (0, 0, pw, ph), border_radius=10)
        pygame.draw.rect(panel, (*col, 80),  (0, 0, 4, ph), border_radius=10)
        pygame.draw.rect(panel, (*glw, 60), (0, 0, pw, ph), 1, border_radius=10)
        self.screen.blit(panel, (px, py))

        nm_t = self.font_md.render(f"[ {s['name']} ]", True, glw)
        self.screen.blit(nm_t, (px + 14, py + 8))

        sb_t = self.font_sm.render(s["sub"], True, (190, 190, 220))
        self.screen.blit(sb_t, (px + 14, py + 30))

        tg_t = self.font_sm.render(f"STYLE: {s['tag']}", True, glw)
        self.screen.blit(tg_t, (px + 14, py + 48))

    def _draw_guide(self):
        rows = [
            "A / D  또는  ← / →   스테이지 선택",
            "ENTER / F / L   선택 확정",
        ]
        for i, txt in enumerate(rows):
            sf = self.font_sm.render(txt, True, (160, 160, 190))
            self.screen.blit(sf, (self.W//2 - sf.get_width()//2,
                                  self.H - 46 + i * 20))
