import pygame
import random
import math
import os


class FinisherSystem:
    """
    영역전개 중 R키가 전환되는 필살기 시스템.

    기본 흐름:
    1. finisher_request 수신
    2. 카메라 컷신 + 캐릭터별 피니셔 연출
    3. 상대 스톡 제거
    4. 모든 영역 해제는 BattleSession의 stock_lost 처리에서 수행
    """

    EINSTEIN_BLACKHOLE_PATH = "assets/images/effects/einstein_blackhole_finisher.png"

    def __init__(self, screen, camera, event_bus, particle_sys=None):
        self.screen = screen
        self.camera = camera
        self.event_bus = event_bus
        self.particle_sys = particle_sys

        self.active = False
        self.gameplay_frozen = False

        self.owner = None
        self.target = None
        self.timer = 0
        self.total = 0
        self.kill_done = False
        self.flash_alpha = 0
        self.shake_power = 0

        self.CUTSCENE_FRAMES = 92
        self.KILL_FRAME = 54
        self.FOCUS_FRAMES = 28
        self.FOCUS_ZOOM = 1.65

        self._style = "default"
        self._hole_x = 0.0
        self._hole_y = 0.0
        self._target_start = pygame.Vector2(0, 0)
        self._owner_start = pygame.Vector2(0, 0)
        self._blackhole_img = self._load_blackhole_img()
        self._hole_focus_started = False

        self.event_bus.subscribe("finisher_request", self.on_finisher_request)

    def _load_blackhole_img(self):
        if not os.path.exists(self.EINSTEIN_BLACKHOLE_PATH):
            return None
        try:
            return pygame.image.load(self.EINSTEIN_BLACKHOLE_PATH).convert_alpha()
        except Exception as e:
            print(f"[Finisher] blackhole image load failed: {e}")
            return None

    def on_finisher_request(self, data: dict):
        if self.active:
            return

        owner = data.get("owner")
        target = data.get("target") or getattr(owner, "_skill_target", None)
        if owner is None or target is None:
            return
        if getattr(owner, "dead", False) or getattr(target, "dead", False):
            return
        if getattr(owner, "respawning", False) or getattr(target, "respawning", False):
            return

        # 단일 영역에서만 필살기 가능
        if not getattr(owner, "domain_active", False):
            return
        if getattr(owner, "finisher_locked", False):
            return
        if not getattr(owner, "finisher_ready", False):
            return

        self._style = "einstein_blackhole" if self._is_einstein(owner) else "default"
        if self._style == "einstein_blackhole":
            self.CUTSCENE_FRAMES = 128
            self.KILL_FRAME = 92
            self.FOCUS_FRAMES = 34
            self.FOCUS_ZOOM = 1.42
        else:
            self.CUTSCENE_FRAMES = 92
            self.KILL_FRAME = 54
            self.FOCUS_FRAMES = 28
            self.FOCUS_ZOOM = 1.65

        self.active = True
        self.gameplay_frozen = True
        self.owner = owner
        self.target = target
        self.timer = self.CUTSCENE_FRAMES
        self.total = self.CUTSCENE_FRAMES
        self.kill_done = False
        self.flash_alpha = 0
        self.shake_power = 0
        self._hole_focus_started = False

        self._owner_start = pygame.Vector2(owner.rect.centerx, owner.rect.centery)
        self._target_start = pygame.Vector2(target.rect.centerx, target.rect.centery)
        self._hole_x, self._hole_y = self._choose_blackhole_center(owner, target)

        # 사용 즉시 필살기 스택 소모
        owner.finisher_charge_stack = 0.0
        owner.finisher_ready = False
        owner.finisher_locked = True
        owner.finisher_unlock_timer = 0

        owner.vel = pygame.Vector2(0, 0)
        target.vel = pygame.Vector2(0, 0)
        owner.invincible = max(getattr(owner, "invincible", 0), self.CUTSCENE_FRAMES)

        if hasattr(self.camera, "start_focus_cutscene"):
            focus_rect = owner.rect if self._style != "einstein_blackhole" else self._make_focus_rect(self._hole_x, self._hole_y, 300, 260)
            self.camera.start_focus_cutscene(
                focus_rect,
                zoom=self.FOCUS_ZOOM,
                frames=self.FOCUS_FRAMES,
            )

    def _is_einstein(self, owner) -> bool:
        try:
            if owner.get_char_name() == "Einstein":
                return True
        except Exception:
            pass
        return owner.__class__.__name__ == "Einstein" or getattr(owner, "DISPLAY_NAME", "") == "Einstein"

    def _choose_blackhole_center(self, owner, target):
        # 현재 카메라 중심을 월드 좌표로 되돌려 경기장 중앙처럼 쓰되, 두 플레이어 사이에서 너무 멀어지지 않게 보정한다.
        cam_cx = self.camera.offset.x + (self.screen.get_width() * 0.5) / max(0.1, self.camera.zoom)
        cam_cy = self.camera.offset.y + (self.screen.get_height() * 0.48) / max(0.1, self.camera.zoom)
        pair_cx = (owner.rect.centerx + target.rect.centerx) * 0.5
        floor_y = max(owner.rect.bottom, target.rect.bottom)
        return (cam_cx * 0.55 + pair_cx * 0.45, min(cam_cy + 20, floor_y - 100))

    def _make_focus_rect(self, cx, cy, w, h):
        return pygame.Rect(int(cx - w / 2), int(cy - h / 2), int(w), int(h))

    def update(self):
        if not self.active:
            self.gameplay_frozen = False
            return

        self.gameplay_frozen = True

        if hasattr(self.camera, "update_scripted"):
            self.camera.update_scripted()

        elapsed = self.total - self.timer

        if self._style == "einstein_blackhole":
            self._update_einstein_blackhole(elapsed)
        else:
            self._update_default_fx(elapsed)

        if not self.kill_done and elapsed >= self.KILL_FRAME:
            self._kill_target()
            self.kill_done = True

        self.timer -= 1
        if self.timer <= 0:
            self._finish()

    def _update_default_fx(self, elapsed):
        if 24 <= elapsed <= 62:
            self.shake_power = max(0, 10 - abs(43 - elapsed) // 3)
        else:
            self.shake_power = max(0, self.shake_power - 1)

        if 44 <= elapsed <= 68:
            if elapsed <= self.KILL_FRAME:
                self.flash_alpha = min(255, self.flash_alpha + 22)
            else:
                self.flash_alpha = max(0, self.flash_alpha - 14)
        else:
            self.flash_alpha = max(0, self.flash_alpha - 18)

    def _update_einstein_blackhole(self, elapsed):
        if self.owner is None or self.target is None:
            return

        if elapsed == 18 and hasattr(self.camera, "start_focus_cutscene"):
            self.camera.start_focus_cutscene(
                self._make_focus_rect(self._hole_x, self._hole_y, 260, 230),
                zoom=1.58,
                frames=38,
            )
            self._hole_focus_started = True

        self.owner.vel = pygame.Vector2(0, 0)
        self.target.vel = pygame.Vector2(0, 0)

        pull_start = 24
        pull_end = max(pull_start + 1, self.KILL_FRAME - 8)
        if elapsed >= pull_start and not self.kill_done:
            ratio = max(0.0, min(1.0, (elapsed - pull_start) / (pull_end - pull_start)))
            ease = ratio * ratio * (3.0 - 2.0 * ratio)
            sink = math.sin(ratio * math.pi) * 18
            tx = self._target_start.x + (self._hole_x - self._target_start.x) * ease
            ty = self._target_start.y + (self._hole_y - self._target_start.y) * ease + sink
            self.target.rect.center = (int(tx), int(ty))
            self.target.invincible = max(getattr(self.target, "invincible", 0), 2)

            if self.particle_sys and elapsed % 5 == 0:
                try:
                    self.particle_sys.spawn(
                        int(tx), int(ty),
                        random.choice([(120, 190, 255), (235, 250, 255), (60, 90, 190)]),
                        count=2, speed=2.4, life=20, r=3,
                    )
                except Exception:
                    pass

        if 58 <= elapsed <= self.KILL_FRAME + 10:
            self.shake_power = max(0, 13 - abs(self.KILL_FRAME - elapsed) // 3)
        else:
            self.shake_power = max(0, self.shake_power - 1)

        if self.KILL_FRAME - 10 <= elapsed <= self.KILL_FRAME + 18:
            if elapsed <= self.KILL_FRAME:
                self.flash_alpha = min(230, self.flash_alpha + 16)
            else:
                self.flash_alpha = max(0, self.flash_alpha - 11)
        else:
            self.flash_alpha = max(0, self.flash_alpha - 14)

    def _kill_target(self):
        if self.target is None or self.owner is None:
            return
        if getattr(self.target, "dead", False):
            return

        tx, ty = self.target.rect.centerx, self.target.rect.centery

        if self.particle_sys:
            color = getattr(self.owner, "glow_color", (255, 255, 255))
            if self._style == "einstein_blackhole":
                color = (120, 190, 255)
            try:
                self.particle_sys.spawn(tx, ty, color, count=64 if self._style == "einstein_blackhole" else 48, speed=9, life=42, r=5)
            except TypeError:
                try:
                    self.particle_sys.spawn_hit(tx, ty, color)
                except Exception:
                    pass

        # Player.lose_stock 패치에서 stock_lost 이벤트가 같이 발생한다.
        try:
            self.target.lose_stock(
                self.event_bus,
                killer=self.owner,
                reason="finisher",
            )
        except TypeError:
            self.target.lose_stock(self.event_bus)
            self.event_bus.emit("stock_lost", {
                "player": self.target,
                "killer": self.owner,
                "reason": "finisher",
            })

    def _finish(self):
        self.active = False
        self.gameplay_frozen = False
        self.owner = None
        self.target = None
        self.timer = 0
        self.total = 0
        self.kill_done = False
        self.flash_alpha = 0
        self.shake_power = 0
        self._style = "default"
        self._hole_focus_started = False

    def draw_overlay(self):
        if not self.active:
            return

        if self._style == "einstein_blackhole":
            self._draw_einstein_blackhole()
        else:
            self._draw_default_overlay()

        if self.flash_alpha > 0:
            flash = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
            flash.fill((255, 255, 255, self.flash_alpha))
            self.screen.blit(flash, (0, 0))

    def _draw_default_overlay(self):
        if self.shake_power > 0:
            for _ in range(4):
                pygame.draw.rect(
                    self.screen,
                    (255, 255, 255),
                    (random.randint(0, self.screen.get_width()),
                     random.randint(0, self.screen.get_height()),
                     2, 2),
                )

    def _draw_einstein_blackhole(self):
        elapsed = self.total - self.timer
        sx, sy = self.camera.world_to_screen(self._hole_x, self._hole_y)
        z = max(0.5, self.camera.zoom)

        fade_in = max(0.0, min(1.0, elapsed / 26.0))
        kill_pulse = 1.0 + 0.28 * max(0.0, 1.0 - abs(self.KILL_FRAME - elapsed) / 16.0)
        breathe = 1.0 + math.sin(elapsed * 0.18) * 0.07
        size = int((150 + 130 * fade_in) * z * breathe * kill_pulse)
        alpha = int(235 * fade_in)

        # 암전과 중력 렌즈 느낌.
        veil = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        veil.fill((0, 0, 18, int(55 + 60 * fade_in)))
        self.screen.blit(veil, (0, 0))

        for i in range(5):
            r = int((size * 0.42 + i * 24 * z + math.sin(elapsed * 0.1 + i) * 7 * z) * kill_pulse)
            ring_alpha = max(0, int((120 - i * 16) * fade_in))
            rect = pygame.Rect(sx - r, sy - r, r * 2, r * 2)
            col = (210, 240, 255, ring_alpha) if i % 2 == 0 else (80, 150, 255, ring_alpha)
            pygame.draw.ellipse(self.screen, col, rect, max(1, int(2 * z)))

        if self._blackhole_img is not None:
            img = self._blackhole_img
            scaled = pygame.transform.smoothscale(img, (max(8, size), max(8, size)))
            angle = -elapsed * 4.5
            rotated = pygame.transform.rotozoom(scaled, angle, 1.0)
            rotated.set_alpha(alpha)
            self.screen.blit(rotated, (sx - rotated.get_width() // 2, sy - rotated.get_height() // 2))
        else:
            r = max(12, size // 2)
            pygame.draw.circle(self.screen, (10, 10, 18, alpha), (sx, sy), r)
            pygame.draw.circle(self.screen, (160, 220, 255, alpha), (sx, sy), r, max(2, int(4 * z)))

        if self.owner is not None:
            ox, oy = self.camera.world_to_screen(self.owner.rect.centerx, self.owner.rect.centery)
            for i in range(3):
                a = int((90 - i * 22) * fade_in)
                pygame.draw.line(self.screen, (150, 210, 255, a), (ox, oy - int(i * 8 * z)), (sx, sy), max(1, int((3 - i) * z)))
            pygame.draw.circle(self.screen, (230, 250, 255, int(90 * fade_in)), (ox, oy), max(8, int(18 * z)), max(1, int(2 * z)))

        if self.target is not None and not self.kill_done:
            tx, ty = self.camera.world_to_screen(self.target.rect.centerx, self.target.rect.centery)
            for i in range(4):
                t = i / 4.0
                mx = int(tx + (sx - tx) * t + math.sin(elapsed * 0.25 + i) * 10 * z)
                my = int(ty + (sy - ty) * t + math.cos(elapsed * 0.2 + i) * 6 * z)
                pygame.draw.circle(self.screen, (120, 190, 255, int(95 * fade_in)), (mx, my), max(2, int((5 - i) * z)))
            pygame.draw.line(self.screen, (90, 150, 255, int(80 * fade_in)), (tx, ty), (sx, sy), max(1, int(2 * z)))

        if self.shake_power > 0:
            for _ in range(10):
                x = sx + random.randint(-size // 2, size // 2)
                y = sy + random.randint(-size // 2, size // 2)
                pygame.draw.circle(self.screen, random.choice([(255, 255, 255), (120, 190, 255), (50, 90, 180)]), (x, y), random.randint(1, 2))
