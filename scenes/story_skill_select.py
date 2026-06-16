import pygame

from settings import SCREEN_WIDTH, SCREEN_HEIGHT
from systems.font_manager import font
from entities.characters.StoryPlayer import StoryPlayer


class StorySkillSelect:
    def __init__(self, screen, battle_config=None, initial_loadout=None):
        self.screen = screen
        self.W = screen.get_width()
        self.H = screen.get_height()

        self.battle_config = battle_config or {}
        self.initial_loadout = initial_loadout or {}

        self.q_options = StoryPlayer.get_story_skill_options("skill_Q")
        self.e_options = StoryPlayer.get_story_skill_options("skill_E")

        self.q_index = self._initial_index(self.q_options, self.initial_loadout.get("skill_Q"))
        self.e_index = self._initial_index(self.e_options, self.initial_loadout.get("skill_E"))
        self.focus = "skill_Q"

        self.done = False
        self.result = None

        self.fnt_title = font(34, bold=True)
        self.fnt_lg = font(20, bold=True)
        self.fnt_md = font(15, bold=True)
        self.fnt_sm = font(12)
        self.fnt_xs = font(11)

        self._t = 0.0
        self._mouse = (0, 0)
        self._q_rects = []
        self._e_rects = []

    def _initial_index(self, options, skill_id):
        for i, opt in enumerate(options):
            if opt["id"] == skill_id:
                return i
        return 0

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self._mouse = event.pos
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, rect in enumerate(self._q_rects):
                if rect.collidepoint(event.pos):
                    self.q_index = i
                    self.focus = "skill_Q"
                    return
            for i, rect in enumerate(self._e_rects):
                if rect.collidepoint(event.pos):
                    self.e_index = i
                    self.focus = "skill_E"
                    return

        if event.type != pygame.KEYDOWN:
            return

        if event.key in (pygame.K_a, pygame.K_LEFT, pygame.K_q):
            self.focus = "skill_Q"
        elif event.key in (pygame.K_d, pygame.K_RIGHT, pygame.K_e):
            self.focus = "skill_E"
        elif event.key in (pygame.K_w, pygame.K_UP):
            self._move_focus(-1)
        elif event.key in (pygame.K_s, pygame.K_DOWN):
            self._move_focus(1)
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
            self.done = True
            self.result = {
                "skill_Q": self.q_options[self.q_index]["id"],
                "skill_E": self.e_options[self.e_index]["id"],
            }

    def _move_focus(self, delta):
        if self.focus == "skill_Q":
            self.q_index = (self.q_index + delta) % len(self.q_options)
        else:
            self.e_index = (self.e_index + delta) % len(self.e_options)

    def update(self):
        self._t += 0.045

    def draw(self):
        self.update()
        self._draw_bg()

        title = self.fnt_title.render("Hora Skill Loadout", True, (245, 250, 255))
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 42))

        boss_name = self.battle_config.get("boss_name", "Boss")
        boss_key = self.battle_config.get("boss_key", "unknown")
        boss_txt = self.fnt_md.render(f"VS  {boss_name}  /  {boss_key.upper()}", True, (255, 210, 170))
        self.screen.blit(boss_txt, (SCREEN_WIDTH // 2 - boss_txt.get_width() // 2, 83))

        left = 118
        top = 128
        col_w = 492
        self._q_rects = self._draw_column(
            "Q SKILL",
            self.q_options,
            self.q_index,
            left,
            top,
            col_w,
            self.focus == "skill_Q",
        )
        self._e_rects = self._draw_column(
            "E SKILL",
            self.e_options,
            self.e_index,
            SCREEN_WIDTH - left - col_w,
            top,
            col_w,
            self.focus == "skill_E",
        )

        q = self.q_options[self.q_index]
        e = self.e_options[self.e_index]
        summary = self.fnt_md.render(
            f"Q: {q['source']} / {q['name']}     E: {e['source']} / {e['name']}",
            True,
            (210, 235, 255),
        )
        self.screen.blit(summary, (SCREEN_WIDTH // 2 - summary.get_width() // 2, SCREEN_HEIGHT - 72))

        hint = self.fnt_sm.render("A/D focus   W/S select   ENTER battle", True, (145, 155, 185))
        self.screen.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, SCREEN_HEIGHT - 42))

    def _draw_bg(self):
        self.screen.fill((6, 9, 22))
        for y in range(SCREEN_HEIGHT):
            t = y / SCREEN_HEIGHT
            col = (int(6 + 10 * t), int(9 + 12 * t), int(22 + 28 * t))
            pygame.draw.line(self.screen, col, (0, y), (SCREEN_WIDTH, y))

        for i in range(28):
            x = (i * 79 + int(self._t * 18)) % (SCREEN_WIDTH + 120) - 60
            y = 118 + (i * 37) % 470
            alpha = 24 + (i % 4) * 12
            pygame.draw.circle(self.screen, (80, 180, 230, alpha), (x, y), 1 + i % 3)

    def _draw_column(self, title, options, selected, x, y, w, focused):
        rects = []
        header_col = (95, 220, 255) if focused else (160, 175, 205)
        header = self.fnt_lg.render(title, True, header_col)
        self.screen.blit(header, (x, y - 36))

        border_col = (95, 220, 255) if focused else (55, 70, 105)
        pygame.draw.rect(self.screen, (8, 12, 30), (x - 12, y - 12, w + 24, 428), border_radius=8)
        pygame.draw.rect(self.screen, border_col, (x - 12, y - 12, w + 24, 428), 1, border_radius=8)

        card_h = 48
        gap = 6
        for i, opt in enumerate(options):
            cy = y + i * (card_h + gap)
            rect = pygame.Rect(x, cy, w, card_h)
            rects.append(rect)

            selected_here = i == selected
            hover = rect.collidepoint(self._mouse)
            bg = (20, 34, 58) if selected_here else (12, 17, 36)
            if hover and not selected_here:
                bg = (18, 25, 48)
            pygame.draw.rect(self.screen, bg, rect, border_radius=7)

            accent = (95, 220, 255) if selected_here else (74, 92, 135)
            pygame.draw.rect(self.screen, accent, rect, 2 if selected_here else 1, border_radius=7)
            pygame.draw.rect(self.screen, accent, (rect.x, rect.y, 4, rect.h), border_radius=7)

            src = self.fnt_xs.render(opt["source"], True, (255, 215, 130))
            nm = self.fnt_md.render(opt["name"], True, (235, 245, 255))
            desc = self.fnt_xs.render(opt["desc"], True, (150, 165, 195))

            self.screen.blit(src, (rect.x + 14, rect.y + 6))
            self.screen.blit(nm, (rect.x + 104, rect.y + 6))
            self.screen.blit(desc, (rect.x + 104, rect.y + 27))

        return rects
