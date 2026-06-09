# systems/domain_system.py

import os
import random
from dataclasses import dataclass

import pygame


@dataclass
class DomainInstance:
    owner: object
    bg_path: str | None
    bg_surface: pygame.Surface

    particle_color: tuple[int, int, int]

    break_hits_limit: int
    hits_taken: int = 0

    cutscene_frames: int = 34
    cutscene_zoom: float = 1.45
    transition_speed: float = 0.045
    freeze_during_transition: bool = True


class DomainSystem:
    """
    영역 전개 시스템.

    흐름:
    1. domain_request 수신
    2. 카메라 컷신 먼저 실행
    3. 컷신이 끝난 뒤 배경 전환 시작
    4. 배경 전환 경계에서 파티클 생성
    5. 파티클은 전환 방향의 반대쪽으로 휘날림
    """

    def __init__(
        self,
        screen: pygame.Surface,
        renderer,
        camera,
        event_bus,
        particle_sys=None,
        dual_domain_bg_path: str | None = "assets/images/domains/domain_clash.png",
        dual_particle_color: tuple[int, int, int] = (20, 20, 20),
    ):
        self.screen = screen
        self.renderer = renderer
        self.camera = camera
        self.event_bus = event_bus
        self.particle_sys = particle_sys

        self.W = screen.get_width()
        self.H = screen.get_height()

        self.dual_domain_bg_path = dual_domain_bg_path
        self.dual_domain_bg = self._load_bg(dual_domain_bg_path)
        self.dual_particle_color = dual_particle_color

        self.active_domains: dict[int, DomainInstance] = {}
        self.pending_requests: list[dict] = []

        # 컷신 / 정지
        self.gameplay_frozen = False
        self.freeze_timer = 0

        # 컷신이 끝난 뒤 시작할 배경 전환 예약
        self.transition_waiting = False
        self.waiting_from_bg = None
        self.waiting_to_bg = None
        self.waiting_side = "left"
        self.waiting_speed = 0.045
        self.waiting_particle_color = (0, 0, 0)
        self.waiting_freeze_during_transition = True

        # 실제 배경 전환
        self.transition_active = False
        self.transition_progress = 1.0
        self.transition_speed = 0.045
        self.transition_side = "left"
        self.transition_particle_color = (0, 0, 0)
        self.freeze_during_transition = True

        self.from_bg: pygame.Surface | None = None
        self.to_bg: pygame.Surface | None = None
        self.current_bg: pygame.Surface | None = None

        # 경계 파티클
        self.edge_particles: list[dict] = []

        self.finisher_unlock_delay = 90

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 상태
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    @property
    def active_count(self) -> int:
        return len(self.active_domains)

    def get_default_bg(self) -> pygame.Surface:
        """
        renderer의 기본 스테이지 배경을 surface로 가져온다.
        네 Renderer는 _bg_image를 사용한다.
        """

        # 1. 이미지 배경이 로드된 경우
        bg_img = getattr(self.renderer, "_bg_image", None)
        if isinstance(bg_img, pygame.Surface):
            return pygame.transform.smoothscale(bg_img, (self.W, self.H))

        # 2. 절차적 배경 fallback
        proc = getattr(self.renderer, "_proc_bg", None)
        city = getattr(self.renderer, "_city_surf", None)

        if isinstance(proc, pygame.Surface):
            surf = pygame.Surface((self.W, self.H))
            surf.blit(proc, (0, 0))

            if isinstance(city, pygame.Surface):
                surf.blit(city, (0, 0))

            return surf

        # 3. 최후 fallback
        surf = pygame.Surface((self.W, self.H))
        surf.fill((8, 10, 24))
        return surf

    def _load_bg(self, path: str | None) -> pygame.Surface:
        if path and os.path.exists(path):
            try:
                img = pygame.image.load(path).convert()
                return pygame.transform.smoothscale(img, (self.W, self.H))
            except Exception as e:
                print(f"[DomainSystem] 배경 로드 실패: {path} / {e}")

        surf = pygame.Surface((self.W, self.H))
        surf.fill((8, 8, 18))
        return surf

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 이벤트
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def on_domain_request(self, data: dict):
        """
        같은 프레임에 두 플레이어가 궁극기를 누를 수 있으므로 바로 처리하지 않고 모아둔다.
        """
        self.pending_requests.append(data)

    def on_attack_hit(self, data: dict):
        """
        영역 전개자가 맞으면 영역 해제 카운트 증가.
        """
        if self.gameplay_frozen:
            return

        target = data.get("target")
        if target is None:
            return

        pid = getattr(target, "player_id", None)
        if pid not in self.active_domains:
            return

        inst = self.active_domains[pid]

        if inst.owner is not target:
            return

        inst.hits_taken += 1
        target.domain_break_hits_taken = inst.hits_taken

        if inst.hits_taken >= inst.break_hits_limit:
            self.break_domain(target)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 업데이트
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def update(self):
        if self.pending_requests:
            self._resolve_pending_requests()

        # 카메라 컷신 중
        if self.freeze_timer > 0:
            self.freeze_timer -= 1
            self.gameplay_frozen = True

            if hasattr(self.camera, "update_scripted"):
                self.camera.update_scripted()

            # 컷신이 끝나면 배경 전환 시작
            if self.freeze_timer <= 0 and self.transition_waiting:
                self._start_waiting_transition()

            self._update_edge_particles()
            return

        # 배경 전환 중
        if self.transition_active:
            self.transition_progress += self.transition_speed

            if self.transition_progress >= 1.0:
                self.transition_progress = 1.0
                self.transition_active = False

                # 영역이 하나도 없으면 원래 renderer.draw_background()로 돌아가게 함
                if self.active_count == 0:
                    self.current_bg = None
                else:
                    self.current_bg = self.to_bg

            edge_x = self._get_transition_edge_x()
            self._spawn_edge_particles(edge_x)

            self.gameplay_frozen = self.freeze_during_transition
        else:
            self.gameplay_frozen = False

        self._update_edge_particles()

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 영역 발동 처리
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def _resolve_pending_requests(self):
        requests = self.pending_requests[:]
        self.pending_requests.clear()

        valid_requests = []

        for req in requests:
            owner = req.get("owner")
            if owner is None:
                continue

            pid = getattr(owner, "player_id", None)
            if pid is None:
                continue

            if pid in self.active_domains:
                continue

            bg_path = req.get("bg_path")
            bg = self._load_bg(bg_path)

            particle_color = req.get("particle_color", (0, 0, 0))
            break_hits = int(req.get("break_hits", 5))

            cutscene_frames = int(req.get("cutscene_frames", 34))
            cutscene_zoom = float(req.get("cutscene_zoom", 1.45))
            transition_speed = float(req.get("transition_speed", 0.045))
            freeze_during_transition = bool(req.get("freeze_during_transition", True))

            inst = DomainInstance(
                owner=owner,
                bg_path=bg_path,
                bg_surface=bg,
                particle_color=particle_color,
                break_hits_limit=break_hits,
                cutscene_frames=cutscene_frames,
                cutscene_zoom=cutscene_zoom,
                transition_speed=transition_speed,
                freeze_during_transition=freeze_during_transition,
            )

            self.active_domains[pid] = inst

            owner.domain_active = True
            owner.domain_locked = True
            owner.domain_break_hits_taken = 0
            owner.domain_break_hits_limit = break_hits

            if hasattr(owner, "apply_domain_stats"):
                owner.apply_domain_stats()

            owner.finisher_charge_stack = 0.0
            owner.finisher_ready = False
            owner.finisher_locked = False
            owner.finisher_unlock_timer = 0

            if hasattr(owner, "on_domain_opened"):
                owner.on_domain_opened()

            valid_requests.append(req)

        if not valid_requests:
            return

        first_owner = valid_requests[0]["owner"]

        # 여러 개가 동시에 들어오면 카메라 컷신은 첫 요청자 기준
        cutscene_frames = int(valid_requests[0].get("cutscene_frames", 34))
        cutscene_zoom = float(valid_requests[0].get("cutscene_zoom", 1.45))

        self._start_cutscene(
            owner=first_owner,
            frames=cutscene_frames,
            zoom=cutscene_zoom,
        )

        # 컷신이 끝난 뒤 시작할 배경 전환 예약
        next_bg, side, particle_color, transition_speed, freeze_during_transition = (
            self._decide_next_transition_settings(
                prefer_owner=first_owner,
                source_requests=valid_requests,
            )
        )

        self._queue_transition_after_cutscene(
            from_bg=self.current_bg or self.get_default_bg(),
            to_bg=next_bg,
            side=side,
            speed=transition_speed,
            particle_color=particle_color,
            freeze_during_transition=freeze_during_transition,
        )

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 영역 해제
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def break_domain(self, owner):
        pid = getattr(owner, "player_id", None)

        if pid not in self.active_domains:
            return

        removed_inst = self.active_domains.pop(pid)

        owner.domain_active = False
        owner.domain_locked = False
        owner.domain_break_hits_taken = 0
        owner.domain_break_hits_limit = 0

        # 해제될 때도 카메라 워킹
        self._start_cutscene(
            owner=owner,
            frames=removed_inst.cutscene_frames,
            zoom=removed_inst.cutscene_zoom,
        )

        # 카메라 워킹이 끝난 뒤 배경 전환
        if self.active_count == 0:
            next_bg = self.get_default_bg()
            side = self._side_from_player(owner)
            particle_color = removed_inst.particle_color
            transition_speed = removed_inst.transition_speed
            freeze_during_transition = removed_inst.freeze_during_transition

        else:
            next_bg, side, particle_color, transition_speed, freeze_during_transition = (
                self._decide_next_transition_settings()
            )

        self._queue_transition_after_cutscene(
            from_bg=self.current_bg or self.get_default_bg(),
            to_bg=next_bg,
            side=side,
            speed=transition_speed,
            particle_color=particle_color,
            freeze_during_transition=freeze_during_transition,
        )
        if hasattr(owner, "clear_domain_stats"):
            owner.clear_domain_stats()

        owner.domain_active = False
        owner.domain_locked = False
        owner.domain_break_hits_taken = 0
        owner.finisher_locked = False

        if hasattr(owner, "on_domain_closed"):
            owner.on_domain_closed()

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 다음 배경 / 방향 / 색상 / 속도 결정
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def _decide_next_transition_settings(self, prefer_owner=None, source_requests=None):
        """
        반환:
        next_bg, side, particle_color, transition_speed, freeze_during_transition
        """

        # 영역 2개 이상이면 특수 배경
        if self.active_count >= 2:
            side = self._side_from_player(prefer_owner) if prefer_owner else "left"

            # 동시에 발동한 경우 두 스킬 색상을 섞어서 사용
            if source_requests and len(source_requests) >= 2:
                colors = [
                    req.get("particle_color", self.dual_particle_color)
                    for req in source_requests
                ]
                particle_color = self._mix_colors(colors)
                transition_speed = max(
                    float(req.get("transition_speed", 0.045))
                    for req in source_requests
                )
                freeze_during_transition = any(
                    bool(req.get("freeze_during_transition", True))
                    for req in source_requests
                )
            else:
                particle_color = self.dual_particle_color
                transition_speed = 0.045
                freeze_during_transition = True

            return (
                self.dual_domain_bg,
                side,
                particle_color,
                transition_speed,
                freeze_during_transition,
            )

        # 영역 1개면 남은 영역 배경
        if self.active_count == 1:
            inst = next(iter(self.active_domains.values()))

            return (
                inst.bg_surface,
                self._side_from_player(inst.owner),
                inst.particle_color,
                inst.transition_speed,
                inst.freeze_during_transition,
            )

        # 영역 0개면 기본 배경
        return (
            self.get_default_bg(),
            "left",
            (0, 0, 0),
            0.045,
            True,
        )

    def _mix_colors(self, colors):
        if not colors:
            return self.dual_particle_color

        r = sum(c[0] for c in colors) // len(colors)
        g = sum(c[1] for c in colors) // len(colors)
        b = sum(c[2] for c in colors) // len(colors)

        return (r, g, b)

    def _side_from_player(self, owner) -> str:
        """
        Player1이면 왼쪽에서 오른쪽으로 전환.
        Player2이면 오른쪽에서 왼쪽으로 전환.
        """
        if owner is None:
            return "left"

        return "left" if getattr(owner, "player_id", 1) == 1 else "right"

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 컷신 / 전환 예약
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def _start_cutscene(self, owner, frames=34, zoom=1.45):
        self.freeze_timer = max(1, int(frames))
        self.gameplay_frozen = True

        if hasattr(self.camera, "start_focus_cutscene"):
            self.camera.start_focus_cutscene(
                owner.rect,
                zoom=zoom,
                frames=frames,
            )

    def _queue_transition_after_cutscene(
        self,
        from_bg,
        to_bg,
        side="left",
        speed=0.045,
        particle_color=(0, 0, 0),
        freeze_during_transition=True,
    ):
        """
        카메라 워킹이 끝난 뒤 실행할 배경 전환 예약.
        """
        self.transition_waiting = True
        self.waiting_from_bg = from_bg
        self.waiting_to_bg = to_bg
        self.waiting_side = side
        self.waiting_speed = speed
        self.waiting_particle_color = particle_color
        self.waiting_freeze_during_transition = freeze_during_transition

    def _start_waiting_transition(self):
        self.transition_waiting = False

        self.from_bg = self.waiting_from_bg
        self.to_bg = self.waiting_to_bg
        self.transition_side = self.waiting_side
        self.transition_speed = self.waiting_speed
        self.transition_particle_color = self.waiting_particle_color
        self.freeze_during_transition = self.waiting_freeze_during_transition

        self.transition_progress = 0.0
        self.transition_active = True

    def force_clear_all(self, winner=None, cutscene=True):
        """스톡이 날아갔을 때 모든 영역을 한 번에 해제."""
        if self.active_count == 0:
            return

        removed = list(self.active_domains.values())
        self.active_domains.clear()

        colors = []
        speed = 0.045
        freeze = True
        for inst in removed:
            p = inst.owner
            colors.append(inst.particle_color)
            speed = max(speed, inst.transition_speed)
            freeze = freeze or inst.freeze_during_transition

            p.domain_active = False
            p.domain_locked = False
            p.domain_break_hits_taken = 0
            p.domain_break_hits_limit = 0
            p.finisher_locked = False
            p.finisher_unlock_timer = 0
            if hasattr(p, "on_domain_closed"):
                p.on_domain_closed()

        particle_color = self._mix_colors(colors) if colors else (0, 0, 0)

        if winner is not None and cutscene:
            self._start_cutscene(winner, frames=30, zoom=1.35)

        self._queue_transition_after_cutscene(
            from_bg=self.current_bg or self.get_default_bg(),
            to_bg=self.get_default_bg(),
            side=self._side_from_player(winner) if winner is not None else "left",
            speed=speed,
            particle_color=particle_color,
            freeze_during_transition=freeze,
        )
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 배경 렌더링
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def draw_background(self):
        # 영역도 없고, 전환도 없으면 그냥 원래 Renderer에게 맡긴다.
        # 이게 가장 중요함.
        if self.active_count == 0 and not self.transition_active and not self.transition_waiting:
            self.renderer.draw_background()
            self._draw_edge_particles()
            return

        base = self.current_bg or self.get_default_bg()

        if not self.transition_active:
            self.screen.blit(base, (0, 0))
            self._draw_edge_particles()
            return

        old_bg = self.from_bg or base
        new_bg = self.to_bg or self.get_default_bg()

        self.screen.blit(old_bg, (0, 0))

        p = max(0.0, min(1.0, self.transition_progress))

        if self.transition_side == "left":
            w = int(self.W * p)

            if w > 0:
                src = pygame.Rect(0, 0, w, self.H)
                self.screen.blit(new_bg, (0, 0), src)

        else:
            w = int(self.W * p)

            if w > 0:
                src = pygame.Rect(self.W - w, 0, w, self.H)
                self.screen.blit(new_bg, (self.W - w, 0), src)

        self._draw_edge_particles()

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 전환 경계 계산
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def _get_transition_edge_x(self) -> int:
        p = max(0.0, min(1.0, self.transition_progress))

        if self.transition_side == "left":
            return int(self.W * p)

        return int(self.W * (1.0 - p))

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 경계 파티클
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def _spawn_edge_particles(self, edge_x: int):
        if edge_x < -20 or edge_x > self.W + 20:
            return

        for _ in range(9):
            y = random.randint(0, self.H)

            # 배경이 바뀌는 방향의 반대쪽으로 날림.
            if self.transition_side == "left":
                # 새 배경: 왼쪽 -> 오른쪽, 파티클: 왼쪽
                vx = random.uniform(-4.0, -1.0)
            else:
                # 새 배경: 오른쪽 -> 왼쪽, 파티클: 오른쪽
                vx = random.uniform(1.0, 4.0)

            vy = random.uniform(-2.8, 2.8)

            size = random.randint(3, 8)
            life = random.randint(20, 44)

            self.edge_particles.append({
                "x": float(edge_x + random.randint(-4, 4)),
                "y": float(y),
                "vx": vx,
                "vy": vy,
                "life": life,
                "max_life": life,
                "size": size,
                "alpha": random.randint(130, 230),
                "color": self.transition_particle_color,
            })

    def _update_edge_particles(self):
        alive = []

        for p in self.edge_particles:
            p["x"] += p["vx"]
            p["y"] += p["vy"]

            p["vy"] += 0.025
            p["life"] -= 1

            if p["life"] > 0:
                alive.append(p)

        self.edge_particles = alive

    def _draw_edge_particles(self):
        for p in self.edge_particles:
            life_ratio = max(0.0, p["life"] / max(1, p["max_life"]))
            alpha = int(p["alpha"] * life_ratio)

            color = p.get("color", (0, 0, 0))
            size = p["size"]

            surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            pygame.draw.circle(
                surf,
                (*color, alpha),
                (size, size),
                size,
            )

            self.screen.blit(
                surf,
                (int(p["x"] - size), int(p["y"] - size)),
            )
