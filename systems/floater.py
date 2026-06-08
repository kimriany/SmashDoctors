from systems.font_manager import font
"""피격 데미지 수치 팝업."""
import pygame


class DamageFloater:
    def __init__(self, x, y, value, color=(255,220,50), is_skill=False):
        self.x=float(x); self.y=float(y)
        self.vy=-3.2; self.value=value
        self.color=color; self.life=55; self.max_life=55
        self.is_skill=is_skill
        size = 26 if is_skill else 21
        self._font = font(size, bold=True)

    def update(self):
        self.y+=self.vy; self.vy*=0.90; self.life-=1

    @property
    def alive(self): return self.life > 0

    def draw(self, surface, cam):
        """cam = Camera 인스턴스"""
        a  = self.life / self.max_life
        sx, sy = cam.world_to_screen(self.x, self.y)
        prefix = "★" if self.is_skill else ""
        txt = self._font.render(f"{prefix}+{self.value}%", True, self.color)
        shadow = self._font.render(f"{prefix}+{self.value}%", True, (20,20,20))
        for ox,oy in ((-1,1),(1,1),(0,2)):
            shadow.set_alpha(int(180*a))
            surface.blit(shadow, (sx - txt.get_width()//2+ox, sy - txt.get_height()//2+oy))
        txt.set_alpha(int(255*a))
        surface.blit(txt, (sx - txt.get_width()//2, sy - txt.get_height()//2))


class FloaterSystem:
    def __init__(self):
        self.floaters: list[DamageFloater] = []

    def spawn(self, x, y, value, color=(255,220,50), is_skill=False):
        self.floaters.append(DamageFloater(x, y, value, color, is_skill))

    def update(self):
        self.floaters = [f for f in self.floaters if f.alive]
        for f in self.floaters: f.update()

    def draw(self, surface, cam):
        for f in self.floaters: f.draw(surface, cam)
