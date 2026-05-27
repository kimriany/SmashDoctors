import pygame
from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TITLE,
    STOCK_COUNT, BLAST_MARGIN,
)
from engine.camera   import Camera
from engine.renderer import Renderer
from systems.event_bus   import EventBus
from systems.stage_loader import StageLoader
from systems.particle import ParticleSystem
from systems.floater  import FloaterSystem
from entities.player  import Player
from entities.boss    import Boss


class GameState:
    TITLE   = "title"
    PLAYING = "playing"
    WIN     = "win"


class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = GameState.TITLE

        # 서브시스템
        self.event_bus      = EventBus()
        self.camera         = Camera(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.renderer       = Renderer(self.screen)
        self.particle_sys   = ParticleSystem()
        self.floater_sys    = FloaterSystem()

        # 스테이지
        self.stage_loader = StageLoader("data/stages/stage_01.json")
        stage = self.stage_loader.load()
        self.platforms    = stage["platforms"]

        self.winner_name  = ""
        self.winner_color = (255, 255, 255)

        self._register_events()
        self._init_entities()

    # ─── 초기화 ─────────────────────────────────────────────
    def _init_entities(self):
        self.player1 = Player(200, 300, name="Player 1", player_id=1)
        self.player2 = Player(900, 300, name="Player 2", player_id=2)
        self.boss    = Boss(600, 300, name="Boss")
        self.boss.set_target(self.player1)

        # 스폰 위치 저장
        self.player1.spawn_x, self.player1.spawn_y = 200, 300
        self.player2.spawn_x, self.player2.spawn_y = 900, 300

        # 2P 모드: boss 대신 player2 사용
        self.vs_mode = True   # True = 2P 대전, False = 보스전

    def _register_events(self):
        self.event_bus.subscribe("attack_hit",   self._on_attack_hit)
        self.event_bus.subscribe("entity_dead",  self._on_entity_dead)
        self.event_bus.subscribe("skill_used",   self._on_skill_used)

    def reset(self):
        self.particle_sys = ParticleSystem()
        self.floater_sys  = FloaterSystem()
        self.event_bus    = EventBus()
        self._register_events()
        self._init_entities()
        self.state = GameState.PLAYING

    # ─── 메인 루프 ──────────────────────────────────────────
    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            self._handle_events()

            if self.state == GameState.TITLE:
                self.renderer.draw_background()
                self.renderer.draw_title_screen()
            elif self.state == GameState.PLAYING:
                self._update(dt)
                self._draw()
            elif self.state == GameState.WIN:
                self._draw()
                self.renderer.draw_win_screen(self.winner_name, self.winner_color)

            pygame.display.flip()

    # ─── 이벤트 처리 ────────────────────────────────────────
    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False

                if self.state == GameState.TITLE and event.key == pygame.K_RETURN:
                    self.reset()

                if self.state == GameState.WIN and event.key == pygame.K_RETURN:
                    self.reset()

                if self.state == GameState.PLAYING:
                    self.player1.handle_keydown(event.key, self.event_bus, self.particle_sys)
                    if self.vs_mode:
                        self.player2.handle_keydown(event.key, self.event_bus, self.particle_sys)

    # ─── 업데이트 ────────────────────────────────────────────
    def _update(self, dt):
        keys = pygame.key.get_pressed()
        self.player1.handle_input(keys)
        if self.vs_mode:
            self.player2.handle_input(keys)

        self.player1.update(dt, self.platforms, self.event_bus, self.particle_sys)
        if self.vs_mode:
            self.player2.update(dt, self.platforms, self.event_bus, self.particle_sys)
            # 충돌 체크
            self.player1.check_attack_collision(self.player2, self.event_bus, self.particle_sys, self.floater_sys)
            self.player2.check_attack_collision(self.player1, self.event_bus, self.particle_sys, self.floater_sys)
            self.player1.check_skill_collision(self.player2, self.event_bus, self.particle_sys, self.floater_sys)
            self.player2.check_skill_collision(self.player1, self.event_bus, self.particle_sys, self.floater_sys)
        else:
            self.boss.update(dt, self.platforms, self.event_bus, self.particle_sys)
            self.player1.check_attack_collision(self.boss, self.event_bus, self.particle_sys, self.floater_sys)
            self.boss.check_attack_collision(self.player1, self.event_bus, self.particle_sys, self.floater_sys)
            self.player1.check_skill_collision(self.boss, self.event_bus, self.particle_sys, self.floater_sys)
            self.boss.check_skill_collision(self.player1, self.event_bus, self.particle_sys, self.floater_sys)

        # 화면 밖 판정 (blast zone)
        self._check_blast_zones()

        # 파티클/플로터
        self.particle_sys.update()
        self.floater_sys.update()

        # 카메라: 살아있는 엔티티 기준
        alive_rects = [e.rect for e in self._all_entities() if not e.dead and not getattr(e, 'respawning', False)]
        if alive_rects:
            self.camera.follow_multi(alive_rects)

    def _all_entities(self):
        if self.vs_mode:
            return [self.player1, self.player2]
        return [self.player1, self.boss]

    def _check_blast_zones(self):
        """화면 밖으로 나간 플레이어 처리"""
        sw, sh = SCREEN_WIDTH, SCREEN_HEIGHT
        bm = BLAST_MARGIN

        for player in [self.player1] + ([self.player2] if self.vs_mode else []):
            if player.dead or player.respawning:
                continue
            sx = player.rect.x - self.camera.offset.x
            sy = player.rect.y - self.camera.offset.y
            if sx < -bm or sx > sw + bm or sy < -bm or sy > sh + bm:
                player.lose_stock(self.event_bus)

    # ─── 이벤트 핸들러 ──────────────────────────────────────
    def _on_attack_hit(self, data):
        attacker = data["attacker"]
        target   = data["target"]
        damage   = data["damage"]
        ps       = data.get("particle_system")
        fs       = data.get("floater_system")

        target.take_damage(damage)
        target.apply_knockback(attacker, damage)

        if ps:
            ps.spawn_hit(target.rect.centerx, target.rect.centery, target.color)
        if fs:
            color = (100, 200, 255) if data.get("is_skill") else (255, 220, 50)
            fs.spawn(target.rect.centerx, target.rect.top - 10, damage, color)

    def _on_entity_dead(self, data):
        entity = data["entity"]
        print(f"[Game] {entity.name} 사망")
        self._check_win()

    def _on_skill_used(self, data):
        print(f"[Game] {data['user'].name} 스킬 사용: {data['skill'].name}")

    def _check_win(self):
        if self.vs_mode:
            p1_out = self.player1.dead and self.player1.stocks <= 0
            p2_out = self.player2.dead and self.player2.stocks <= 0
            if p1_out:
                self.winner_name  = "Player 2"
                self.winner_color = self.player2.glow_color
                self.state = GameState.WIN
            elif p2_out:
                self.winner_name  = "Player 1"
                self.winner_color = self.player1.glow_color
                self.state = GameState.WIN
        else:
            if self.boss.dead:
                self.winner_name  = "Player 1"
                self.winner_color = self.player1.glow_color
                self.state = GameState.WIN
            elif self.player1.dead and self.player1.stocks <= 0:
                self.winner_name  = "Boss"
                self.winner_color = self.boss.glow_color
                self.state = GameState.WIN

    # ─── 렌더링 ─────────────────────────────────────────────
    def _draw(self):
        self.renderer.draw_background()
        self.renderer.draw_platforms(self.platforms, self.camera)
        self.particle_sys.draw(self.screen, self.camera.offset)

        for entity in self._all_entities():
            entity.draw(self.screen, self.camera)

        self.floater_sys.draw(self.screen, self.camera.offset)

        hud_players = [self.player1]
        if self.vs_mode:
            hud_players.append(self.player2)
        self.renderer.draw_hud(hud_players)
