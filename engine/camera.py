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

        self.scripted = False
        self.script_timer = 0
        self.script_total = 0

        self.script_target_rect = None
        self.script_start_offset = pygame.Vector2(0, 0)
        self.script_start_zoom = 1.0
        self.script_end_zoom = 1.45

    # ─── 매 프레임 호출 ─────────────────────────────────────────
    def update(self, rects: list[pygame.Rect]):

        if self.scripted:
            self.update_scripted()
            return

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

    def start_focus_cutscene(self, target_rect: pygame.Rect, zoom=1.45, frames=30):
        """
        특정 대상에게 카메라가 이동하면서 확대되는 컷신.
        """
        self.scripted = True
        self.script_timer = 0
        self.script_total = max(1, int(frames))

        self.script_target_rect = target_rect.copy()
        self.script_start_offset = self.offset.copy()
        self.script_start_zoom = self.zoom
        self.script_end_zoom = zoom

    def update_scripted(self):
        """
        컷신 중 카메라 업데이트.
        Game의 일반 camera.update(active)는 이 동안 호출하지 않는 게 좋다.
        """
        if not self.scripted or self.script_target_rect is None:
            return

        t = self.script_timer / max(1, self.script_total)
        t = max(0.0, min(1.0, t))

        # ease out
        ease = 1.0 - (1.0 - t) * (1.0 - t)

        self.zoom = self.script_start_zoom + (self.script_end_zoom - self.script_start_zoom) * ease

        cx = self.script_target_rect.centerx
        cy = self.script_target_rect.centery

        target_offset_x = cx - (self.sw / 2) / self.zoom
        target_offset_y = cy - (self.sh / 2) / self.zoom

        self.offset.x = self.script_start_offset.x + (target_offset_x - self.script_start_offset.x) * ease
        self.offset.y = self.script_start_offset.y + (target_offset_y - self.script_start_offset.y) * ease

        self.script_timer += 1

        if self.script_timer >= self.script_total:
            self.scripted = False