import pygame


class Camera:
    def __init__(self, screen_width, screen_height):
        self.offset = pygame.Vector2(0, 0)
        self.screen_width  = screen_width
        self.screen_height = screen_height
        self._target_x = 0.0
        self._target_y = 0.0

    def follow_multi(self, rects, margin=120):
        """여러 엔티티를 동시에 프레임 안에 유지 (스매시 브라더스 스타일)"""
        if not rects:
            return

        min_x = min(r.centerx for r in rects)
        max_x = max(r.centerx for r in rects)
        min_y = min(r.centery for r in rects)
        max_y = max(r.centery for r in rects)

        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2

        self._target_x = center_x - self.screen_width  / 2
        self._target_y = center_y - self.screen_height / 2

        # 부드러운 추적
        self.offset.x += (self._target_x - self.offset.x) * 0.08
        self.offset.y += (self._target_y - self.offset.y) * 0.08

        # 수직 범위 제한
        self.offset.y = max(-150, min(self.offset.y, 200))

    def follow(self, target_rect):
        self.follow_multi([target_rect])

    def apply_rect(self, rect):
        return pygame.Rect(
            rect.x - int(self.offset.x),
            rect.y - int(self.offset.y),
            rect.w,
            rect.h,
        )

    def apply_point(self, x, y):
        return (x - int(self.offset.x), y - int(self.offset.y))
