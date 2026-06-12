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
    FINISHER_ASSET_PATHS = {
        "einstein_blackhole": "assets/images/effects/finishers/blackhole_lens.png",
        "hoking_horizon": "assets/images/effects/finishers/blackhole_lens.png",
        "pythagoras_geometry": "assets/images/effects/finishers/pythagoras_sigil.png",
        "nobel_barrage": "assets/images/effects/finishers/nobel_explosion_ring.png",
        "schrodinger_collapse": "assets/images/effects/finishers/schrodinger_quantum_orb.png",
        "turing_erasure": "assets/images/effects/finishers/turing_digital_ring.png",
        "curie_meltdown": "assets/images/effects/finishers/curie_radium_burst.png",
        "impact": "assets/images/effects/finishers/ultimate_starburst.png",
    }
    STYLE_SETTINGS = {
        "einstein_blackhole": {
            "frames": 142, "kill": 104, "focus": 34, "zoom": 1.46,
            "primary": (120, 190, 255), "secondary": (235, 250, 255), "veil": (0, 0, 18),
        },
        "pythagoras_geometry": {
            "frames": 128, "kill": 92, "focus": 34, "zoom": 1.54,
            "primary": (95, 185, 255), "secondary": (255, 235, 120), "veil": (4, 16, 42),
        },
        "nobel_barrage": {
            "frames": 134, "kill": 94, "focus": 34, "zoom": 1.50,
            "primary": (255, 120, 35), "secondary": (255, 230, 110), "veil": (34, 16, 4),
        },
        "schrodinger_collapse": {
            "frames": 132, "kill": 96, "focus": 34, "zoom": 1.56,
            "primary": (155, 120, 255), "secondary": (95, 220, 255), "veil": (24, 10, 54),
        },
        "turing_erasure": {
            "frames": 128, "kill": 92, "focus": 34, "zoom": 1.52,
            "primary": (80, 235, 190), "secondary": (120, 200, 255), "veil": (2, 18, 28),
        },
        "hoking_horizon": {
            "frames": 142, "kill": 104, "focus": 38, "zoom": 1.58,
            "primary": (80, 170, 255), "secondary": (235, 250, 255), "veil": (1, 4, 18),
        },
        "curie_meltdown": {
            "frames": 132, "kill": 94, "focus": 34, "zoom": 1.52,
            "primary": (140, 255, 90), "secondary": (235, 255, 150), "veil": (10, 34, 10),
        },
        "default": {
            "frames": 92, "kill": 54, "focus": 28, "zoom": 1.65,
            "primary": (255, 255, 255), "secondary": (255, 240, 180), "veil": (0, 0, 0),
        },
    }

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
        self._owner_anchor = pygame.Vector2(0, 0)
        self._caster_side = 1
        self._blackhole_img = self._load_blackhole_img()
        self._finisher_assets = self._load_finisher_assets()
        self._hole_focus_started = False
        self._style_started = False
        self._primary_color = (255, 255, 255)
        self._secondary_color = (255, 240, 180)
        self._veil_color = (0, 0, 0)

        self.event_bus.subscribe("finisher_request", self.on_finisher_request)

    def _load_blackhole_img(self):
        if not os.path.exists(self.EINSTEIN_BLACKHOLE_PATH):
            return None
        try:
            return pygame.image.load(self.EINSTEIN_BLACKHOLE_PATH).convert_alpha()
        except Exception as e:
            print(f"[Finisher] blackhole image load failed: {e}")
            return None

    def _load_finisher_assets(self):
        assets = {}
        for key, path in self.FINISHER_ASSET_PATHS.items():
            if not os.path.exists(path):
                continue
            try:
                assets[key] = pygame.image.load(path).convert_alpha()
            except Exception as e:
                print(f"[Finisher] asset load failed ({path}): {e}")
        return assets

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

        self._style = self._style_for_owner(owner)
        self._apply_style_settings(self._style)

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
        self._style_started = False

        self._owner_start = pygame.Vector2(owner.rect.centerx, owner.rect.centery)
        self._target_start = pygame.Vector2(target.rect.centerx, target.rect.centery)
        self._hole_x, self._hole_y = self._choose_finisher_center(owner, target)
        self._owner_anchor = pygame.Vector2(*self._choose_owner_anchor(owner, target))
        self._teleport_owner_to_anchor(intro=True)

        # 사용 즉시 필살기 스택 소모
        owner.finisher_charge_stack = 0.0
        owner.finisher_ready = False
        owner.finisher_locked = True
        owner.finisher_unlock_timer = 0

        owner.vel = pygame.Vector2(0, 0)
        target.vel = pygame.Vector2(0, 0)
        owner.invincible = max(getattr(owner, "invincible", 0), self.CUTSCENE_FRAMES)

        if hasattr(self.camera, "start_focus_cutscene"):
            focus_rect = owner.rect if self._style == "default" else self._make_focus_rect(self._hole_x, self._hole_y, 300, 260)
            self.camera.start_focus_cutscene(
                focus_rect,
                zoom=self.FOCUS_ZOOM,
                frames=self.FOCUS_FRAMES,
            )

    def _char_name(self, owner) -> str:
        try:
            return str(owner.get_char_name())
        except Exception:
            pass
        return str(getattr(owner, "DISPLAY_NAME", "") or owner.__class__.__name__)

    def _style_for_owner(self, owner) -> str:
        name = self._char_name(owner).lower()
        if "einstein" in name:
            return "einstein_blackhole"
        if "pythagoras" in name or "pita" in name:
            return "pythagoras_geometry"
        if "nobel" in name:
            return "nobel_barrage"
        if "schrodinger" in name or "schrödinger" in name:
            return "schrodinger_collapse"
        if "turing" in name:
            return "turing_erasure"
        if "hoking" in name or "hawking" in name:
            return "hoking_horizon"
        if "curie" in name:
            return "curie_meltdown"
        return "default"

    def _apply_style_settings(self, style: str):
        cfg = self.STYLE_SETTINGS.get(style, self.STYLE_SETTINGS["default"])
        self.CUTSCENE_FRAMES = cfg["frames"]
        self.KILL_FRAME = cfg["kill"]
        self.FOCUS_FRAMES = cfg["focus"]
        self.FOCUS_ZOOM = cfg["zoom"]
        self._primary_color = cfg["primary"]
        self._secondary_color = cfg["secondary"]
        self._veil_color = cfg["veil"]

    def _choose_blackhole_center(self, owner, target):
        # 현재 카메라 중심을 월드 좌표로 되돌려 경기장 중앙처럼 쓰되, 두 플레이어 사이에서 너무 멀어지지 않게 보정한다.
        cam_cx = self.camera.offset.x + (self.screen.get_width() * 0.5) / max(0.1, self.camera.zoom)
        cam_cy = self.camera.offset.y + (self.screen.get_height() * 0.48) / max(0.1, self.camera.zoom)
        pair_cx = (owner.rect.centerx + target.rect.centerx) * 0.5
        floor_y = max(owner.rect.bottom, target.rect.bottom)
        return (cam_cx * 0.55 + pair_cx * 0.45, min(cam_cy + 20, floor_y - 100))

    def _choose_finisher_center(self, owner, target):
        if self._style == "einstein_blackhole":
            return self._choose_blackhole_center(owner, target)

        pair_cx = (owner.rect.centerx + target.rect.centerx) * 0.5
        floor_y = max(owner.rect.bottom, target.rect.bottom)
        if self._style in ("nobel_barrage", "curie_meltdown"):
            return (target.rect.centerx, target.rect.centery - 18)
        if self._style in ("hoking_horizon", "schrodinger_collapse", "turing_erasure"):
            return (pair_cx, min(target.rect.centery - 10, floor_y - 95))
        if self._style == "pythagoras_geometry":
            return (pair_cx, (owner.rect.centery + target.rect.centery) * 0.5 - 8)
        return (owner.rect.centerx, owner.rect.centery)

    def _choose_owner_anchor(self, owner, target):
        side = -1 if self._owner_start.x <= self._target_start.x else 1
        self._caster_side = side
        floor_y = max(owner.rect.bottom, target.rect.bottom)
        half_h = max(30, owner.rect.height // 2)

        if self._style == "nobel_barrage":
            dist, lift = 245, 108
        elif self._style == "pythagoras_geometry":
            dist, lift = 220, 76
        elif self._style == "hoking_horizon":
            dist, lift = 235, 120
        else:
            dist, lift = 210, 96

        anchor_x = self._hole_x + side * dist
        anchor_y = min(self._hole_y + lift, floor_y - half_h - 4)
        if self._style in ("hoking_horizon", "einstein_blackhole"):
            anchor_y = self._hole_y + lift * 0.62
        return anchor_x, anchor_y

    def _teleport_owner_to_anchor(self, intro=False):
        if self.owner is None:
            return

        self.owner.rect.center = (int(self._owner_anchor.x), int(self._owner_anchor.y))
        self.owner.vel = pygame.Vector2(0, 0)
        self.owner.facing = -1 if self._caster_side > 0 else 1
        if intro and self.particle_sys:
            try:
                self.particle_sys.spawn(
                    self._owner_start.x, self._owner_start.y,
                    self._secondary_color,
                    count=18, speed=7, life=28, r=5, glow=True,
                )
                self.particle_sys.spawn(
                    self._owner_anchor.x, self._owner_anchor.y,
                    self._primary_color,
                    count=34, speed=8, life=38, r=6, glow=True,
                )
            except Exception:
                pass

    def _hold_owner_pose(self, elapsed):
        if self.owner is None:
            return
        bob = math.sin(elapsed * 0.12) * 4.0
        self.owner.rect.center = (int(self._owner_anchor.x), int(self._owner_anchor.y + bob))
        self.owner.vel = pygame.Vector2(0, 0)
        self.owner.facing = -1 if self._caster_side > 0 else 1

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
        elif self._style != "default":
            self._update_character_finisher(elapsed)
        else:
            self._update_default_fx(elapsed)

        if not self.kill_done and elapsed >= self.KILL_FRAME:
            self._kill_target()
            self.kill_done = True

        self.timer -= 1
        if self.timer <= 0:
            self._finish()

    def _update_default_fx(self, elapsed):
        self._hold_owner_pose(elapsed)
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

        self._hold_owner_pose(elapsed)
        if not self._style_started:
            self._style_started = True
            if self.particle_sys:
                try:
                    self.particle_sys.spawn(
                        self._owner_anchor.x, self._owner_anchor.y,
                        self._secondary_color,
                        count=34, speed=7, life=36, r=6, glow=True,
                    )
                except Exception:
                    pass

        if elapsed == 18 and hasattr(self.camera, "start_focus_cutscene"):
            self.camera.start_focus_cutscene(
                self._make_focus_rect(self._hole_x, self._hole_y, 260, 230),
                zoom=1.58,
                frames=38,
            )
            self._hole_focus_started = True

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

    def _update_character_finisher(self, elapsed):
        if self.owner is None or self.target is None:
            return

        self._hold_owner_pose(elapsed)

        if not self._style_started:
            self._style_started = True
            if self.particle_sys:
                try:
                    self.particle_sys.spawn(
                        self._hole_x, self._hole_y,
                        self._primary_color,
                        count=24, speed=6, life=34, r=5, glow=True,
                    )
                except Exception:
                    pass

        if not self.kill_done:
            self.target.vel = pygame.Vector2(0, 0)
            self.target.invincible = max(getattr(self.target, "invincible", 0), 2)

        if elapsed == 18 and hasattr(self.camera, "start_focus_cutscene"):
            self.camera.start_focus_cutscene(
                self._make_focus_rect(self._hole_x, self._hole_y, 260, 230),
                zoom=max(self.FOCUS_ZOOM, 1.55),
                frames=34,
            )

        ratio = max(0.0, min(1.0, elapsed / max(1, self.KILL_FRAME)))

        if not self.kill_done:
            if self._style == "hoking_horizon":
                pull_start = 22
                if elapsed >= pull_start:
                    pull_ratio = max(0.0, min(1.0, (elapsed - pull_start) / max(1, self.KILL_FRAME - pull_start - 5)))
                    pull = pull_ratio * pull_ratio * (3.0 - 2.0 * pull_ratio)
                    tx = self._target_start.x + (self._hole_x - self._target_start.x) * pull
                    ty = self._target_start.y + (self._hole_y - self._target_start.y) * pull
                    self.target.rect.center = (int(tx), int(ty))
            elif self._style == "schrodinger_collapse":
                amp = max(0.0, 18.0 * (1.0 - ratio))
                ox = math.sin(elapsed * 0.83) * amp
                oy = math.cos(elapsed * 0.61) * amp * 0.55
                self.target.rect.center = (int(self._target_start.x + ox), int(self._target_start.y + oy))
            elif self._style == "turing_erasure":
                if elapsed % 9 < 4:
                    self.target.rect.center = (int(self._target_start.x + random.randint(-3, 3)),
                                               int(self._target_start.y + random.randint(-2, 2)))
                else:
                    self.target.rect.center = (int(self._target_start.x), int(self._target_start.y))
            elif self._style == "nobel_barrage":
                lift = math.sin(ratio * math.pi) * 32
                jitter = 4 if elapsed > 28 else 1
                self.target.rect.center = (
                    int(self._target_start.x + random.randint(-jitter, jitter)),
                    int(self._target_start.y - lift + random.randint(-jitter, jitter)),
                )
            elif self._style == "curie_meltdown":
                melt = min(18, elapsed * 0.18)
                self.target.rect.center = (
                    int(self._target_start.x + math.sin(elapsed * 0.42) * 5),
                    int(self._target_start.y + math.sin(elapsed * 0.22) * melt),
                )
            elif self._style == "pythagoras_geometry":
                cut_start = 26
                if elapsed >= cut_start:
                    cut_ratio = max(0.0, min(1.0, (elapsed - cut_start) / max(1, self.KILL_FRAME - cut_start)))
                    slide = math.sin(cut_ratio * math.pi) * 24
                    self.target.rect.center = (int(self._target_start.x + self.owner.facing * slide),
                                               int(self._target_start.y - slide * 0.35))

        if self.particle_sys and elapsed % 5 == 0:
            try:
                if self._style == "nobel_barrage":
                    px = self._hole_x + random.randint(-120, 120)
                    py = self._hole_y + random.randint(-85, 85)
                    self.particle_sys.spawn(px, py, random.choice([self._primary_color, self._secondary_color, (80, 55, 35)]),
                                            count=2, speed=4.5, life=18, r=4, glow=True)
                elif self._style == "curie_meltdown":
                    self.particle_sys.spawn(self._hole_x + random.randint(-95, 95),
                                            self._hole_y + random.randint(-70, 70),
                                            random.choice([self._primary_color, self._secondary_color, (80, 230, 190)]),
                                            count=2, speed=2.1, gravity=-0.05, life=22, r=3, glow=True)
                else:
                    self.particle_sys.spawn(self._hole_x, self._hole_y,
                                            random.choice([self._primary_color, self._secondary_color]),
                                            count=1, speed=3.0, life=20, r=3, glow=True)
            except Exception:
                pass

        if self.KILL_FRAME - 18 <= elapsed <= self.KILL_FRAME + 12:
            self.shake_power = max(0, 14 - abs(self.KILL_FRAME - elapsed) // 2)
        else:
            self.shake_power = max(0, self.shake_power - 1)

        if self.KILL_FRAME - 8 <= elapsed <= self.KILL_FRAME + 16:
            if elapsed <= self.KILL_FRAME:
                self.flash_alpha = min(225, self.flash_alpha + 18)
            else:
                self.flash_alpha = max(0, self.flash_alpha - 13)
        else:
            self.flash_alpha = max(0, self.flash_alpha - 14)

    def _kill_target(self):
        if self.target is None or self.owner is None:
            return
        if getattr(self.target, "dead", False):
            return

        tx, ty = self.target.rect.centerx, self.target.rect.centery

        if self.particle_sys:
            color = self._primary_color if self._style != "default" else getattr(self.owner, "glow_color", (255, 255, 255))
            try:
                count = 64 if self._style == "einstein_blackhole" else 56 if self._style != "default" else 48
                self.particle_sys.spawn(tx, ty, color, count=count, speed=9, life=42, r=5, glow=self._style != "default")
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
        self._style_started = False

    def draw_overlay(self):
        if not self.active:
            return
        elapsed = self.total - self.timer

        if self._style == "einstein_blackhole":
            self._draw_einstein_blackhole()
        elif self._style != "default":
            self._draw_character_finisher()
        else:
            self._draw_default_overlay()

        if self.flash_alpha > 0:
            flash = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
            flash.fill((255, 255, 255, self.flash_alpha))
            self.screen.blit(flash, (0, 0))

        self._draw_cinematic_frame(elapsed)

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

    def _draw_cinematic_frame(self, elapsed):
        w, h = self.screen.get_size()
        fade = max(0.0, min(1.0, elapsed / 18.0))
        bar_h = int(48 * fade)
        if bar_h > 0:
            pygame.draw.rect(self.screen, (0, 0, 0), (0, 0, w, bar_h))
            pygame.draw.rect(self.screen, (0, 0, 0), (0, h - bar_h, w, bar_h))
            line_alpha = int(120 * fade)
            line = pygame.Surface((w, 2), pygame.SRCALPHA)
            line.fill((*self._secondary_color, line_alpha))
            self.screen.blit(line, (0, bar_h))
            self.screen.blit(line, (0, h - bar_h - 2))

        vignette = pygame.Surface((w, h), pygame.SRCALPHA)
        edge = int(58 * fade)
        pygame.draw.rect(vignette, (0, 0, 0, edge), (0, 0, w, h), max(8, int(26 * fade)))
        self.screen.blit(vignette, (0, 0))

    def _draw_caster_presence(self, elapsed, z, fade, kill_pulse):
        if self.owner is None:
            return

        ox, oy = self.camera.world_to_screen(self.owner.rect.centerx, self.owner.rect.centery)
        sx, sy = self.camera.world_to_screen(self._hole_x, self._hole_y)
        charge = max(0.0, min(1.0, elapsed / max(1, self.KILL_FRAME - 18)))
        aura = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)

        if elapsed < 24:
            start_x, start_y = self.camera.world_to_screen(self._owner_start.x, self._owner_start.y)
            ghost_alpha = int((1.0 - elapsed / 24.0) * 160)
            pygame.draw.line(aura, (*self._secondary_color, ghost_alpha), (start_x, start_y), (ox, oy), max(3, int(7 * z)))
            pygame.draw.circle(aura, (*self._secondary_color, ghost_alpha), (start_x, start_y), max(10, int(26 * z)), max(2, int(4 * z)))

        for i in range(5):
            r = int((24 + i * 18 + charge * 22 + math.sin(elapsed * 0.18 + i) * 5) * z * kill_pulse)
            col = self._secondary_color if i % 2 == 0 else self._primary_color
            pygame.draw.circle(aura, (*col, int((118 - i * 14) * fade)), (ox, oy), max(4, r), max(1, int((3 if i < 2 else 2) * z)))

        for i in range(9):
            angle = elapsed * 0.055 + i * math.tau / 9
            inner = (30 + charge * 16) * z
            outer = (68 + charge * 70) * z
            p1 = (ox + int(math.cos(angle) * inner), oy + int(math.sin(angle) * inner))
            p2 = (ox + int(math.cos(angle) * outer), oy + int(math.sin(angle) * outer))
            pygame.draw.line(aura, (*self._primary_color, int(90 * fade)), p1, p2, max(1, int(2 * z)))

        pygame.draw.line(aura, (*self._secondary_color, int(115 * fade * charge)), (ox, oy), (sx, sy), max(2, int(4 * z)))
        pygame.draw.circle(aura, (255, 255, 255, int(110 * fade * charge)), (ox, oy), max(4, int(9 * z)))
        self.screen.blit(aura, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

    def _draw_asset_centered(self, asset_key, sx, sy, size, angle=0.0, alpha=255, blend=True):
        img = self._finisher_assets.get(asset_key)
        if img is None:
            return False

        size = max(8, int(size))
        iw, ih = img.get_size()
        aspect = iw / max(1, ih)
        if aspect >= 1.0:
            w = size
            h = max(8, int(size / aspect))
        else:
            h = size
            w = max(8, int(size * aspect))

        scaled = pygame.transform.smoothscale(img, (w, h))
        if angle:
            scaled = pygame.transform.rotozoom(scaled, angle, 1.0)
        scaled.set_alpha(max(0, min(255, int(alpha))))
        flags = pygame.BLEND_RGBA_ADD if blend else 0
        self.screen.blit(scaled, (sx - scaled.get_width() // 2, sy - scaled.get_height() // 2), special_flags=flags)
        return True

    def _draw_execution_burst(self, sx, sy, elapsed, z, fade, kill_pulse):
        closeness = max(0.0, 1.0 - abs(self.KILL_FRAME - elapsed) / 18.0)
        if closeness <= 0:
            return
        self._draw_asset_centered(
            "impact",
            sx,
            sy,
            (160 + 120 * closeness) * z * kill_pulse,
            angle=elapsed * 2.5,
            alpha=125 * fade * closeness,
        )
        burst = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        ray_len = int(420 * z * kill_pulse)
        for i in range(22):
            ang = i * math.tau / 22 + elapsed * 0.03
            start = int(26 * z)
            p1 = (sx + int(math.cos(ang) * start), sy + int(math.sin(ang) * start))
            p2 = (sx + int(math.cos(ang) * ray_len), sy + int(math.sin(ang) * ray_len))
            col = self._secondary_color if i % 2 else self._primary_color
            pygame.draw.line(burst, (*col, int(160 * fade * closeness)), p1, p2, max(1, int(3 * z)))

        r = int((42 + 82 * closeness) * z * kill_pulse)
        pygame.draw.circle(burst, (255, 255, 255, int(115 * fade * closeness)), (sx, sy), max(8, r), max(2, int(5 * z)))
        self.screen.blit(burst, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

    def _draw_character_finisher(self):
        elapsed = self.total - self.timer
        sx, sy = self.camera.world_to_screen(self._hole_x, self._hole_y)
        z = max(0.5, self.camera.zoom)
        fade = max(0.0, min(1.0, elapsed / 24.0))
        kill_pulse = 1.0 + 0.35 * max(0.0, 1.0 - abs(self.KILL_FRAME - elapsed) / 16.0)

        veil = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        veil.fill((*self._veil_color, int((58 + 42 * kill_pulse) * fade)))
        self.screen.blit(veil, (0, 0))

        asset_size = {
            "pythagoras_geometry": 440,
            "nobel_barrage": 470,
            "schrodinger_collapse": 410,
            "turing_erasure": 420,
            "hoking_horizon": 430,
            "curie_meltdown": 450,
        }.get(self._style, 400)
        asset_alpha = int(155 * fade)
        asset_angle = -elapsed * 0.7 if self._style in ("hoking_horizon", "turing_erasure") else elapsed * 0.35
        self._draw_asset_centered(
            self._style,
            sx,
            sy,
            asset_size * z * kill_pulse,
            angle=asset_angle,
            alpha=asset_alpha,
        )

        if self._style == "pythagoras_geometry":
            self._draw_pythagoras_geometry(elapsed, sx, sy, z, fade, kill_pulse)
        elif self._style == "nobel_barrage":
            self._draw_nobel_barrage(elapsed, sx, sy, z, fade, kill_pulse)
        elif self._style == "schrodinger_collapse":
            self._draw_schrodinger_collapse(elapsed, sx, sy, z, fade, kill_pulse)
        elif self._style == "turing_erasure":
            self._draw_turing_erasure(elapsed, sx, sy, z, fade, kill_pulse)
        elif self._style == "hoking_horizon":
            self._draw_hoking_horizon(elapsed, sx, sy, z, fade, kill_pulse)
        elif self._style == "curie_meltdown":
            self._draw_curie_meltdown(elapsed, sx, sy, z, fade, kill_pulse)

        self._draw_caster_presence(elapsed, z, fade, kill_pulse)
        self._draw_execution_burst(sx, sy, elapsed, z, fade, kill_pulse)

        if self.shake_power > 0:
            for _ in range(10):
                x = sx + random.randint(-int(160 * z), int(160 * z))
                y = sy + random.randint(-int(120 * z), int(120 * z))
                pygame.draw.circle(self.screen, random.choice([self._primary_color, self._secondary_color, (255, 255, 255)]), (x, y), random.randint(1, 2))

    def _draw_pythagoras_geometry(self, elapsed, sx, sy, z, fade, kill_pulse):
        surf = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        span = int(210 * z * kill_pulse)
        sweep = max(0.0, min(1.0, (elapsed - 18) / max(1, self.KILL_FRAME - 18)))
        facing = getattr(self.owner, "facing", 1) if self.owner is not None else 1

        a = (sx - facing * span, sy + int(span * 0.52))
        b = (sx + facing * span, sy + int(span * 0.52))
        c = (sx + facing * span, sy - int(span * 0.82))
        pygame.draw.polygon(surf, (*self._primary_color, int(34 * fade)), (a, b, c))
        pygame.draw.lines(surf, (*self._secondary_color, int(190 * fade)), True, (a, b, c), max(2, int(3 * z)))

        cut_x = int(a[0] + (b[0] - a[0]) * sweep)
        cut_y = int(a[1] + (c[1] - a[1]) * sweep)
        pygame.draw.line(surf, (255, 255, 255, int(235 * fade)), a, (cut_x, cut_y), max(3, int(5 * z)))
        pygame.draw.line(surf, (*self._primary_color, int(130 * fade)), (sx - facing * span, sy), (sx + facing * span, sy), max(1, int(2 * z)))

        for i in range(5):
            t = (sweep + i * 0.14) % 1.0
            x = int(a[0] + (b[0] - a[0]) * t)
            y = int(a[1] + (c[1] - a[1]) * t)
            rr = max(3, int((10 + i * 3) * z))
            pts = [(x, y - rr), (x + facing * rr, y + rr), (x - facing * rr, y + rr)]
            pygame.draw.polygon(surf, (*self._secondary_color, int((120 - i * 15) * fade)), pts, max(1, int(2 * z)))

        self.screen.blit(surf, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

    def _draw_nobel_barrage(self, elapsed, sx, sy, z, fade, kill_pulse):
        surf = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        base = int(70 * z * kill_pulse)
        for i in range(5):
            phase = elapsed * 0.17 + i * math.tau / 5
            ex = sx + int(math.cos(phase) * (92 + i * 16) * z)
            ey = sy + int(math.sin(phase * 1.3) * (58 + i * 9) * z)
            r = max(10, base + int(math.sin(phase) * 12 * z) - i * int(6 * z))
            pygame.draw.circle(surf, (*self._primary_color, int((70 - i * 8) * fade)), (ex, ey), r)
            pygame.draw.circle(surf, (*self._secondary_color, int((155 - i * 18) * fade)), (ex, ey), max(3, r // 2), max(2, int(4 * z)))

        warn_r = int((72 + elapsed * 1.6) * z) % max(1, int(170 * z))
        pygame.draw.circle(surf, (255, 255, 255, int(125 * fade)), (sx, sy), max(12, warn_r), max(1, int(2 * z)))

        if self.KILL_FRAME - 10 <= elapsed <= self.KILL_FRAME + 10:
            pygame.draw.circle(surf, (255, 245, 180, int(210 * fade)), (sx, sy), int(145 * z * kill_pulse))

        self.screen.blit(surf, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

    def _draw_schrodinger_collapse(self, elapsed, sx, sy, z, fade, kill_pulse):
        surf = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        for i in range(7):
            r = int((42 + i * 18 + math.sin(elapsed * 0.14 + i) * 7) * z * kill_pulse)
            rect = pygame.Rect(sx - r * 2, sy - r, r * 4, r * 2)
            col = self._primary_color if i % 2 == 0 else self._secondary_color
            pygame.draw.ellipse(surf, (*col, int((125 - i * 12) * fade)), rect, max(1, int(2 * z)))

        if self.target is not None and not self.kill_done:
            tx, ty = self.camera.world_to_screen(self.target.rect.centerx, self.target.rect.centery)
            for i in range(6):
                ang = elapsed * 0.24 + i * math.tau / 6
                gx = tx + int(math.cos(ang) * 34 * z)
                gy = ty + int(math.sin(ang * 1.4) * 24 * z)
                pygame.draw.circle(surf, (*random.choice([self._primary_color, self._secondary_color]), int(70 * fade)), (gx, gy), max(8, int(18 * z)))

        collapse = max(0.0, min(1.0, (elapsed - 30) / max(1, self.KILL_FRAME - 30)))
        pygame.draw.circle(surf, (255, 255, 255, int(95 * fade * collapse)), (sx, sy), max(8, int((140 - 88 * collapse) * z)))
        self.screen.blit(surf, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

    def _draw_turing_erasure(self, elapsed, sx, sy, z, fade, kill_pulse):
        surf = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        step = max(16, int(28 * z))
        shift = int((elapsed * 4 * z) % step)
        for x in range(-step, self.screen.get_width() + step, step):
            alpha = int(38 * fade)
            pygame.draw.line(surf, (*self._secondary_color, alpha), (x + shift, 0), (x + shift, self.screen.get_height()), 1)
        for y in range(-step, self.screen.get_height() + step, step):
            alpha = int(34 * fade)
            pygame.draw.line(surf, (*self._primary_color, alpha), (0, y + shift), (self.screen.get_width(), y + shift), 1)

        scan_y = int((sy - 115 * z) + ((elapsed * 5) % max(1, int(230 * z))))
        pygame.draw.rect(surf, (*self._primary_color, int(100 * fade)), (0, scan_y, self.screen.get_width(), max(2, int(4 * z))))

        if self.target is not None and not self.kill_done:
            tx, ty = self.camera.world_to_screen(self.target.rect.centerx, self.target.rect.centery)
            bit_font = pygame.font.Font(None, max(12, int(18 * z)))
            for i in range(14):
                bit = "1" if (elapsed + i) % 2 == 0 else "0"
                text = bit_font.render(bit, True, self._secondary_color)
                text.set_alpha(int((80 + i * 7) * fade))
                bx = tx + random.randint(-85, 85)
                by = ty + random.randint(-75, 75)
                surf.blit(text, (bx, by))

            pygame.draw.rect(surf, (*self._primary_color, int(160 * fade)),
                             pygame.Rect(tx - int(70 * z), ty - int(55 * z), int(140 * z), int(110 * z)),
                             max(1, int(2 * z)))

        self.screen.blit(surf, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

    def _draw_hoking_horizon(self, elapsed, sx, sy, z, fade, kill_pulse):
        surf = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        base = int(125 * z * kill_pulse)
        pygame.draw.circle(surf, (0, 0, 0, int(170 * fade)), (sx, sy), max(15, int(base * 0.55)))
        for i in range(7):
            r = int((base * (0.55 + i * 0.16) + math.sin(elapsed * 0.11 + i) * 8 * z) * kill_pulse)
            col = self._secondary_color if i % 2 == 0 else self._primary_color
            pygame.draw.circle(surf, (*col, int((150 - i * 14) * fade)), (sx, sy), r, max(1, int((3 if i < 2 else 2) * z)))

        if self.target is not None and not self.kill_done:
            tx, ty = self.camera.world_to_screen(self.target.rect.centerx, self.target.rect.centery)
            pygame.draw.line(surf, (*self._primary_color, int(105 * fade)), (tx, ty), (sx, sy), max(1, int(3 * z)))
            for i in range(6):
                t = i / 6.0
                px = int(tx + (sx - tx) * t + math.sin(elapsed * 0.25 + i) * 8 * z)
                py = int(ty + (sy - ty) * t + math.cos(elapsed * 0.21 + i) * 6 * z)
                pygame.draw.circle(surf, (*self._secondary_color, int(105 * fade)), (px, py), max(2, int((7 - i) * z)))

        self.screen.blit(surf, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

    def _draw_curie_meltdown(self, elapsed, sx, sy, z, fade, kill_pulse):
        surf = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        w = int(230 * z * kill_pulse)
        h = int(160 * z * kill_pulse)
        rect = pygame.Rect(sx - w // 2, sy - h // 2, w, h)
        pygame.draw.ellipse(surf, (*self._primary_color, int(55 * fade)), rect)
        for i in range(5):
            rr = int((42 + i * 24 + math.sin(elapsed * 0.15 + i) * 5) * z * kill_pulse)
            pygame.draw.ellipse(surf, (*random.choice([self._primary_color, self._secondary_color, (80, 230, 190)]), int((135 - i * 16) * fade)),
                                pygame.Rect(sx - rr * 2, sy - rr, rr * 4, rr * 2), max(1, int(2 * z)))

        for i in range(3):
            ang = elapsed * 0.04 + i * math.tau / 3
            p1 = (sx, sy)
            p2 = (sx + int(math.cos(ang - 0.28) * 68 * z), sy + int(math.sin(ang - 0.28) * 68 * z))
            p3 = (sx + int(math.cos(ang + 0.28) * 68 * z), sy + int(math.sin(ang + 0.28) * 68 * z))
            pygame.draw.polygon(surf, (*self._secondary_color, int(78 * fade)), (p1, p2, p3))
        pygame.draw.circle(surf, (*self._secondary_color, int(150 * fade)), (sx, sy), max(5, int(14 * z)))

        self.screen.blit(surf, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

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

        if self._finisher_assets.get("einstein_blackhole") is not None:
            self._draw_asset_centered(
                "einstein_blackhole",
                sx,
                sy,
                size * 1.2,
                angle=-elapsed * 2.2,
                alpha=alpha,
            )
        elif self._blackhole_img is not None:
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

        self._draw_caster_presence(elapsed, z, fade_in, kill_pulse)
        self._draw_execution_burst(sx, sy, elapsed, z, fade_in, kill_pulse)

        if self.shake_power > 0:
            for _ in range(10):
                x = sx + random.randint(-size // 2, size // 2)
                y = sy + random.randint(-size // 2, size // 2)
                pygame.draw.circle(self.screen, random.choice([(255, 255, 255), (120, 190, 255), (50, 90, 180)]), (x, y), random.randint(1, 2))
