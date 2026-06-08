from systems.font_manager import font
"""
Story Intro — 스토리 모드 진입창

구성:
  - 타이틀 + 배경 애니메이션
  - 저장 데이터 요약 (클리어 수 / 마지막 선택 캐릭터)
  - CONTINUE / NEW GAME / BACK 선택
"""
import pygame
import math
import random
import os

from systems.story_save   import StorySave
from systems.story_loader import StoryLoader


class StoryIntro:
    """
    result:
        "continue"  → 스테이지 선택창으로 (저장 데이터 유지)
        "new_game"  → 저장 초기화 후 스테이지 선택창으로
        "back"      → 모드 선택창으로
    """

    MENU_ITEMS = [
        ("CONTINUE",  "continue"),
        ("NEW GAME",  "new_game"),
        ("BACK",      "back"),
    ]

    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.W = screen.get_width()
        self.H = screen.get_height()

        self.fnt_title  = font(52, bold=True)
        self.fnt_sub    = font(20, bold=True)
        self.fnt_menu   = font(28, bold=True)
        self.fnt_info   = font(14)
        self.fnt_sm     = font(12)

        self.save   = StorySave()
        self.loader = StoryLoader()

        self.cursor = 0
        self.done   = False
        self.result = None
        self._t     = 0.0

        rng = random.Random(55)
        self._stars = [(rng.randint(0,self.W), rng.randint(0,self.H),
                        rng.uniform(0.3,1.6), rng.uniform(0.15,0.7)) for _ in range(150)]
        self._bg = self._bake_bg()

        # 배경 이미지 (있으면 사용)
        self._bg_img: pygame.Surface | None = None
        for p in ["assets/images/story_bg.png","assets/images/story_bg.jpg"]:
            if os.path.exists(p):
                try:
                    img = pygame.image.load(p).convert()
                    self._bg_img = pygame.transform.smoothscale(img, (self.W, self.H))
                    break
                except Exception: pass

    def _bake_bg(self) -> pygame.Surface:
        sf = pygame.Surface((self.W, self.H))
        for y in range(self.H):
            t = y/self.H
            pygame.draw.line(sf,(int(4+t*8),int(5+t*8),int(14+t*20)),(0,y),(self.W,y))
        return sf

    # ── 이벤트 ──────────────────────────────────────────────────
    def handle_event(self, event: pygame.event.Event):
        if event.type != pygame.KEYDOWN:
            return
        k = event.key
        n = len(self.MENU_ITEMS)

        if k in (pygame.K_w, pygame.K_UP):
            self.cursor = (self.cursor - 1) % n
        elif k in (pygame.K_s, pygame.K_DOWN):
            self.cursor = (self.cursor + 1) % n
        elif k in (pygame.K_RETURN, pygame.K_f, pygame.K_SPACE):
            label, result = self.MENU_ITEMS[self.cursor]

            # NEW GAME → 저장 초기화
            if result == "new_game":
                self.save.reset()

            # CONTINUE인데 저장 데이터 없으면 new_game처럼 동작
            if result == "continue" and self.save.cleared_count() == 0:
                result = "new_game"

            self.result = result
            self.done   = True

        elif k == pygame.K_ESCAPE:
            self.result = "back"
            self.done   = True

    def update(self):
        self._t += 0.03

    # ── draw ────────────────────────────────────────────────────
    def draw(self):
        # 배경
        if self._bg_img:
            # 배경 이미지 위에 어두운 오버레이
            self.screen.blit(self._bg_img, (0,0))
            ov = pygame.Surface((self.W,self.H), pygame.SRCALPHA)
            ov.fill((0,0,0,160))
            self.screen.blit(ov, (0,0))
        else:
            self.screen.blit(self._bg, (0,0))
            for sx,sy,sr,sa in self._stars:
                fl = sa + math.sin(self._t*2+sx*0.01)*0.18
                c  = int(max(0,min(255,fl*255)))
                pygame.draw.circle(self.screen,(c,c,c),(sx,sy),int(sr))

        self._draw_title()
        self._draw_save_info()
        self._draw_progress_bar()
        self._draw_menu()
        self._draw_guide()

    # ── 타이틀 ──────────────────────────────────────────────────
    def _draw_title(self):
        # 글로우 효과
        pulse = abs(math.sin(self._t * 1.2))
        glow_alpha = int(40 + 30 * pulse)
        glow = self.fnt_title.render("SMASH  DOCTORS", True, (80,120,255))
        for ox,oy in [(-2,0),(2,0),(0,-2),(0,2)]:
            glow.set_alpha(glow_alpha)
            self.screen.blit(glow, (self.W//2 - glow.get_width()//2 + ox, 60+oy))

        t = self.fnt_title.render("SMASH  DOCTORS", True, (255,255,255))
        self.screen.blit(t, (self.W//2 - t.get_width()//2, 60))

        s = self.fnt_sub.render("— STORY MODE —", True, (140,160,230))
        self.screen.blit(s, (self.W//2 - s.get_width()//2, 128))

        pygame.draw.line(self.screen, (60,90,200),
                         (self.W//2-200,158),(self.W//2+200,158),1)

    # ── 저장 정보 ────────────────────────────────────────────────
    def _draw_save_info(self):
        cleared = self.save.cleared_count()
        total   = self.loader.total

        px, py = self.W//2 - 160, 175
        pw, ph = 320, 76

        panel = pygame.Surface((pw,ph), pygame.SRCALPHA)
        pygame.draw.rect(panel,(5,8,22,200),(0,0,pw,ph),border_radius=10)
        pygame.draw.rect(panel,(60,80,180,80),(0,0,pw,ph),1,border_radius=10)
        self.screen.blit(panel,(px,py))

        if cleared == 0:
            msg = self.fnt_info.render("No save data found.", True, (150,150,170))
            self.screen.blit(msg,(px+12,py+12))
            hint = self.fnt_sm.render("Start a NEW GAME to begin.", True,(120,120,140))
            self.screen.blit(hint,(px+12,py+32))
        else:
            prog = self.fnt_info.render(
                f"Progress:  {cleared} / {total}  chapters cleared", True,(200,220,255))
            self.screen.blit(prog,(px+12,py+10))

            char = self.save.get_character()
            if char:
                ch_txt = self.fnt_info.render(f"Character: {char}", True,(180,200,240))
                self.screen.blit(ch_txt,(px+12,py+30))

            # 마지막 클리어 챕터 표시
            if self.save._data["cleared"]:
                last = max(self.save._data["cleared"])
                ch   = self.loader.get_chapter(last)
                if ch:
                    last_txt = self.fnt_sm.render(
                        f"Last cleared: {ch['title']} — {ch['subtitle']}",
                        True, (140,160,200))
                    self.screen.blit(last_txt,(px+12,py+52))

    # ── 진행도 바 ────────────────────────────────────────────────
    def _draw_progress_bar(self):
        total   = max(1, self.loader.total)
        cleared = self.save.cleared_count()

        bx, by = self.W//2 - 160, 265
        bw, bh = 320, 14

        pygame.draw.rect(self.screen,(18,18,36),(bx,by,bw,bh),border_radius=6)
        fw = int(bw * (cleared/total))
        if fw > 0:
            pygame.draw.rect(self.screen,(60,120,255),(bx,by,fw,bh),border_radius=6)
            pygame.draw.rect(self.screen,(120,180,255),(bx,by,fw,4),border_radius=6)
        pygame.draw.rect(self.screen,(60,80,160),(bx,by,bw,bh),1,border_radius=6)

        pct_txt = self.fnt_sm.render(f"{cleared}/{total}", True,(160,180,220))
        self.screen.blit(pct_txt,(bx+bw+8,by))

    # ── 메뉴 ────────────────────────────────────────────────────
    def _draw_menu(self):
        base_y = 320

        for i,(label,result) in enumerate(self.MENU_ITEMS):
            sel = (i == self.cursor)
            y   = base_y + i * 70

            # 선택 배경 카드
            if sel:
                pulse = abs(math.sin(self._t * 2.5))
                card  = pygame.Surface((300,52), pygame.SRCALPHA)
                pygame.draw.rect(card,(30,50,120,int(140+60*pulse)),
                                 (0,0,300,52),border_radius=10)
                pygame.draw.rect(card,(80,120,255,200),(0,0,300,52),2,border_radius=10)
                self.screen.blit(card,(self.W//2-150,y-6))

            # 비활성 조건 (CONTINUE인데 저장 없음)
            disabled = (result == "continue" and self.save.cleared_count() == 0)
            color = (100,100,120) if disabled else \
                    ((255,255,255) if sel else (170,170,200))

            txt = self.fnt_menu.render(label, True, color)
            self.screen.blit(txt,(self.W//2 - txt.get_width()//2, y))

            # 선택 화살표
            if sel and not disabled:
                ax = self.W//2 - 160 - int(abs(math.sin(self._t*4))*8)
                pygame.draw.polygon(self.screen,(80,140,255),
                    [(ax,y+14),(ax+14,y+6),(ax+14,y+22)])

            # 부설명
            sub = {
                "continue": "Resume from your last save",
                "new_game": "Start over from Chapter 1",
                "back":     "Return to mode select",
            }.get(result,"")
            if sub:
                sc = (80,80,100) if disabled else (130,140,170)
                st = self.fnt_sm.render(sub, True, sc)
                self.screen.blit(st,(self.W//2 - st.get_width()//2, y+30))

    # ── 가이드 ──────────────────────────────────────────────────
    def _draw_guide(self):
        rows = ["W / S  or  ↑ / ↓   navigate",
                "ENTER / F   confirm   |   ESC   back"]
        for i,txt in enumerate(rows):
            sf = self.fnt_sm.render(txt, True, (100,100,130))
            self.screen.blit(sf,(self.W//2-sf.get_width()//2, self.H-44+i*18))
