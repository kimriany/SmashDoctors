"""
캐릭터 선택창 — 완전 재작성
P1(A/D/F확정/G취소), P2(←/→/L확정/;취소)
캐릭터 픽셀아트 프리뷰 + 스탯 바 + 스킬 설명 포함
"""
import pygame
import math
import random
import os

from entities.characters.doctor_blue   import DoctorBlue
from entities.characters.doctor_red    import DoctorRed
from entities.characters.doctor_green  import DoctorGreen
from entities.characters.doctor_purple import DoctorPurple

ROSTER = [DoctorBlue, DoctorRed, DoctorGreen, DoctorPurple]

CARD_W   = 220
CARD_H   = 320
CARD_GAP = 30
CARD_Y   = 155


class CharacterSelect:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.W = screen.get_width()
        self.H = screen.get_height()

        self.font_title = pygame.font.SysFont("Arial", 42, bold=True)
        self.font_lg    = pygame.font.SysFont("Arial", 22, bold=True)
        self.font_md    = pygame.font.SysFont("Arial", 15, bold=True)
        self.font_sm    = pygame.font.SysFont("Arial", 12, bold=True)

        self.cursors = [0, 1]
        self.locked  = [False, False]
        self._t      = 0.0
        self.done    = False
        self.result  = (None, None)

        total_w  = len(ROSTER) * CARD_W + (len(ROSTER) - 1) * CARD_GAP
        self._x0 = (self.W - total_w) // 2

        rng = random.Random(13)
        self._stars = [
            (rng.randint(0, self.W), rng.randint(0, self.H),
             rng.uniform(0.3, 1.5), rng.uniform(0.2, 0.7))
            for _ in range(110)
        ]

        # 배경 캐시
        self._bg = self._bake_bg()

        # 캐릭터 스프라이트 썸네일 캐시 (SPRITE_IDLE or SPRITE_PATH)
        # 이미지 없으면 None → 도형 미리보기로 폴백
        THUMB_W, THUMB_H = 90, 110
        self._char_thumbs: dict[str, pygame.Surface | None] = {}
        for cls in ROSTER:
            path = getattr(cls, "SPRITE_IDLE", None) or getattr(cls, "SPRITE_PATH", None)
            thumb = None
            if path and os.path.exists(path):
                try:
                    img = pygame.image.load(path).convert_alpha()
                    thumb = pygame.transform.smoothscale(img, (THUMB_W, THUMB_H))
                except Exception as e:
                    print(f"[CharSelect] 썸네일 로드 실패: {e}")
            self._char_thumbs[cls.__name__] = thumb

    def _bake_bg(self) -> pygame.Surface:
        sf = pygame.Surface((self.W, self.H))
        for y in range(self.H):
            t = y / self.H
            pygame.draw.line(sf,
                             (int(6+t*12), int(8+t*12), int(20+t*28)),
                             (0, y), (self.W, y))
        return sf

    # ── 이벤트 ────────────────────────────────────────────────
    def handle_event(self, event: pygame.event.Event):
        if event.type != pygame.KEYDOWN:
            return
        k = event.key

        if not self.locked[0]:
            if   k == pygame.K_a:      self.cursors[0] = (self.cursors[0]-1) % len(ROSTER)
            elif k == pygame.K_d:      self.cursors[0] = (self.cursors[0]+1) % len(ROSTER)
            elif k in (pygame.K_f, pygame.K_RETURN): self.locked[0] = True
        else:
            if k == pygame.K_g:        self.locked[0] = False

        if not self.locked[1]:
            if   k == pygame.K_LEFT:   self.cursors[1] = (self.cursors[1]-1) % len(ROSTER)
            elif k == pygame.K_RIGHT:  self.cursors[1] = (self.cursors[1]+1) % len(ROSTER)
            elif k in (pygame.K_l,):   self.locked[1] = True
        else:
            if k == pygame.K_SEMICOLON: self.locked[1] = False

        if all(self.locked):
            self.result = (ROSTER[self.cursors[0]], ROSTER[self.cursors[1]])
            self.done   = True

    def update(self):
        self._t += 0.04

    # ── draw ──────────────────────────────────────────────────
    def draw(self):
        # 배경
        self.screen.blit(self._bg, (0, 0))
        for sx, sy, sr, sa in self._stars:
            fl = sa + math.sin(self._t * 2 + sx * 0.01) * 0.15
            c  = int(max(0, min(255, fl * 255)))
            pygame.draw.circle(self.screen, (c, c, c), (sx, sy), int(sr))

        self._draw_title()

        for i, cls in enumerate(ROSTER):
            self._draw_card(i, cls)

        for pid in range(2):
            self._draw_cursor(pid)

        self._draw_info_panels()
        self._draw_guide()

    def _draw_title(self):
        t = self.font_title.render("CHARACTER  SELECT", True, (255, 255, 255))
        self.screen.blit(t, (self.W//2 - t.get_width()//2, 34))
        lx = self.W//2 - 200
        pygame.draw.line(self.screen, (70, 100, 220), (lx, 88), (lx+400, 88), 2)

    def _card_rect(self, i):
        x = self._x0 + i * (CARD_W + CARD_GAP)
        return pygame.Rect(x, CARD_Y, CARD_W, CARD_H)

    def _draw_card(self, i, cls):
        r   = self._card_rect(i)
        col = cls.PREVIEW_COLOR
        glw = tuple(min(255, c + 80) for c in col)

        p1h = self.cursors[0] == i
        p2h = self.cursors[1] == i
        hovered = p1h or p2h

        off = -int(abs(math.sin(self._t * 2.2)) * 9) if hovered else 0
        rx, ry = r.x, r.y + off

        # ── 카드 배경 ──
        card = pygame.Surface((CARD_W, CARD_H), pygame.SRCALPHA)
        # 그라디언트 효과 (위→아래)
        for cy in range(CARD_H):
            ratio = cy / CARD_H
            a = int(38 + ratio * 22)
            pygame.draw.line(card, (*col, a), (0, cy), (CARD_W, cy))
        pygame.draw.rect(card, (*glw, 55 if hovered else 30),
                         (0, 0, CARD_W, CARD_H), 2, border_radius=14)
        self.screen.blit(card, (rx, ry))

        # ── 캐릭터 픽셀아트 미리보기 ──
        self._draw_char_preview(cls, rx + CARD_W//2, ry + 95, col, glw)

        # ── 캐릭터 이름 ──
        nm = self.font_lg.render(cls.DISPLAY_NAME, True, (255, 255, 255))
        self.screen.blit(nm, (rx + CARD_W//2 - nm.get_width()//2, ry + 178))

        # ── 구분선 ──
        pygame.draw.line(self.screen, (*glw, 120),
                         (rx + 16, ry + 200), (rx + CARD_W - 16, ry + 200), 1)

        # ── 스탯 바 3종 ──
        stats = [
            ("SPD", min(1.0, cls.WALK_SPEED / 8.5)),
            ("PWR", min(1.0, cls.ATTACK_DMG / 18.0)),
            ("JMP", min(1.0, (abs(cls.JUMP_POWER) + (cls.MAX_JUMPS - 2) * 3) / 22.0)),
        ]
        for si, (lb, v) in enumerate(stats):
            self._draw_stat_bar(rx + 16, ry + 212 + si * 30,
                                CARD_W - 32, lb, v, col, glw)

        # ── 스킬 이름 ──
        sk_txt = self.font_sm.render(f"✦ {cls.SKILL_NAME}", True,
                                     tuple(min(255, c+60) for c in col))
        self.screen.blit(sk_txt, (rx + CARD_W//2 - sk_txt.get_width()//2,
                                  ry + CARD_H - 28))

        # ── LOCKED 오버레이 ──
        if (p1h and self.locked[0]) or (p2h and self.locked[1]):
            lo = pygame.Surface((CARD_W, CARD_H), pygame.SRCALPHA)
            pygame.draw.rect(lo, (*col, 55), (0, 0, CARD_W, CARD_H), border_radius=14)
            self.screen.blit(lo, (rx, ry))
            lt = self.font_md.render("✔ LOCKED IN", True, (255, 255, 255))
            self.screen.blit(lt, (rx + CARD_W//2 - lt.get_width()//2,
                                  ry + CARD_H - 30))

    def _draw_char_preview(self, cls, cx, cy, col, glw):
        """캐릭터 미리보기 — 이미지 있으면 썸네일, 없으면 도형."""
        import math as m
        bob   = int(m.sin(self._t * 2.5) * 3)
        thumb = self._char_thumbs.get(cls.__name__)

        # 배경 원 글로우
        for rr, aa in [(60, 28), (52, 52)]:
            gs = pygame.Surface((rr*2, rr*2), pygame.SRCALPHA)
            pygame.draw.circle(gs, (*col, aa), (rr, rr), rr)
            self.screen.blit(gs, (cx - rr, cy - rr))

        if thumb is not None:
            # ── 이미지 썸네일 ──
            tw, th = thumb.get_size()
            self.screen.blit(thumb, (cx - tw//2, cy - th//2 + bob))
            # 외곽 링
            pygame.draw.circle(self.screen, glw, (cx, cy + bob//2), 52, 2)
        else:
            # ── 도형 미리보기 ──
            sh = pygame.Surface((52, 10), pygame.SRCALPHA)
            pygame.draw.ellipse(sh, (0, 0, 0, 70), sh.get_rect())
            self.screen.blit(sh, (cx - 26, cy + 36 + bob))

            tc = cls.TRIM_COLOR
            pygame.draw.rect(self.screen, tc,
                             (cx - 18, cy + 18 + bob, 13, 18), border_radius=3)
            pygame.draw.rect(self.screen, tc,
                             (cx + 5,  cy + 18 + bob, 13, 18), border_radius=3)
            pygame.draw.rect(self.screen, col,
                             (cx - 20, cy - 4 + bob, 40, 24), border_radius=6)
            pygame.draw.rect(self.screen, tc,
                             (cx - 18, cy - 2 + bob, 10, 20), border_radius=2)
            pygame.draw.rect(self.screen, col,
                             (cx - 16, cy - 30 + bob, 32, 26), border_radius=9)
            pygame.draw.rect(self.screen, tc,
                             (cx - 13, cy - 28 + bob, 26, 9), border_radius=5)
            pygame.draw.rect(self.screen, (210, 235, 255),
                             (cx + 2, cy - 20 + bob, 11, 9), border_radius=2)
            pygame.draw.rect(self.screen, (90, 100, 130),
                             (cx + 2, cy - 20 + bob, 11, 9), 1, border_radius=2)
            pygame.draw.circle(self.screen, (15, 15, 35),
                               (cx + 8, cy - 16 + bob), 3)
            pygame.draw.circle(self.screen, (255, 255, 255),
                               (cx + 6, cy - 18 + bob), 1)
            pygame.draw.circle(self.screen, glw, (cx, cy), 52, 2)

    def _draw_stat_bar(self, x, y, w, label, ratio, col, glw):
        lb = self.font_sm.render(label, True, (180, 180, 215))
        self.screen.blit(lb, (x, y + 1))
        bx, bw = x + 38, w - 42
        # 배경
        pygame.draw.rect(self.screen, (18, 15, 38),
                         (bx, y + 2, bw, 12), border_radius=4)
        fw = int(bw * ratio)
        if fw > 0:
            pygame.draw.rect(self.screen, col,
                             (bx, y + 2, fw, 12), border_radius=4)
            pygame.draw.rect(self.screen, glw,
                             (bx, y + 2, fw, 3), border_radius=4)
        pygame.draw.rect(self.screen, (70, 60, 120),
                         (bx, y + 2, bw, 12), 1, border_radius=4)

    def _draw_cursor(self, pid):
        i   = self.cursors[pid]
        r   = self._card_rect(i)
        col = (110, 185, 255) if pid == 0 else (255, 130, 110)
        lbl = "P1" if pid == 0 else "P2"
        off = -int(abs(math.sin(self._t * 2.2)) * 9)
        rx, ry = r.x, r.y + off

        # 테두리 글로우 (2겹)
        for bw, aa in [(5, 80), (2, 220)]:
            gs = pygame.Surface((CARD_W + 20, CARD_H + 20), pygame.SRCALPHA)
            pygame.draw.rect(gs, (*col, aa),
                             (0, 0, CARD_W+20, CARD_H+20), bw, border_radius=17)
            self.screen.blit(gs, (rx - 10, ry - 10))

        # P1/P2 배지
        badge = pygame.Surface((46, 24), pygame.SRCALPHA)
        badge.fill((*col, 230))
        pygame.draw.rect(badge, (255,255,255,60),
                         badge.get_rect(), 1, border_radius=5)
        bt = self.font_sm.render(lbl, True, (255, 255, 255))
        badge.blit(bt, (23 - bt.get_width()//2, 5))
        bxo = 0 if pid == 0 else CARD_W - 46
        self.screen.blit(badge, (rx + bxo, ry - 28))

        # 위 화살표
        acx = rx + CARD_W // 2
        tip = ry - 34 - int(abs(math.sin(self._t * 3.5)) * 7)
        pygame.draw.polygon(self.screen, col,
                            [(acx, tip), (acx-11, tip+15), (acx+11, tip+15)])

    def _draw_info_panels(self):
        """하단 양쪽 선택 캐릭터 설명 패널."""
        panels = [
            (self.cursors[0], 0, 20),
            (self.cursors[1], 1, self.W - 220),
        ]
        for idx, pid, px in panels:
            cls = ROSTER[idx]
            col = cls.PREVIEW_COLOR
            glw = tuple(min(255, c+80) for c in col)
            pc  = (110,185,255) if pid==0 else (255,130,110)
            py  = CARD_Y + CARD_H + 16
            pw, ph = 200, 100

            panel = pygame.Surface((pw, ph), pygame.SRCALPHA)
            pygame.draw.rect(panel, (5, 8, 22, 190),
                             (0, 0, pw, ph), border_radius=10)
            pygame.draw.rect(panel, (*pc, 160),
                             (0, 0, 4, ph), border_radius=10)
            pygame.draw.rect(panel, (*pc, 60),
                             (0, 0, pw, ph), 1, border_radius=10)
            self.screen.blit(panel, (px, py))

            pnm = self.font_md.render(f"P{pid+1}: {cls.DISPLAY_NAME}",
                                      True, pc)
            self.screen.blit(pnm, (px + 10, py + 8))

            sk = list(cls.__dict__.get('SKILL_NAME', cls.SKILL_NAME)
                      if 'SKILL_NAME' in cls.__dict__ else [cls.SKILL_NAME])
            sk_txt = self.font_sm.render(
                f"스킬: {cls.SKILL_NAME}", True, glw)
            self.screen.blit(sk_txt, (px + 10, py + 30))

            # 한줄 설명
            for li, line in enumerate(cls.DESCRIPTION.split('\n')[:2]):
                lt = self.font_sm.render(line, True, (190, 190, 210))
                self.screen.blit(lt, (px + 10, py + 52 + li * 18))

    def _draw_guide(self):
        rows = [
            ("P1:  A/D 이동    F 선택    G 취소", (110, 185, 255)),
            ("P2:  ←/→ 이동   L 선택    ; 취소", (255, 130, 110)),
        ]
        for i, (txt, col) in enumerate(rows):
            sf = self.font_sm.render(txt, True, col)
            self.screen.blit(sf,
                             (self.W//2 - sf.get_width()//2,
                              self.H - 48 + i * 20))

        if all(self.locked):
            fc = (255, int(200 + math.sin(self._t * 6) * 55), 80)
            go = self.font_lg.render("PRESS  ENTER  →  STAGE SELECT", True, fc)
            self.screen.blit(go, (self.W//2 - go.get_width()//2, self.H - 88))
