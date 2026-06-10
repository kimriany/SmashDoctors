"""
Transition — 화면 전환 이펙트 시스템

사용법:
    tr = Transition("fade", duration=30)
    tr.start()

    # 매 프레임
    tr.update()
    tr.draw(screen)
    if tr.at_midpoint:      # 여기서 씬 전환
        change_scene()
    if tr.done:
        pass                # 전환 완료

종류:
    "fade"        검정 페이드 인/아웃
    "fade_white"  흰색 페이드
    "slide_left"  왼쪽으로 슬라이드
    "slide_right" 오른쪽으로 슬라이드
    "slash"       대각선 슬래시 (빠른 전환)
    "zoom_in"     줌인
    "wipe"        수직 와이프
"""
import pygame
import math


class Transition:
    def __init__(self, kind: str = "fade", duration: int = 40):
        self.kind     = kind
        self.duration = duration
        self.half     = duration // 2
        self._frame   = 0
        self._active  = False
        self._done    = False
        self._mid     = False   # 중간 지점 플래그 (씬 전환 타이밍)

    # ── 상태 ─────────────────────────────────────────────────────
    @property
    def active(self) -> bool:  return self._active
    @property
    def done(self)   -> bool:  return self._done
    @property
    def at_midpoint(self) -> bool:
        mid = self._mid
        self._mid = False
        return mid

    def start(self):
        self._frame  = 0
        self._active = True
        self._done   = False
        self._mid    = False

    # ── 업데이트 ─────────────────────────────────────────────────
    def update(self):
        if not self._active:
            return
        prev = self._frame
        self._frame += 1

        # 중간 지점 감지
        if prev < self.half <= self._frame:
            self._mid = True

        if self._frame >= self.duration:
            self._active = False
            self._done   = True

    # ── 렌더 ─────────────────────────────────────────────────────
    def draw(self, screen: pygame.Surface):
        if not self._active and not self._done:
            return
        W, H = screen.get_size()
        t    = self._frame / self.duration     # 0.0 → 1.0
        mt   = abs(t * 2 - 1)                  # 0→1→0 (중간에 최대)

        kind = self.kind

        if kind in ("fade", "fade_white"):
            col = (0,0,0) if kind == "fade" else (255,255,255)
            alpha = int(255 * (1 - abs(t * 2 - 1)))   # 올라갔다 내려옴
            sf = pygame.Surface((W, H))
            sf.fill(col)
            sf.set_alpha(alpha)
            screen.blit(sf, (0, 0))

        elif kind == "slide_left":
            alpha = int(255 * mt)
            sf = pygame.Surface((W, H))
            sf.fill((0, 0, 0))
            sf.set_alpha(alpha)
            ox = int(-W * (1 - mt)) if t < 0.5 else int(W * (t * 2 - 1))
            screen.blit(sf, (ox, 0))

        elif kind == "slash":
            # 대각선 슬래시 여러 줄
            sf = pygame.Surface((W, H), pygame.SRCALPHA)
            alpha = int(255 * (1 - abs(t * 2 - 1)))
            n_slashes = 8
            for i in range(n_slashes):
                x = int((i / n_slashes - 0.5 + mt * 1.5) * W * 1.4)
                pts = [(x, 0), (x + W//n_slashes, 0),
                       (x + W//n_slashes - 60, H), (x - 60, H)]
                pygame.draw.polygon(sf, (10, 10, 20, alpha), pts)
            screen.blit(sf, (0, 0))

        elif kind == "wipe":
            sf = pygame.Surface((W, H), pygame.SRCALPHA)
            alpha = int(220 * (1 - abs(t * 2 - 1)))
            h = int(H * mt)
            cy = H // 2
            pygame.draw.rect(sf, (5, 8, 22, alpha),
                             (0, cy - h//2, W, h))
            screen.blit(sf, (0, 0))

        elif kind == "zoom_in":
            sf = pygame.Surface((W, H), pygame.SRCALPHA)
            alpha = int(180 * mt)
            scale = 0.8 + 0.2 * mt
            sw, sh = int(W * scale), int(H * scale)
            pygame.draw.rect(sf, (5, 8, 22, alpha),
                             ((W-sw)//2, (H-sh)//2, sw, sh),
                             border_radius=int(30 * (1-mt)))
            screen.blit(sf, (0, 0))
