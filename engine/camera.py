"""
Camera — 스매시 브라더스 스타일 자동 줌 + 위치 추적

외부에서 쓰는 API:
    camera.update(rects)              매 프레임 호출 (살아있는 rect 목록)
    camera.apply_rect(rect)           world Rect → screen Rect
    camera.world_to_screen(x, y)      world 좌표 → screen 픽셀
    camera.apply_point(x, y)          world_to_screen 별칭
    camera.offset                     Vector2 (하위 호환용)
"""
import pygame
import math


class Camera:
    MIN_ZOOM  = 0.55
    MAX_ZOOM  = 1.10
    PADDING   = 220     # 캐릭터 주변 여유 픽셀 (world 단위)
    LERP_POS  = 0.08    # 위치 보간 속도
    LERP_ZOOM = 0.05    # 줌 보간 속도

    def __init__(self, sw: int, sh: int):
        self.sw = sw
        self.sh = sh
        self.offset = pygame.Vector2(0, 0)   # world 좌표계 좌상단
        self._tx    = 0.0
        self._ty    = 0.0
        self.zoom   = 1.0
        self._tz    = 1.0

    # ─── 매 프레임 호출 ─────────────────────────────────────────
    def update(self, rects: list[pygame.Rect]):
        """살아있는 캐릭터 rect 목록을 받아 카메라 위치·줌 갱신."""
        if not rects:
            return

        min_x = min(r.centerx for r in rects)
        max_x = max(r.centerx for r in rects)
        min_y = min(r.centery for r in rects)
        max_y = max(r.centery for r in rects)

        span_x = (max_x - min_x) + self.PADDING * 2
        span_y = (max_y - min_y) + self.PADDING * 2

        zoom_x = self.sw / max(span_x, 1)
        zoom_y = self.sh / max(span_y, 1)
        self._tz = max(self.MIN_ZOOM, min(self.MAX_ZOOM, min(zoom_x, zoom_y)))

        self.zoom += (self._tz - self.zoom) * self.LERP_ZOOM

        cx = (min_x + max_x) / 2
        cy = (min_y + max_y) / 2
        self._tx = cx - (self.sw / 2) / self.zoom
        self._ty = cy - (self.sh / 2) / self.zoom

        self.offset.x += (self._tx - self.offset.x) * self.LERP_POS
        self.offset.y += (self._ty - self.offset.y) * self.LERP_POS
        self.offset.y  = max(-200.0, min(self.offset.y, 300.0))

    # 하위 호환: game.py 등에서 follow_multi 로 호출하던 곳 대응
    def follow_multi(self, rects: list[pygame.Rect]):
        self.update(rects)

    # ─── 좌표 변환 ──────────────────────────────────────────────
    def world_to_screen(self, wx: float, wy: float) -> tuple[int, int]:
        return (int((wx - self.offset.x) * self.zoom),
                int((wy - self.offset.y) * self.zoom))

    def apply_rect(self, rect: pygame.Rect) -> pygame.Rect:
        sx, sy = self.world_to_screen(rect.x, rect.y)
        return pygame.Rect(sx, sy,
                           int(rect.w * self.zoom),
                           int(rect.h * self.zoom))

    def apply_point(self, x: float, y: float) -> tuple[int, int]:
        return self.world_to_screen(x, y)
