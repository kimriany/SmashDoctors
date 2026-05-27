import pygame
import random
import math
from settings import MAX_PARTICLES


class Particle:
    __slots__ = ('x', 'y', 'vx', 'vy', 'life', 'max_life', 'r', 'color', 'gravity')

    def __init__(self, x, y, color, vx=0, vy=0, life=30, r=4, gravity=0.15):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.life = life
        self.max_life = life
        self.r = r
        self.color = color
        self.gravity = gravity

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += self.gravity
        self.vx *= 0.96
        self.life -= 1

    @property
    def alive(self):
        return self.life > 0

    def draw(self, surface, cam_offset):
        alpha = self.life / self.max_life
        r = max(1, int(self.r * alpha))
        sx = int(self.x - cam_offset.x)
        sy = int(self.y - cam_offset.y)
        if -r < sx < surface.get_width() + r and -r < sy < surface.get_height() + r:
            color = (
                int(self.color[0] * alpha),
                int(self.color[1] * alpha),
                int(self.color[2] * alpha),
            )
            pygame.draw.circle(surface, color, (sx, sy), r)


class ParticleSystem:
    def __init__(self):
        self.particles = []

    def spawn(self, x, y, color, count=8, speed=4.0, spread_angle=360, gravity=0.15, life=30, r=4):
        for _ in range(count):
            angle = math.radians(random.uniform(0, spread_angle))
            sp = random.uniform(speed * 0.4, speed)
            vx = math.cos(angle) * sp
            vy = math.sin(angle) * sp - random.uniform(0, 2)
            self.particles.append(
                Particle(x, y, color, vx=vx, vy=vy, life=life + random.randint(-5, 5), r=r, gravity=gravity)
            )
        # 최대 파티클 초과 시 오래된 것 제거
        if len(self.particles) > MAX_PARTICLES:
            self.particles = self.particles[-MAX_PARTICLES:]

    def spawn_hit(self, x, y, color):
        self.spawn(x, y, color, count=14, speed=5, life=28, r=5)
        self.spawn(x, y, (255, 240, 180), count=6, speed=3, life=18, r=3)

    def spawn_jump(self, x, y, color):
        self.spawn(x, y, color, count=8, speed=3, spread_angle=180, gravity=0.2, life=20, r=3)

    def spawn_respawn(self, x, y, color):
        self.spawn(x, y, color, count=30, speed=6, life=50, r=6)

    def spawn_skill(self, x, y, color):
        self.spawn(x, y, color, count=20, speed=7, life=40, r=7)
        self.spawn(x, y, (255, 255, 255), count=8, speed=4, life=20, r=3)

    def update(self):
        self.particles = [p for p in self.particles if p.alive]
        for p in self.particles:
            p.update()

    def draw(self, surface, cam_offset):
        for p in self.particles:
            p.draw(surface, cam_offset)
