# engine/battle_session.py

import pygame

from settings import SCREEN_WIDTH, SCREEN_HEIGHT, BLAST_MARGIN

from engine.camera import Camera
from engine.renderer import Renderer

from systems.event_bus import EventBus
from systems.stage_loader import StageLoader
from systems.particle import ParticleSystem
from systems.floater import FloaterSystem
from systems.domain_system import DomainSystem


class BattleSession:
    """
    전투 한 판만 담당하는 클래스.

    mode="pvp":
        - player1, player2 둘 다 입력을 받음
        - 결과: "p1_win", "p2_win", "back"

    mode="story":
        - player1만 입력을 받음
        - player2는 보스/AI
        - 결과: "p1_dead", "p2_dead", "back"
    """

    def __init__(
        self,
        screen,
        stage_info,
        player1_cls,
        player2_cls,
        mode="pvp",
        player1_name=None,
        player2_name=None,
        player1_stocks=3,
        player2_stocks=3,
        dual_domain_bg_path="assets/images/Double_domain.jpeg",
    ):
        self.screen = screen
        self.stage_info = stage_info
        self.player1_cls = player1_cls
        self.player2_cls = player2_cls
        self.mode = mode

        self.player1_name = player1_name or ("Player" if mode == "story" else "Player 1")
        self.player2_name = player2_name or ("Boss" if mode == "story" else "Player 2")

        self.player1_stocks = player1_stocks
        self.player2_stocks = player2_stocks

        self.camera = Camera(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.renderer = Renderer(self.screen)

        self.event_bus = EventBus()
        self.particle_sys = ParticleSystem()
        self.floater_sys = FloaterSystem()

        self.domain_sys = None

        self.platforms = []
        self.player1 = None
        self.player2 = None

        self.result = None
        self.winner_name = ""
        self.winner_color = (255, 255, 255)

        self.dual_domain_bg_path = dual_domain_bg_path

        self._setup_battle()

    # ─────────────────────────────────────────────
    # 초기화
    # ─────────────────────────────────────────────
    def _setup_battle(self):
        data = StageLoader(self.stage_info["path"]).load()

        self.platforms = data["platforms"]

        sp1 = data.get("player_spawn", [220, 340])
        sp2 = data.get("boss_spawn", [940, 340])

        if self.player2_cls is None:
            from entities.characters.Einstein import Einstein
            self.player2_cls = Einstein

        self.player1 = self.player1_cls(
            sp1[0],
            sp1[1],
            name=self.player1_name,
            player_id=1,
        )

        self.player2 = self.player2_cls(
            sp2[0],
            sp2[1],
            name=self.player2_name,
            player_id=2,
        )

        self.player1.spawn_x = sp1[0]
        self.player1.spawn_y = sp1[1]
        self.player2.spawn_x = sp2[0]
        self.player2.spawn_y = sp2[1]

        self.player1.stocks = self.player1_stocks
        self.player2.stocks = self.player2_stocks

        stage_id = self.stage_info.get("id")
        if stage_id is not None:
            self.renderer.load_stage_background(stage_id)

        self.domain_sys = DomainSystem(
            screen=self.screen,
            renderer=self.renderer,
            camera=self.camera,
            event_bus=self.event_bus,
            particle_sys=self.particle_sys,
            dual_domain_bg_path=self.dual_domain_bg_path,
        )

        self.event_bus.subscribe("domain_request", self.domain_sys.on_domain_request)
        self.event_bus.subscribe("attack_hit", self.domain_sys.on_attack_hit)

        self.event_bus.subscribe("attack_hit", self._on_attack_hit)
        self.event_bus.subscribe("entity_dead", self._on_entity_dead)

    # ─────────────────────────────────────────────
    # 외부 호출
    # ─────────────────────────────────────────────
    def update(self, events):
        if self.result is not None:
            return self.result

        self._handle_events(events)
        self._update_frame()

        return self.result

    def draw(self):
        self._draw_game()

    def draw_win(self):
        self._draw_game()
        self.renderer.draw_win_screen(self.winner_name, self.winner_color)

    # ─────────────────────────────────────────────
    # 입력
    # ─────────────────────────────────────────────
    def _handle_events(self, events):
        for event in events:
            if event.type != pygame.KEYDOWN:
                continue

            k = event.key

            if k == pygame.K_ESCAPE:
                self.result = "back"
                return

            if self.domain_sys and self.domain_sys.gameplay_frozen:
                continue

            if self.mode == "pvp":
                self.player1.handle_keydown(k, self.event_bus, self.particle_sys)
                self.player2.handle_keydown(k, self.event_bus, self.particle_sys)

            elif self.mode == "story":
                self.player1.handle_keydown(k, self.event_bus, self.particle_sys)

    # ─────────────────────────────────────────────
    # 업데이트
    # ─────────────────────────────────────────────
    def _update_frame(self):
        if self.domain_sys:
            self.domain_sys.update()

        if self.domain_sys and self.domain_sys.gameplay_frozen:
            self.particle_sys.update()
            self.floater_sys.update()
            return

        keys = pygame.key.get_pressed()

        self.player1.handle_input(keys)

        if self.mode == "pvp":
            self.player2.handle_input(keys)

        elif self.mode == "story":
            self._update_story_boss_ai()

        ps = self.particle_sys
        fs = self.floater_sys

        self.player1.update(0, self.platforms, self.event_bus, ps)
        self.player2.update(0, self.platforms, self.event_bus, ps)

        self.player1.check_attack_collision(self.player2, self.event_bus, ps, fs)
        self.player2.check_attack_collision(self.player1, self.event_bus, ps, fs)

        self.player1.check_skill_collision(self.player2, self.event_bus, ps, fs)
        self.player2.check_skill_collision(self.player1, self.event_bus, ps, fs)

        self._check_blast_zones()

        ps.update()
        fs.update()

        self._update_camera()

    def _update_story_boss_ai(self):
        if hasattr(self.player2, "ai_update"):
            self.player2.ai_update(
                self.player1,
                self.platforms,
                self.event_bus,
                self.particle_sys,
            )

        elif hasattr(self.player2, "handle_ai"):
            self.player2.handle_ai(self.player1)

    def _update_camera(self):
        active = []

        for entity in (self.player1, self.player2):
            if entity.dead:
                continue

            if getattr(entity, "respawning", False):
                continue

            active.append(entity.rect)

        if active:
            self.camera.update(active)

    # ─────────────────────────────────────────────
    # 장외 판정
    # ─────────────────────────────────────────────
    def _check_blast_zones(self):
        for p in (self.player1, self.player2):
            if p.dead:
                continue

            if getattr(p, "respawning", False):
                continue

            sx, sy = self.camera.world_to_screen(p.rect.x, p.rect.y)

            if (
                sx < -BLAST_MARGIN
                or sx > SCREEN_WIDTH + BLAST_MARGIN
                or sy < -BLAST_MARGIN
                or sy > SCREEN_HEIGHT + BLAST_MARGIN
            ):
                if hasattr(p, "lose_stock"):
                    p.lose_stock(self.event_bus)

    # ─────────────────────────────────────────────
    # 이벤트 버스 콜백
    # ─────────────────────────────────────────────
    def _on_attack_hit(self, data):
        attacker = data["attacker"]
        target = data["target"]
        damage = data["damage"]

        ps = data.get("particle_system")
        fs = data.get("floater_system")

        target.take_damage(damage)
        target.apply_knockback(attacker, damage)

        if ps:
            ps.spawn_hit(
                target.rect.centerx,
                target.rect.centery,
                target.color,
            )

        if fs:
            col = (80, 200, 255) if data.get("is_skill") else (255, 220, 50)

            fs.spawn(
                target.rect.centerx,
                target.rect.top - 14,
                damage,
                col,
                is_skill=data.get("is_skill", False),
            )

    def _on_entity_dead(self, _data):
        self._check_result()

    # ─────────────────────────────────────────────
    # 결과 판정
    # ─────────────────────────────────────────────
    def _check_result(self):
        p1_dead = self.player1.dead and self.player1.stocks <= 0
        p2_dead = self.player2.dead and self.player2.stocks <= 0

        if not p1_dead and not p2_dead:
            return

        if self.mode == "pvp":
            if p1_dead:
                self.winner_name = "Player 2"
                self.winner_color = self.player2.glow_color
                self.result = "p2_win"

            elif p2_dead:
                self.winner_name = "Player 1"
                self.winner_color = self.player1.glow_color
                self.result = "p1_win"

        elif self.mode == "story":
            if p1_dead:
                self.result = "p1_dead"

            elif p2_dead:
                self.result = "p2_dead"

    # ─────────────────────────────────────────────
    # 렌더링
    # ─────────────────────────────────────────────
    def _draw_game(self):
        if self.domain_sys:
            self.domain_sys.draw_background()
        else:
            self.renderer.draw_background()

        self.renderer.draw_platforms(self.platforms, self.camera)

        self.particle_sys.draw(self.screen, self.camera)

        self.player1.draw(self.screen, self.camera)
        self.player2.draw(self.screen, self.camera)

        self.floater_sys.draw(self.screen, self.camera)

        self.renderer.draw_hud([self.player1, self.player2])