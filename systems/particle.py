"""파티클 시스템."""
import pygame
import random
import math
from settings import MAX_PARTICLES


class Particle:
    __slots__ = ('x','y','vx','vy','life','max_life','r','color','gravity','glow')

    def __init__(self, x, y, color, vx=0, vy=0, life=30, r=4, gravity=0.14, glow=False):
        self.x=float(x); self.y=float(y)
        self.vx=vx;      self.vy=vy
        self.life=life;  self.max_life=life
        self.r=r;        self.color=color
        self.gravity=gravity; self.glow=glow

    def update(self):
        self.x+=self.vx; self.y+=self.vy
        self.vy+=self.gravity; self.vx*=0.955; self.life-=1

    @property
    def alive(self): return self.life > 0

    def draw(self, surface, cam):
        a   = self.life / self.max_life
        r   = max(1, int(self.r * (0.4 + 0.6*a)))
        # camera.world_to_screen 사용
        sx, sy = cam.world_to_screen(self.x, self.y)
        W, H = surface.get_size()
        if not (-r < sx < W+r and -r < sy < H+r):
            return
        col = (int(self.color[0]*a), int(self.color[1]*a), int(self.color[2]*a))
        if self.glow and r > 2:
            gs = pygame.Surface((r*4, r*4), pygame.SRCALPHA)
            pygame.draw.circle(gs, (*self.color, int(60*a)), (r*2,r*2), r*2)
            pygame.draw.circle(gs, col, (r*2,r*2), r)
            surface.blit(gs, (sx-r*2, sy-r*2), special_flags=pygame.BLEND_RGBA_ADD)
        else:
            pygame.draw.circle(surface, col, (sx, sy), r)


class ParticleSystem:
    def __init__(self):
        self.particles: list[Particle] = []

    def spawn(self, x, y, color, count=8, speed=4.0, gravity=0.14, life=30, r=4, glow=False):
        for _ in range(count):
            angle = random.uniform(0, math.pi*2)
            sp    = random.uniform(speed*0.35, speed)
            self.particles.append(Particle(
                x, y, color,
                vx=math.cos(angle)*sp, vy=math.sin(angle)*sp - random.uniform(0,1.5),
                life=life+random.randint(-6,6), r=r, gravity=gravity, glow=glow
            ))
        if len(self.particles) > MAX_PARTICLES:
            self.particles = self.particles[-MAX_PARTICLES:]

    def spawn_hit(self, x, y, color):
        self.spawn(x,y,color, count=14, speed=6, life=28, r=5, glow=True)
        self.spawn(x,y,(255,240,180), count=7, speed=3.5, life=18, r=3)
        self._ring(x, y, color)

    def _ring(self, x, y, color):
        for i in range(16):
            ang = (i/16)*math.pi*2
            spd = 5.5+random.uniform(0,2)
            self.particles.append(Particle(x,y,color,
                vx=math.cos(ang)*spd, vy=math.sin(ang)*spd,
                life=14, r=3, gravity=-0.05, glow=True))

    def spawn_jump(self, x, y, color):
        self.spawn(x,y,color, count=10, speed=3.5, gravity=0.18, life=22, r=4)

    def spawn_respawn(self, x, y, color):
        self.spawn(x,y,color, count=28, speed=7, life=55, r=7, glow=True)

    def spawn_skill(self, x, y, color):
        self.spawn(x,y,color, count=22, speed=8, life=44, r=8, glow=True)
        self.spawn(x,y,(255,255,255), count=10, speed=4, life=22, r=3)
        self._ring(x, y, color)

    def update(self):
        live = [p for p in self.particles if p.alive]
        for p in live: p.update()
        self.particles = [p for p in live if p.alive]

    def draw(self, surface, cam):
        """cam = Camera 인스턴스 (world_to_screen 사용)"""
        for p in self.particles:
            p.draw(surface, cam)
