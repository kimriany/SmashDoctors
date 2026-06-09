import pygame
import random


class FinisherSystem:
    """
    영역전개 중 R키가 전환되는 필살기 시스템.

    흐름:
    1. finisher_request 수신
    2. 사용자에게 카메라 확대
    3. 화면 흔들림 + 흰색 플래시
    4. 상대 스톡 제거
    5. 모든 영역 해제는 BattleSession의 stock_lost 처리에서 수행
    """

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

        self.event_bus.subscribe("finisher_request", self.on_finisher_request)

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

        self.active = True
        self.gameplay_frozen = True
        self.owner = owner
        self.target = target
        self.timer = self.CUTSCENE_FRAMES
        self.total = self.CUTSCENE_FRAMES
        self.kill_done = False
        self.flash_alpha = 0
        self.shake_power = 0

        # 사용 즉시 필살기 스택 소모
        owner.finisher_charge_stack = 0.0
        owner.finisher_ready = False
        owner.finisher_locked = True
        owner.finisher_unlock_timer = 0

        owner.vel = pygame.Vector2(0, 0)
        target.vel = pygame.Vector2(0, 0)

        if hasattr(self.camera, "start_focus_cutscene"):
            self.camera.start_focus_cutscene(
                owner.rect,
                zoom=self.FOCUS_ZOOM,
                frames=self.FOCUS_FRAMES,
            )

    def update(self):
        if not self.active:
            self.gameplay_frozen = False
            return

        self.gameplay_frozen = True

        if hasattr(self.camera, "update_scripted"):
            self.camera.update_scripted()

        elapsed = self.total - self.timer

        # 흔들림/플래시 연출
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

        if not self.kill_done and elapsed >= self.KILL_FRAME:
            self._kill_target()
            self.kill_done = True

        self.timer -= 1
        if self.timer <= 0:
            self._finish()

    def _kill_target(self):
        if self.target is None or self.owner is None:
            return
        if getattr(self.target, "dead", False):
            return

        tx, ty = self.target.rect.centerx, self.target.rect.centery

        if self.particle_sys:
            color = getattr(self.owner, "glow_color", (255, 255, 255))
            try:
                self.particle_sys.spawn(tx, ty, color, count=48, speed=9, life=42, r=5)
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
            # 아직 lose_stock 시그니처를 못 바꿨을 때도 작동하게 둔다.
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

    def draw_overlay(self):
        if not self.active:
            return

        # 화면 흔들림 느낌의 검은 비네팅
        if self.shake_power > 0:
            for _ in range(4):
                x = random.randint(-self.shake_power, self.shake_power)
                y = random.randint(-self.shake_power, self.shake_power)
                pygame.draw.rect(
                    self.screen,
                    (255, 255, 255),
                    (random.randint(0, self.screen.get_width()),
                     random.randint(0, self.screen.get_height()),
                     2, 2),
                )

        if self.flash_alpha > 0:
            flash = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
            flash.fill((255, 255, 255, self.flash_alpha))
            self.screen.blit(flash, (0, 0))