import pygame


class Camera:
    def __init__(self, screen_width, screen_height):
        self.offset = pygame.Vector2(0, 0)
        self.screen_width = screen_width
        self.screen_height = screen_height

    def follow(self, target_rect):
        # target이 화면 중앙 근처에 오도록 이동
        target_x = target_rect.centerx - self.screen_width // 2
        target_y = target_rect.centery - self.screen_height // 2

        # 부드러운 카메라 움직임
        self.offset.x += (target_x - self.offset.x) * 0.08
        self.offset.y += (target_y - self.offset.y) * 0.08

        # 현재는 세로 카메라를 너무 많이 움직이지 않도록 제한
        self.offset.y = max(-80, min(self.offset.y, 120))

    def apply_rect(self, rect):
        return pygame.Rect(
            rect.x - int(self.offset.x),
            rect.y - int(self.offset.y),
            rect.w,
            rect.h,
        )
