"""
Opening — 게임 시작 오프닝 연출

Phase:
  0  검정 화면 페이드인 (0~30f)
  1  로고 타이핑 효과 (30~90f)
  2  부제 페이드인 (90~130f)
  3  파티클 폭발 (130~180f)
  4  타이틀 슬라이드업 (180~240f)
  5  PRESS ANY KEY 깜빡임 (240f~)

아무 키/클릭 → 스킵 가능 (Phase 3 이후부터)
"""
import pygame
import math
import random
import os


class Opening:
    TITLE    = "SMASH  DOCTORS"
    SUBTITLE = "Science  ·  Smash  ·  Survive"

    PHASE_END = [30, 90, 130, 180, 240]   # 각 페이즈 종료 프레임

    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.W = screen.get_width()
        self.H = screen.get_height()

        from systems.font_manager import font
        self.fnt_title    = font(68, bold=True)
        self.fnt_sub      = font(22, bold=True)
        self.fnt_any_key  = font(16)
        self.fnt_logo     = font(14)

        self.done    = False
        self._frame  = 0
        self._phase  = 0
        self._skip   = False

        # 배경 이미지
        self._bg: pygame.Surface | None = None
        for p in ["assets/images/opening_bg.png",
                  "assets/images/opening_bg.jpg",
                  "assets/images/bg_stage_01.jpeg"]:
            if os.path.exists(p):
                try:
                    img = pygame.image.load(p).convert()
                    self._bg = pygame.transform.smoothscale(img, (self.W, self.H))
                    break
                except Exception:
                    pass

        # 파티클
        rng = random.Random(42)
        self._particles = [
            {
                "x": self.W/2 + rng.uniform(-20, 20),
                "y": self.H/2 + rng.uniform(-10, 10),
                "vx": rng.uniform(-6, 6),
                "vy": rng.uniform(-8, 2),
                "r":  rng.uniform(2, 7),
                "col": random.choice([
                    (100, 180, 255), (255, 180, 80),
                    (180, 100, 255), (80, 220, 180),
                    (255, 100, 120),
                ]),
                "life": rng.randint(40, 80),
                "max_life": 0,
            }
            for _ in range(80)
        ]
        for p in self._particles:
            p["max_life"] = p["life"]

        # 별
        rng2 = random.Random(7)
        self._stars = [
            (rng2.randint(0, self.W), rng2.randint(0, self.H),
             rng2.uniform(0.3, 1.8), rng2.uniform(0.2, 0.8))
            for _ in range(160)
        ]

        # 배경 캐시
        self._dark_bg = self._bake_bg()

    def _bake_bg(self) -> pygame.Surface:
        sf = pygame.Surface((self.W, self.H))
        for y in range(self.H):
            t = y / self.H
            pygame.draw.line(sf,
                (int(3+t*8), int(4+t*8), int(12+t*18)),
                (0, y), (self.W, y))
        return sf

    # ── 이벤트 ──────────────────────────────────────────────────
    def handle_event(self, event: pygame.event.Event):
        if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
            if self._phase >= 3:   # Phase 3 이후부터 스킵 허용
                self.done = True

    # ── 업데이트 ────────────────────────────────────────────────
    def update(self):
        if self.done:
            return
        self._frame += 1

        # 파티클
        if self._phase >= 3:
            for p in self._particles:
                if p["life"] > 0:
                    p["x"]  += p["vx"]
                    p["y"]  += p["vy"]
                    p["vy"] += 0.18
                    p["vx"] *= 0.97
                    p["life"] -= 1

        # 페이즈 전환
        for i, end in enumerate(self.PHASE_END):
            if self._frame >= end and self._phase == i:
                self._phase = i + 1
                break

        # Phase 5: PRESS ANY KEY 단계 → 계속 유지
        if self._phase >= 5 and self._frame > self.PHASE_END[-1] + 180:
            self.done = True   # 5초 후 자동 진행

    # ── draw ────────────────────────────────────────────────────
    def draw(self):
        f = self._frame
        W, H = self.W, self.H

        # ── 배경 ──
        if self._bg and self._phase >= 2:
            bg_alpha = min(255, int(255 * (f - self.PHASE_END[1]) / 40))
            self._bg.set_alpha(bg_alpha)
            self.screen.blit(self._dark_bg, (0, 0))
            self.screen.blit(self._bg, (0, 0))
            # 어두운 오버레이
            ov = pygame.Surface((W, H), pygame.SRCALPHA)
            ov.fill((0, 0, 0, 140))
            self.screen.blit(ov, (0, 0))
        else:
            self.screen.blit(self._dark_bg, (0, 0))

        # 별
        star_alpha = min(1.0, (f - 10) / 30) if f > 10 else 0
        for sx, sy, sr, sa in self._stars:
            fl = sa * star_alpha + math.sin(f * 0.03 + sx * 0.01) * 0.1 * star_alpha
            c  = int(max(0, min(255, fl * 255)))
            pygame.draw.circle(self.screen, (c, c, c), (sx, sy), int(sr))

        # ── Phase 0: 페이드인 ──
        if self._phase == 0:
            alpha = max(0, 255 - int(255 * f / self.PHASE_END[0]))
            sf = pygame.Surface((W, H))
            sf.fill((0, 0, 0))
            sf.set_alpha(alpha)
            self.screen.blit(sf, (0, 0))
            return

        # ── Phase 1: 타이틀 타이핑 ──
        title_progress = min(1.0, (f - self.PHASE_END[0]) /
                             (self.PHASE_END[1] - self.PHASE_END[0]))
        visible_chars  = int(len(self.TITLE) * title_progress)
        shown_title    = self.TITLE[:visible_chars]

        ty = H // 2 - 40
        if self._phase >= 4:
            # Phase 4: 위로 슬라이드
            slide = (f - self.PHASE_END[3]) / (self.PHASE_END[4] - self.PHASE_END[3])
            ty    = int((H//2 - 40) + (-80) * min(1.0, slide))

        # 타이틀 글로우
        if self._phase >= 1:
            pulse = abs(math.sin(f * 0.04)) * 0.4 + 0.6
            for col, off, a in [
                ((60, 120, 255), 3, int(40 * pulse)),
                ((180, 100, 255), 2, int(25 * pulse)),
            ]:
                glow = self.fnt_title.render(shown_title, True, col)
                glow.set_alpha(a)
                for ox, oy in [(-off,0),(off,0),(0,-off),(0,off)]:
                    self.screen.blit(glow, (W//2 - glow.get_width()//2 + ox, ty + oy))

            title_sf = self.fnt_title.render(shown_title, True, (255, 255, 255))
            self.screen.blit(title_sf, (W//2 - title_sf.get_width()//2, ty))

            # 커서 깜빡임 (타이핑 중)
            if title_progress < 1.0 and (f // 8) % 2 == 0:
                cw = self.fnt_title.size(shown_title)[0]
                cx = W//2 - self.fnt_title.size(self.TITLE)[0]//2 + cw + 4
                pygame.draw.rect(self.screen, (200, 200, 255),
                                 (cx, ty + 8, 4, self.fnt_title.get_height() - 16))

        # ── Phase 2: 부제 ──
        if self._phase >= 2:
            sub_alpha = min(255, int(255 * (f - self.PHASE_END[1]) / 30))
            sub_sf    = self.fnt_sub.render(self.SUBTITLE, True, (160, 180, 230))
            sub_sf.set_alpha(sub_alpha)
            self.screen.blit(sub_sf,
                (W//2 - sub_sf.get_width()//2, ty + self.fnt_title.get_height() + 12))

            # 구분선
            line_w = int(400 * min(1.0, (f - self.PHASE_END[1]) / 25))
            line_y = ty + self.fnt_title.get_height() + 8
            if line_w > 0:
                lsf = pygame.Surface((line_w, 2), pygame.SRCALPHA)
                lsf.fill((80, 100, 200, sub_alpha))
                self.screen.blit(lsf, (W//2 - line_w//2, line_y))

        # ── Phase 3: 파티클 ──
        if self._phase >= 3:
            for p in self._particles:
                if p["life"] > 0:
                    a = int(255 * p["life"] / p["max_life"])
                    r = max(1, int(p["r"] * p["life"] / p["max_life"]))
                    gs = pygame.Surface((r*4, r*4), pygame.SRCALPHA)
                    pygame.draw.circle(gs, (*p["col"], a//3), (r*2, r*2), r*2)
                    pygame.draw.circle(gs, (*p["col"], a),    (r*2, r*2), r)
                    self.screen.blit(gs, (int(p["x"]) - r*2, int(p["y"]) - r*2))

        # ── Phase 5: PRESS ANY KEY ──
        if self._phase >= 5:
            ak_alpha = int(160 + 90 * abs(math.sin(f * 0.06)))
            ak_sf    = self.fnt_any_key.render("PRESS  ANY  KEY", True, (200, 210, 240))
            ak_sf.set_alpha(ak_alpha)
            self.screen.blit(ak_sf,
                (W//2 - ak_sf.get_width()//2, H - 80))

            # 하단 로고/버전
            ver = self.fnt_logo.render("v0.1  ·  SmashDoctors", True, (80, 85, 110))
            self.screen.blit(ver, (W//2 - ver.get_width()//2, H - 40))
