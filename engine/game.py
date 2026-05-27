import pygame

from settings import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TITLE
from engine.camera import Camera
from systems.event_bus import EventBus
from systems.stage_loader import StageLoader
from entities.player import Player
from entities.boss import Boss


class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(TITLE)

        self.clock = pygame.time.Clock()
        self.running = True

        self.event_bus = EventBus()
        self.camera = Camera(SCREEN_WIDTH, SCREEN_HEIGHT)

        self.stage_loader = StageLoader("data/stages/stage_01.json")
        self.stage = self.stage_loader.load()

        self.platforms = self.stage["platforms"]

        self.player = Player(200, 300, name="Player 1")
        self.boss = Boss(700, 300, name="Boss")

        self.entities = [
            self.player,
            self.boss,
        ]

        self.event_bus.subscribe("attack_hit", self.on_attack_hit)
        self.event_bus.subscribe("entity_dead", self.on_entity_dead)

        self.font = pygame.font.SysFont("arial", 24)

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            self.handle_events()
            self.update(dt)
            self.draw()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False

                self.player.handle_keydown(event.key, self.event_bus)

    def update(self, dt):
        keys = pygame.key.get_pressed()

        self.player.handle_input(keys)

        for entity in self.entities:
            entity.update(dt, self.platforms, self.event_bus)

        # 공격 판정 체크
        self.player.check_attack_collision(self.boss, self.event_bus)
        self.boss.check_attack_collision(self.player, self.event_bus)

        # 카메라는 일단 플레이어를 따라가도록 설정
        self.camera.follow(self.player.rect)

    def draw(self):
        self.screen.fill((25, 28, 38))

        # 배경
        pygame.draw.rect(self.screen, (35, 39, 53), (0, 430, 1000, 170))

        # 플랫폼
        for platform in self.platforms:
            draw_rect = self.camera.apply_rect(platform)
            pygame.draw.rect(self.screen, (110, 115, 130), draw_rect, border_radius=8)
            pygame.draw.rect(self.screen, (155, 160, 180), (draw_rect.x, draw_rect.y, draw_rect.w, 8), border_radius=8)

        # 엔티티
        for entity in self.entities:
            entity.draw(self.screen, self.camera)

        self.draw_ui()

        pygame.display.flip()

    def draw_ui(self):
        p_text = self.font.render(
            f"P1 HP: {self.player.hp} / Fatigue: {self.player.fatigue}",
            True,
            (240, 240, 240),
        )
        b_text = self.font.render(
            f"Boss HP: {self.boss.hp}",
            True,
            (240, 180, 180),
        )

        self.screen.blit(p_text, (20, 20))
        self.screen.blit(b_text, (20, 52))

    def on_attack_hit(self, data):
        attacker = data["attacker"]
        target = data["target"]
        damage = data["damage"]

        target.take_damage(damage)

        # 넉백
        if attacker.rect.centerx < target.rect.centerx:
            target.vel.x = 8
        else:
            target.vel.x = -8

        target.vel.y = -7

    def on_entity_dead(self, data):
        entity = data["entity"]
        print(f"{entity.name} died")
