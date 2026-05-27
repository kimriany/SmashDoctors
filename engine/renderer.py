"""배경·플랫폼·HUD 렌더링 모듈"""
import pygame
import math


class Renderer:
    def __init__(self, screen):
        self.screen = screen
        self.W = screen.get_width()
        self.H = screen.get_height()

        # 배경 레이어 (stars)
        import random
        self.stars = [
            (random.randint(0, self.W), random.randint(0, self.H),
             random.uniform(0.3, 1.5), random.uniform(0.2, 0.7))
            for _ in range(120)
        ]
        self.star_t = 0.0

        # 폰트
        self.font_lg = pygame.font.SysFont("Arial", 32, bold=True)
        self.font_md = pygame.font.SysFont("Arial", 20, bold=True)
        self.font_sm = pygame.font.SysFont("Arial", 14, bold=True)

    # ─── 배경 ────────────────────────────────────────────────
    def draw_background(self):
        self.star_t += 0.01
        # 그라디언트 배경
        for y in range(0, self.H, 4):
            ratio = y / self.H
            r = int(8 + ratio * 10)
            g = int(10 + ratio * 12)
            b = int(22 + ratio * 23)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (self.W, y))
            pygame.draw.line(self.screen, (r, g, b), (0, y+1), (self.W, y+1))
            pygame.draw.line(self.screen, (r, g, b), (0, y+2), (self.W, y+2))
            pygame.draw.line(self.screen, (r, g, b), (0, y+3), (self.W, y+3))

        # 별
        for sx, sy, sr, sa in self.stars:
            flicker = sa + math.sin(self.star_t * 2 + sx) * 0.15
            c = int(max(0, min(255, flicker * 255)))
            pygame.draw.circle(self.screen, (c, c, c), (sx, sy), int(sr))

        # 도시 실루엣
        self._draw_city()

    def _draw_city(self):
        city_color = (14, 18, 38)
        win_color  = (28, 45, 90)
        import random; rng = random.Random(42)
        x = 0
        while x < self.W:
            bw = rng.randint(40, 80)
            bh = rng.randint(40, 130)
            by = self.H - 80 - bh
            pygame.draw.rect(self.screen, city_color, (x, by, bw, bh + 80))
            # 창문
            for wy in range(by + 6, by + bh - 6, 14):
                for wxi in range(x + 6, x + bw - 6, 10):
                    if rng.random() > 0.55:
                        pygame.draw.rect(self.screen, win_color, (wxi, wy, 5, 7))
            x += bw + rng.randint(2, 8)

    # ─── 플랫폼 ─────────────────────────────────────────────
    def draw_platforms(self, platforms, camera):
        for p in platforms:
            dr = camera.apply_rect(p)
            is_main = p.h > 30

            # 플랫폼 본체
            base_color = (38, 52, 100) if is_main else (28, 42, 85)
            pygame.draw.rect(self.screen, base_color, dr, border_radius=6)

            # 상단 하이라이트
            top_color = (80, 110, 200) if is_main else (60, 90, 170)
            top_rect = pygame.Rect(dr.x, dr.y, dr.w, 5)
            pygame.draw.rect(self.screen, top_color, top_rect, border_radius=6)

            # 그리드 라인
            for gx in range(dr.x + 20, dr.x + dr.w - 10, 22):
                pygame.draw.line(self.screen, (55, 75, 140, 80), (gx, dr.y + 5), (gx, dr.y + dr.h), 1)

            # 테두리
            pygame.draw.rect(self.screen, (60, 90, 160), dr, 1, border_radius=6)

    # ─── HUD ─────────────────────────────────────────────────
    def draw_hud(self, players, timer=None):
        # 각 플레이어 패널
        for i, p in enumerate(players):
            panel_x = 30 if i == 0 else self.W - 230
            self._draw_player_panel(p, panel_x, self.H - 125)

        # 중앙 스톡 표시
        self._draw_stocks_center(players)

        # 타이머 (있을 경우)
        if timer is not None:
            t_surf = self.font_lg.render(str(int(timer)), True, (220, 220, 255))
            self.screen.blit(t_surf, (self.W // 2 - t_surf.get_width() // 2, 12))

    def _draw_player_panel(self, player, x, y):
        W, H = 200, 110
        # 반투명 배경
        panel = pygame.Surface((W, H), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 160))
        pygame.draw.rect(panel, (*player.glow_color, 80), (0, 0, W, H), 2, border_radius=8)
        self.screen.blit(panel, (x, y))

        # 이름
        nm = self.font_md.render(player.name, True, player.glow_color)
        self.screen.blit(nm, (x + 10, y + 8))

        # 데미지 % (스매시 스타일)
        pct = int(player.damage_pct)
        if pct < 50:
            dmg_color = (255, 255, 255)
        elif pct < 100:
            dmg_color = (255, 230, 80)
        else:
            dmg_color = (255, 70, 70)

        dmg_surf = self.font_lg.render(f"{pct}%", True, dmg_color)
        self.screen.blit(dmg_surf, (x + 10, y + 30))

        # HP 바
        bar_x, bar_y = x + 10, y + 72
        bar_w = W - 20
        pygame.draw.rect(self.screen, (30, 30, 30), (bar_x, bar_y, bar_w, 12), border_radius=4)
        hp_ratio = max(0, player.hp / player.max_hp)
        hp_color = player.color if hp_ratio > 0.4 else (255, 80, 80)
        pygame.draw.rect(self.screen, hp_color, (bar_x, bar_y, int(bar_w * hp_ratio), 12), border_radius=4)
        hp_label = self.font_sm.render("HP", True, (160, 160, 180))
        self.screen.blit(hp_label, (bar_x, bar_y - 14))

        # 피로도 바
        fat_y = bar_y + 16
        pygame.draw.rect(self.screen, (30, 30, 30), (bar_x, fat_y, bar_w, 7), border_radius=3)
        fat_ratio = player.fatigue / player.max_fatigue
        pygame.draw.rect(self.screen, (140, 60, 220), (bar_x, fat_y, int(bar_w * fat_ratio), 7), border_radius=3)
        fat_label = self.font_sm.render("FATIGUE", True, (120, 80, 180))
        self.screen.blit(fat_label, (bar_x, fat_y - 14))

        # 스킬 쿨다운
        skill = list(player.skills.values())[0]
        if skill.current_cooldown > 0:
            cd_ratio = skill.current_cooldown / skill.cooldown
            cd_surf = self.font_sm.render(
                f"SKILL CD: {skill.current_cooldown // 10 + 1}s", True, (180, 100, 100)
            )
        else:
            cd_surf = self.font_sm.render("SKILL READY!", True, (100, 220, 100))
        self.screen.blit(cd_surf, (x + 10, y + 96))

    def _draw_stocks_center(self, players):
        cx = self.W // 2
        for i, p in enumerate(players):
            base_x = cx - 80 if i == 0 else cx + 10
            for s in range(3):
                filled = s < p.stocks
                color = p.color if filled else (50, 50, 60)
                border = p.glow_color if filled else (80, 80, 90)
                pygame.draw.circle(self.screen, color,  (base_x + s * 26, 22), 10)
                pygame.draw.circle(self.screen, border, (base_x + s * 26, 22), 10, 2)
                if filled:
                    pygame.draw.circle(self.screen, (255, 255, 255, 80), (base_x + s*26 - 3, 18), 4)

    # ─── 오버레이 ────────────────────────────────────────────
    def draw_title_screen(self):
        overlay = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))

        title = pygame.font.SysFont("Arial", 58, bold=True).render("⚡ SMASH DOCTORS", True, (255, 255, 255))
        sub   = self.font_md.render("SCIENCE SMASH PROTOTYPE", True, (120, 140, 200))

        self.screen.blit(title, (self.W//2 - title.get_width()//2, 140))
        self.screen.blit(sub,   (self.W//2 - sub.get_width()//2,   210))

        controls = [
            ("PLAYER 1 (Blue)",  "A/D: 이동  |  W: 점프  |  F: 공격  |  G: 스킬", (120, 180, 255)),
            ("PLAYER 2 (Red)",   "←/→: 이동  |  ↑: 점프  |  L: 공격  |  ;: 스킬", (255, 120, 120)),
        ]
        for i, (name, ctrl, color) in enumerate(controls):
            nm_surf = self.font_md.render(name, True, color)
            ct_surf = self.font_sm.render(ctrl, True, (200, 200, 220))
            base_y  = 310 + i * 60
            self.screen.blit(nm_surf, (self.W//2 - nm_surf.get_width()//2, base_y))
            self.screen.blit(ct_surf, (self.W//2 - ct_surf.get_width()//2, base_y + 26))

        start = self.font_lg.render("PRESS ENTER TO START", True, (255, 255, 100))
        self.screen.blit(start, (self.W//2 - start.get_width()//2, 460))

    def draw_win_screen(self, winner_name, winner_color):
        overlay = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 210))
        self.screen.blit(overlay, (0, 0))

        win = pygame.font.SysFont("Arial", 52, bold=True).render(
            f"{winner_name} WINS!", True, winner_color
        )
        restart = self.font_md.render("PRESS ENTER to play again  |  ESC to quit", True, (180, 180, 200))
        self.screen.blit(win,     (self.W//2 - win.get_width()//2,     240))
        self.screen.blit(restart, (self.W//2 - restart.get_width()//2, 330))

    def draw_scanlines(self):
        for y in range(0, self.H, 5):
            pygame.draw.line(self.screen, (0, 0, 0, 25), (0, y), (self.W, y))
