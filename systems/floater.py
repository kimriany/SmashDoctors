import pygame


class DamageFloater:
    """피격 시 화면에 뜨는 데미지 숫자"""
    def __init__(self, x, y, value, color=(255, 220, 50)):
        self.x = float(x)
        self.y = float(y)
        self.vy = -2.5
        self.value = value
        self.color = color
        self.life = 50
        self.max_life = 50

    def update(self):
        self.y += self.vy
        self.vy *= 0.93
        self.life -= 1

    @property
    def alive(self):
        return self.life > 0

    def draw(self, surface, font, cam_offset):
        alpha = self.life / self.max_life
        sx = int(self.x - cam_offset.x)
        sy = int(self.y - cam_offset.y)
        text = font.render(f"-{self.value}", True, self.color)
        text.set_alpha(int(255 * alpha))
        surface.blit(text, (sx - text.get_width() // 2, sy))


class FloaterSystem:
    def __init__(self):
        self.floaters = []
        self.font = None

    def init_font(self):
        self.font = pygame.font.SysFont("Arial", 22, bold=True)

    def spawn(self, x, y, value, color=(255, 220, 50)):
        self.floaters.append(DamageFloater(x, y, value, color))

    def update(self):
        self.floaters = [f for f in self.floaters if f.alive]
        for f in self.floaters:
            f.update()

    def draw(self, surface, cam_offset):
        if not self.font:
            self.init_font()
        for f in self.floaters:
            f.draw(surface, self.font, cam_offset)
