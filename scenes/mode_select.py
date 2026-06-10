from systems.font_manager import font
from scenes.transition import Transition
import pygame
import math
import random
import os


class ModeSelect:
    MODES = [
        {
            "id":      "pvp",
            "title":   "PVP",
            "sub":     "2 Player Battle",
            "desc":    ["Fight against a friend locally.", "Pick your fighter and stage."],
            "color":   (55, 130, 230),
            "glow":    (110, 185, 255),
            "dark":    (20,  55, 130),
            "icon":    "assets/images/icons/pvp.png",
            "enabled": True,
        },
        {
            "id":      "story",
            "title":   "STORY",
            "sub":     "Solo Campaign",
            "desc":    ["Unravel the time-loop mystery.", "Face bosses across all stages."],
            "color":   (140, 60, 220),
            "glow":    (200, 130, 255),
            "dark":    (60,  20, 110),
            "icon":    "assets/images/icons/story.png",
            "enabled": True,
        },
    ]

    CARD_W   = 360
    CARD_H   = 430
    CARD_GAP = 80

    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.W = screen.get_width()
        self.H = screen.get_height()

        self.fnt_title  = font(48, bold=True)
        self.fnt_mode   = font(46, bold=True)
        self.fnt_sub    = font(18, bold=True)
        self.fnt_desc   = font(14)
        self.fnt_guide  = font(13)
        self.fnt_sm     = font(12, bold=True)

        self.cursor = 0
        self.done   = False
        self.result = None
        self._t     = 0.0

        # 입장 애니메이션
        self._enter_frame = 0
        self._entering    = True   # 처음 들어올 때 슬라이드인

        # 전환 이펙트
        self.transition = Transition("slash", duration=36)

        # 카드 아이콘 이미지 캐시
        self._icons: dict[str, pygame.Surface | None] = {}
        for m in self.MODES:
            path = m.get("icon", "")
            img  = None
            if path and os.path.exists(path):
                try:
                    raw = pygame.image.load(path).convert_alpha()
                    img = pygame.transform.smoothscale(raw, (100, 100))
                except Exception:
                    pass
            self._icons[m["id"]] = img

        total_w  = len(self.MODES)*self.CARD_W + (len(self.MODES)-1)*self.CARD_GAP
        self._x0 = (self.W - total_w) // 2

        # 배경
        rng = random.Random(99)
        self._stars = [
            (rng.randint(0,self.W), rng.randint(0,self.H),
             rng.uniform(0.3,1.8), rng.uniform(0.1,0.7))
            for _ in range(160)
        ]
        self._bg     = self._bake_bg()
        self._grid   = self._bake_grid()

        # 배경 이미지
        self._bg_img: pygame.Surface | None = None
        for p in ["assets/images/menu_bg.png","assets/images/menu_bg.jpg",
                  "assets/images/bg_stage_01.jpeg"]:
            if os.path.exists(p):
                try:
                    raw = pygame.image.load(p).convert()
                    self._bg_img = pygame.transform.smoothscale(raw,(self.W,self.H))
                    break
                except Exception:
                    pass

    def _bake_bg(self) -> pygame.Surface:
        sf = pygame.Surface((self.W, self.H))
        for y in range(self.H):
            t = y/self.H
            pygame.draw.line(sf,(int(4+t*10),int(5+t*10),int(14+t*22)),(0,y),(self.W,y))
        return sf

    def _bake_grid(self) -> pygame.Surface:
        """원근감 그리드 (배경 장식)."""
        sf = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        vp_x, vp_y = self.W//2, self.H//2
        for i in range(-12, 13):
            x0 = vp_x + i * 80
            pygame.draw.line(sf, (40, 55, 120, 18), (x0, 0), (vp_x, vp_y))
            pygame.draw.line(sf, (40, 55, 120, 18), (x0, self.H), (vp_x, vp_y))
        for j in range(1, 9):
            y = int(vp_y + j * (self.H//2 / 8))
            t = j / 8
            w = int(self.W * 0.1 + self.W * 0.9 * t)
            pygame.draw.line(sf,(40,55,120,int(20*t)),(vp_x-w//2,y),(vp_x+w//2,y))
        return sf

    # ── 이벤트 ──────────────────────────────────────────────────
    def handle_event(self, event: pygame.event.Event):
        if self.transition.active:
            return
        if event.type != pygame.KEYDOWN:
            return
        k = event.key
        n = len(self.MODES)

        if k in (pygame.K_a, pygame.K_LEFT):
            self.cursor = (self.cursor - 1) % n
        elif k in (pygame.K_d, pygame.K_RIGHT):
            self.cursor = (self.cursor + 1) % n
        elif k in (pygame.K_RETURN, pygame.K_f, pygame.K_SPACE):
            if self.MODES[self.cursor]["enabled"]:
                self.result = self.MODES[self.cursor]["id"]
                self.transition.start()

    def update(self):
        self._t += 0.025
        if self._entering:
            self._enter_frame += 1
            if self._enter_frame >= 40:
                self._entering = False

        self.transition.update()
        if self.transition.done:
            self.done = True

    # ── draw ────────────────────────────────────────────────────
    def draw(self):
        W, H = self.W, self.H

        # 배경
        if self._bg_img:
            self.screen.blit(self._bg_img,(0,0))
            ov = pygame.Surface((W,H),pygame.SRCALPHA); ov.fill((0,0,0,150))
            self.screen.blit(ov,(0,0))
        else:
            self.screen.blit(self._bg,(0,0))

        # 원근감 그리드
        self.screen.blit(self._grid,(0,0))

        # 별
        for sx,sy,sr,sa in self._stars:
            fl = sa + math.sin(self._t*2+sx*0.01)*0.15
            c  = int(max(0,min(255,fl*255)))
            pygame.draw.circle(self.screen,(c,c,c),(sx,sy),int(sr))

        # 입장 오프셋
        enter_off = 0
        if self._entering:
            p = self._enter_frame / 40
            p = 1 - (1-p)**3   # ease-out cubic
            enter_off = int((1-p) * H * 0.25)

        self._draw_title(enter_off)
        for i,mode in enumerate(self.MODES):
            self._draw_card(i, mode, enter_off)
        self._draw_guide(enter_off)

        # 전환 이펙트
        self.transition.draw(self.screen)

    def _draw_title(self, yoff):
        W = self.W
        pulse = abs(math.sin(self._t * 1.5))
        # 글로우
        glow = self.fnt_title.render("SMASH  DOCTORS", True, (60,110,255))
        for ox,oy in [(-3,0),(3,0),(0,-3),(0,3)]:
            glow.set_alpha(int(30+20*pulse))
            self.screen.blit(glow,(W//2-glow.get_width()//2+ox, 38+yoff+oy))
        t = self.fnt_title.render("SMASH  DOCTORS", True, (255,255,255))
        self.screen.blit(t,(W//2-t.get_width()//2, 38+yoff))
        s = self.fnt_sub.render("SELECT  MODE", True, (120,140,210))
        self.screen.blit(s,(W//2-s.get_width()//2, 98+yoff))
        # 라인
        lw = int(320 + 30*math.sin(self._t))
        lsf = pygame.Surface((lw,2),pygame.SRCALPHA)
        for x in range(lw):
            a = int(180 * math.sin(math.pi*x/lw))
            lsf.set_at((x,0),(70,100,220,a))
            lsf.set_at((x,1),(70,100,220,a//2))
        self.screen.blit(lsf,(self.W//2-lw//2, 124+yoff))

    def _card_rect(self, i) -> pygame.Rect:
        x = self._x0 + i*(self.CARD_W+self.CARD_GAP)
        return pygame.Rect(x,(self.H-self.CARD_H)//2+30,self.CARD_W,self.CARD_H)

    def _draw_card(self, i, mode, yoff):
        r   = self._card_rect(i)
        col = mode["color"]
        glw = mode["glow"]
        drk = mode["dark"]
        sel = (i == self.cursor)

        # 선택 카드: 위로 + 글로우
        float_off = -int(abs(math.sin(self._t*2.0))*14) if sel else 0
        rx = r.x; ry = r.y + float_off + yoff

        # ── 카드 그림자 ──
        if sel:
            sh = pygame.Surface((self.CARD_W+20, self.CARD_H+20), pygame.SRCALPHA)
            pygame.draw.rect(sh,(0,0,0,60),(10,10,self.CARD_W,self.CARD_H),border_radius=20)
            self.screen.blit(sh,(rx-10,ry+8))

        # ── 카드 배경 (그라디언트 느낌) ──
        card = pygame.Surface((self.CARD_W,self.CARD_H),pygame.SRCALPHA)
        for cy in range(self.CARD_H):
            ratio = cy/self.CARD_H
            # 선택 시 더 밝게
            base_a = int(45+ratio*30) if sel else int(25+ratio*18)
            r2,g2,b2 = col
            pygame.draw.line(card,
                (int(r2*(0.6+0.4*ratio)), int(g2*(0.6+0.4*ratio)),
                 int(b2*(0.6+0.4*ratio)), base_a),
                (0,cy),(self.CARD_W,cy))

        # 테두리
        bw = 3 if sel else 1
        bc = (*glw, 240 if sel else 55)
        pygame.draw.rect(card, bc,(0,0,self.CARD_W,self.CARD_H),bw,border_radius=18)
        self.screen.blit(card,(rx,ry))

        # ── 내부 상단 컬러 밴드 ──
        band = pygame.Surface((self.CARD_W-4,90),pygame.SRCALPHA)
        for cy in range(90):
            a = int(80*(1-cy/90))
            pygame.draw.line(band,(*col,a),(0,cy),(self.CARD_W-4,cy))
        self.screen.blit(band,(rx+2,ry+2))

        # ── 아이콘 ──
        icon_img = self._icons.get(mode["id"])
        if icon_img:
            ix = rx + self.CARD_W//2 - 50
            iy = ry + 50
            self.screen.blit(icon_img,(ix,iy))
        else:
            # 아이콘 없을 때 원형 placeholder
            g_r = 50 + int(math.sin(self._t*3)*5) if sel else 46
            gs  = pygame.Surface((g_r*2,g_r*2),pygame.SRCALPHA)
            pygame.draw.circle(gs,(*glw,40 if sel else 22),(g_r,g_r),g_r)
            pygame.draw.circle(gs,(*glw,100 if sel else 50),(g_r,g_r),g_r,2)
            # 심볼
            sym = "⚔" if mode["id"]=="pvp" else "📖"
            sf  = self.fnt_mode.render(sym,True,glw if sel else (*glw,))
            gs.blit(sf,(g_r-sf.get_width()//2, g_r-sf.get_height()//2))
            self.screen.blit(gs,(rx+self.CARD_W//2-g_r, ry+50))

        # ── 모드명 ──
        title_y = ry + 165
        tc  = (255,255,255) if sel else (*glw,)
        t_sf = self.fnt_mode.render(mode["title"], True, tc)
        self.screen.blit(t_sf,(rx+self.CARD_W//2-t_sf.get_width()//2, title_y))

        # ── 구분선 ──
        line_y = title_y + t_sf.get_height() + 10
        lw2 = self.CARD_W - 60
        for x in range(lw2):
            a = int((80 if sel else 40)*math.sin(math.pi*x/lw2))
            pygame.draw.line(self.screen,(*glw,a),
                (rx+30+x,line_y),(rx+30+x,line_y))
        pygame.draw.line(self.screen,(*glw,80 if sel else 35),
            (rx+30,line_y),(rx+self.CARD_W-30,line_y),1)

        # ── 부제 ──
        sub_y = line_y + 14
        sub_sf = self.fnt_sub.render(mode["sub"],True,
            (220,230,255) if sel else (160,165,190))
        self.screen.blit(sub_sf,(rx+self.CARD_W//2-sub_sf.get_width()//2,sub_y))

        # ── 설명 ──
        for li,line in enumerate(mode["desc"]):
            lc = (185,190,215) if sel else (120,125,150)
            ls = self.fnt_desc.render(line,True,lc)
            self.screen.blit(ls,(rx+self.CARD_W//2-ls.get_width()//2,
                sub_y+36+li*24))

        # ── 선택 표시 (화살표) ──
        if sel:
            acx = rx+self.CARD_W//2
            tip = ry-28-int(abs(math.sin(self._t*3.5))*10)
            pygame.draw.polygon(self.screen,glw,
                [(acx,tip),(acx-14,tip+20),(acx+14,tip+20)])
            # 하단 CONFIRM 힌트
            hint = self.fnt_sm.render("ENTER / F  to confirm",True,(*glw,))
            hint.set_alpha(int(160+80*abs(math.sin(self._t*2.5))))
            self.screen.blit(hint,(rx+self.CARD_W//2-hint.get_width()//2,
                ry+self.CARD_H-32))

    def _draw_guide(self, yoff):
        lines = [
            "A / D  or  ← / →   select",
            "ENTER / F   confirm",
        ]
        for i,txt in enumerate(lines):
            sf = self.fnt_guide.render(txt,True,(100,105,135))
            self.screen.blit(sf,(self.W//2-sf.get_width()//2,
                self.H-48+i*20+yoff//3))