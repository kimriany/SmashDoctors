import pygame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TITLE, BLAST_MARGIN

from engine.camera    import Camera
from engine.renderer  import Renderer
from systems.event_bus    import EventBus
from systems.stage_loader import StageLoader
from systems.particle  import ParticleSystem
from systems.floater   import FloaterSystem

from scenes.character_select import CharacterSelect
from scenes.stage_select     import StageSelect


class GameState:
    TITLE     = "title"
    CHAR_SEL  = "char_select"
    STAGE_SEL = "stage_select"
    PLAYING   = "playing"
    WIN       = "win"


class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock   = pygame.time.Clock()
        self.running = True
        self.state   = GameState.TITLE

        self.camera   = Camera(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.renderer = Renderer(self.screen)

        self.char_select  = CharacterSelect(self.screen)
        self.stage_select = StageSelect(self.screen)

        self.platforms    = []
        self.winner_name  = ""
        self.winner_color = (255,255,255)

        self._cls_p1     = None
        self._cls_p2     = None
        self._stage_info = None

        self.event_bus    = None
        self.particle_sys = None
        self.floater_sys  = None
        self.player1 = None
        self.player2 = None

    # ─── 게임 시작 ─────────────────────────────────────────────
    def _start_game(self):
        self.event_bus    = EventBus()
        self.particle_sys = ParticleSystem()
        self.floater_sys  = FloaterSystem()

        data = StageLoader(self._stage_info["path"]).load()
        self.platforms = data["platforms"]
        sp1 = data.get("player_spawn", [220, 340])
        sp2 = data.get("boss_spawn",   [940, 340])

        self.player1 = self._cls_p1(sp1[0], sp1[1], name="Player 1", player_id=1)
        self.player2 = self._cls_p2(sp2[0], sp2[1], name="Player 2", player_id=2)
        self.player1.spawn_x, self.player1.spawn_y = sp1[0], sp1[1]
        self.player2.spawn_x, self.player2.spawn_y = sp2[0], sp2[1]

        # 스테이지 배경 이미지 로드
        self.renderer.load_stage_background(self._stage_info["id"])

        self.event_bus.subscribe("attack_hit",  self._on_attack_hit)
        self.event_bus.subscribe("entity_dead", self._on_entity_dead)

        self.state = GameState.PLAYING

    def _restart(self):
        self.char_select  = CharacterSelect(self.screen)
        self.stage_select = StageSelect(self.screen)
        self._cls_p1 = self._cls_p2 = self._stage_info = None
        self.state = GameState.CHAR_SEL

    # ─── 메인 루프 ─────────────────────────────────────────────
    def run(self):
        while self.running:
            self.clock.tick(FPS)
            self._handle_events()

            if self.state == GameState.TITLE:
                self.renderer.draw_background()
                self.renderer.draw_title_screen()

            elif self.state == GameState.CHAR_SEL:
                self.char_select.update()
                self.char_select.draw()

            elif self.state == GameState.STAGE_SEL:
                self.stage_select.update()
                self.stage_select.draw()

            elif self.state == GameState.PLAYING:
                self._update()
                self._draw_game()

            elif self.state == GameState.WIN:
                self._draw_game()
                self.renderer.draw_win_screen(self.winner_name, self.winner_color)

            pygame.display.flip()

    # ─── 이벤트 ────────────────────────────────────────────────
    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.KEYDOWN:
                k = event.key

                if k == pygame.K_ESCAPE:
                    if self.state in (GameState.PLAYING, GameState.WIN):
                        self._restart()
                    else:
                        self.running = False

                if self.state == GameState.TITLE:
                    if k == pygame.K_RETURN:
                        self.state = GameState.CHAR_SEL

                elif self.state == GameState.CHAR_SEL:
                    self.char_select.handle_event(event)
                    # 둘 다 LOCKED 후 ENTER → 다음 단계
                    if self.char_select.done and k == pygame.K_RETURN:
                        self._cls_p1, self._cls_p2 = self.char_select.result
                        self.stage_select = StageSelect(self.screen)
                        self.state = GameState.STAGE_SEL

                elif self.state == GameState.STAGE_SEL:
                    self.stage_select.handle_event(event)
                    if self.stage_select.done:
                        self._stage_info = self.stage_select.result
                        self._start_game()

                elif self.state == GameState.PLAYING:
                    self.player1.handle_keydown(k, self.event_bus, self.particle_sys)
                    self.player2.handle_keydown(k, self.event_bus, self.particle_sys)

                elif self.state == GameState.WIN:
                    if k == pygame.K_RETURN:
                        self._restart()

    # ─── 업데이트 ──────────────────────────────────────────────
    def _update(self):
        keys = pygame.key.get_pressed()
        self.player1.handle_input(keys)
        self.player2.handle_input(keys)

        ps = self.particle_sys
        fs = self.floater_sys

        self.player1.update(0, self.platforms, self.event_bus, ps)
        self.player2.update(0, self.platforms, self.event_bus, ps)

        self.player1.check_attack_collision(self.player2, self.event_bus, ps, fs)
        self.player2.check_attack_collision(self.player1, self.event_bus, ps, fs)
        self.player1.check_skill_collision( self.player2, self.event_bus, ps, fs)
        self.player2.check_skill_collision( self.player1, self.event_bus, ps, fs)

        self._check_blast_zones()
        ps.update()
        fs.update()

        active = [e.rect for e in [self.player1, self.player2]
                  if not e.dead and not getattr(e,'respawning',False)]
        if active:
            self.camera.update(active)   # follow_multi 대신 update 직접 호출

    def _check_blast_zones(self):
        for p in [self.player1, self.player2]:
            if p.dead or p.respawning:
                continue
            sx, sy = self.camera.world_to_screen(p.rect.x, p.rect.y)
            if (sx < -BLAST_MARGIN or sx > SCREEN_WIDTH  + BLAST_MARGIN or
                sy < -BLAST_MARGIN or sy > SCREEN_HEIGHT + BLAST_MARGIN):
                p.lose_stock(self.event_bus)

    # ─── 이벤트 핸들러 ─────────────────────────────────────────
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
            col = (80,200,255) if data.get("is_skill") else (255,220,50)
            fs.spawn(target.rect.centerx, target.rect.top-14, damage, col,
                     is_skill=data.get("is_skill",False))

    def _on_entity_dead(self, _):
        self._check_win()

    def _check_win(self):
        if self.player1.dead and self.player1.stocks <= 0:
            self.winner_name  = "Player 2"
            self.winner_color = self.player2.glow_color
            self.state = GameState.WIN
        elif self.player2.dead and self.player2.stocks <= 0:
            self.winner_name  = "Player 1"
            self.winner_color = self.player1.glow_color
            self.state = GameState.WIN

    # ─── 렌더링 ────────────────────────────────────────────────
    def _draw_game(self):
        self.renderer.draw_background()
        self.renderer.draw_platforms(self.platforms, self.camera)
        self.particle_sys.draw(self.screen, self.camera)   # camera 객체 전달
        self.player1.draw(self.screen, self.camera)
        self.player2.draw(self.screen, self.camera)
        self.floater_sys.draw(self.screen, self.camera)    # camera 객체 전달
        self.renderer.draw_hud([self.player1, self.player2])
