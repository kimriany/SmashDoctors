from systems.font_manager import font
"""
Character Select — 스킬 아이콘 + 툴팁 (마우스 오버) + 궁극기 슬롯
"""
import pygame
import math
import random
import os
from scenes.transition import Transition

from entities.characters.Pita        import Pita
from entities.characters.Nobel       import Nobel
from entities.characters.Einstein    import Einstein
from entities.characters.Schrödinger import Schrödinger
from entities.characters.Turing      import Turing
from entities.characters.Hoking      import Hoking
from entities.characters.Curie       import Curie
ROSTER = [
    Pita,
    Nobel,
    Einstein,
    Schrödinger,
    Turing,
    Hoking,
    Curie,
    # 여기에 캐릭터 계속 추가하면 됨
    # Newton,
    # Darwin,
    # Tesla,
]

PAGE_SIZE = 4

CARD_W   = 240
CARD_H   = 420
CARD_GAP = 18
CARD_Y   = 95

PAGE_ARROW_W = 54
PAGE_ARROW_H = 86

# 스킬 슬롯 정의 (key, 표시이름, P1키힌트, P2키힌트)
# player.py 키 매핑: Q/;=skill_Q  E/'=skill_E  R//=skill_R
SKILL_SLOTS = [
    ("skill_Q", "BASIC", "Q",   ";"),
    ("skill_E", "CC",    "E",   "'"),
    ("skill_R", "ULT",   "R",   "/"),
]


def _wrap(text: str, font: pygame.font.Font, max_w: int) -> list[str]:
    words = text.split()
    lines, line = [], ""
    for w in words:
        test = (line + " " + w).strip()
        if font.size(test)[0] <= max_w:
            line = test
        else:
            if line: lines.append(line)
            line = w
    if line: lines.append(line)
    return lines or [""]


class CharacterSelect:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.W = screen.get_width()
        self.H = screen.get_height()

        self.fnt_title = font(34, bold=True)
        self.fnt_lg    = font(17, bold=True)
        self.fnt_md    = font(13, bold=True)
        self.fnt_sm    = font(11, bold=True)
        self.fnt_xs    = font(10)

        self.cursors = [0, 1]
        self.locked  = [False, False]
        self._t      = 0.0
        self.done    = False
        self.result  = (None, None)

        self._mouse   = (0, 0)
        self._tooltip: tuple | None = None   # (char_idx, sk_key)

        self.page = 0
        self.page_count = max(1, math.ceil(len(ROSTER) / PAGE_SIZE))

        total_w = PAGE_SIZE * CARD_W + (PAGE_SIZE - 1) * CARD_GAP
        self._x0 = (self.W - total_w) // 2

        arrow_y = CARD_Y + CARD_H // 2 - PAGE_ARROW_H // 2
        self._page_prev_rect = pygame.Rect(18, arrow_y, PAGE_ARROW_W, PAGE_ARROW_H)
        self._page_next_rect = pygame.Rect(self.W - 18 - PAGE_ARROW_W, arrow_y, PAGE_ARROW_W, PAGE_ARROW_H)

        rng = random.Random(13)
        self._stars = [(rng.randint(0, self.W), rng.randint(0, self.H),
                        rng.uniform(0.3,1.5), rng.uniform(0.2,0.7)) for _ in range(100)]
        self._bg = self._bake_bg()

        # 썸네일
        TW, TH = 96, 114
        self._thumbs: dict[str, pygame.Surface | None] = {}
        for cls in ROSTER:
            path  = getattr(cls,"SPRITE_IDLE",None) or getattr(cls,"SPRITE_PATH",None)
            thumb = None
            if path and os.path.exists(path):
                try:
                    img   = pygame.image.load(path).convert_alpha()
                    thumb = pygame.transform.smoothscale(img, (TW, TH))
                except Exception: pass
            self._thumbs[cls.__name__] = thumb

        # 전환 이펙트 + 입장 애니메이션
        self.transition  = Transition('wipe', duration=32)
        self._enter_t    = 0.0
        self._entered    = False

        # 아이콘 히트박스 — 초기화 시 미리 계산해 둠
        self._icon_rects: dict[tuple, pygame.Rect] = {}
        self._rebuild_icon_rects()

    # ── 아이콘 히트박스 사전 계산 ────────────────────────────────
    def _rebuild_icon_rects(self):
        """현재 페이지에 보이는 카드들의 스킬 아이콘 히트박스 계산."""
        self._icon_rects.clear()

        ICON_W = 48
        n = len(SKILL_SLOTS)
        pad = (CARD_W - n * ICON_W) // (n + 1)
        ICON_Y_OFF = CARD_Y + 120 + 24 + 8 + 3 * 20 + 10

        for slot, char_idx in enumerate(self._visible_indices()):
            card_x = self._x0 + slot * (CARD_W + CARD_GAP)

            for si, (sk_key, _, _, _) in enumerate(SKILL_SLOTS):
                ix = card_x + pad + si * (ICON_W + pad)
                iy = ICON_Y_OFF
                self._icon_rects[(char_idx, sk_key)] = pygame.Rect(
                    ix - 2,
                    iy - 14,
                    ICON_W + 4,
                    80,
                )
    def _bake_bg(self) -> pygame.Surface:
        sf = pygame.Surface((self.W, self.H))
        for y in range(self.H):
            t = y/self.H
            pygame.draw.line(sf,(int(6+t*12),int(8+t*12),int(20+t*28)),(0,y),(self.W,y))
        return sf

    # ── 페이지 계산 ─────────────────────────────────────────────
    def _page_start(self) -> int:
        return self.page * PAGE_SIZE

    def _page_end(self) -> int:
        return min(len(ROSTER), self._page_start() + PAGE_SIZE)

    def _visible_indices(self) -> list[int]:
        return list(range(self._page_start(), self._page_end()))

    def _is_visible_index(self, idx: int) -> bool:
        return self._page_start() <= idx < self._page_end()

    def _slot_of_index(self, idx: int) -> int:
        return idx - self._page_start()

    def _set_page(self, page: int, snap_unlocked: bool = True):
        if self.page_count <= 0:
            self.page = 0
            return

        self.page = max(0, min(page, self.page_count - 1))

        if snap_unlocked:
            start = self._page_start()
            end = self._page_end()

            for pid in range(2):
                if self.locked[pid]:
                    continue

                if not (start <= self.cursors[pid] < end):
                    self.cursors[pid] = start

        self._rebuild_icon_rects()

    def _next_page(self):
        self._set_page(self.page + 1)

    def _prev_page(self):
        self._set_page(self.page - 1)

    def _sync_page_to_cursor(self, pid: int):
        idx = self.cursors[pid]
        new_page = idx // PAGE_SIZE

        if new_page != self.page:
            self.page = new_page
            self._rebuild_icon_rects()

    # ── 이벤트 ──────────────────────────────────────────────────
    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if self._page_prev_rect.collidepoint(event.pos):
                    self._prev_page()
                    return

                if self._page_next_rect.collidepoint(event.pos):
                    self._next_page()
                    return

        if event.type == pygame.MOUSEMOTION:
            self._mouse = event.pos
            # 마우스 위치 기반으로 즉시 툴팁 갱신
            mx, my = self._mouse
            self._tooltip = None
            for (ci, sk_key), rect in self._icon_rects.items():
                if rect.collidepoint(mx, my):
                    self._tooltip = (ci, sk_key)
                    break
            return

        if event.type != pygame.KEYDOWN:
            return
        k = event.key

        if not self.locked[0]:
            if k == pygame.K_a:
                self.cursors[0] = (self.cursors[0] - 1) % len(ROSTER)
                self._sync_page_to_cursor(0)

            elif k == pygame.K_d:
                self.cursors[0] = (self.cursors[0] + 1) % len(ROSTER)
                self._sync_page_to_cursor(0)

            elif k in (pygame.K_f, pygame.K_RETURN):
                self.locked[0] = True
        else:
            if k == pygame.K_g:
                self.locked[0] = False

        if not self.locked[1]:
            if k == pygame.K_LEFT:
                self.cursors[1] = (self.cursors[1] - 1) % len(ROSTER)
                self._sync_page_to_cursor(1)

            elif k == pygame.K_RIGHT:
                self.cursors[1] = (self.cursors[1] + 1) % len(ROSTER)
                self._sync_page_to_cursor(1)

            elif k == pygame.K_l:
                self.locked[1] = True
        else:
            if k == pygame.K_SEMICOLON:
                self.locked[1] = False

        if all(self.locked) and not self.done:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                self.result = (ROSTER[self.cursors[0]], ROSTER[self.cursors[1]])
                self.done   = True
                self.transition.start()

    def update(self):
        self._t += 0.04
        self.transition.update()
        if self.done and self.transition.done:
            pass   # done 유지
        if not self._entered:
            self._enter_t = min(1.0, self._enter_t + 0.045)
            if self._enter_t >= 1.0:
                self._entered = True

    # ── draw ────────────────────────────────────────────────────
    def draw(self):
        self.screen.blit(self._bg,(0,0))
        for sx,sy,sr,sa in self._stars:
            fl = sa + math.sin(self._t*2+sx*0.01)*0.15
            c  = int(max(0,min(255,fl*255)))
            pygame.draw.circle(self.screen,(c,c,c),(sx,sy),int(sr))

        self._draw_title()

        for slot, char_idx in enumerate(self._visible_indices()):
            cls = ROSTER[char_idx]
            self._draw_card(slot, char_idx, cls)

        for pid in range(2):
            self._draw_cursor(pid)

        self._draw_page_arrows()
        self._draw_bottom_panels()
        self._draw_guide()

        # 툴팁은 맨 마지막 (다른 요소 위에)
        if self._tooltip is not None:
            self._draw_tooltip(*self._tooltip)

    def _draw_title(self):
        t = self.fnt_title.render("CHARACTER  SELECT", True, (255,255,255))
        self.screen.blit(t,(self.W//2 - t.get_width()//2, 20))
        pygame.draw.line(self.screen,(70,100,220),(self.W//2-170,62),(self.W//2+170,62),2)

    def _draw_page_arrows(self):
        if self.page_count <= 1:
            return

        mx, my = self._mouse

        def draw_arrow(rect, direction, enabled):
            hovered = rect.collidepoint(mx, my)
            base = (18, 22, 48)
            border = (90, 120, 220) if enabled else (55, 55, 75)

            if hovered and enabled:
                fill = (28, 36, 80)
            else:
                fill = base

            pygame.draw.rect(self.screen, fill, rect, border_radius=14)
            pygame.draw.rect(self.screen, border, rect, 2, border_radius=14)

            cx, cy = rect.center

            if direction == "left":
                pts = [
                    (cx + 10, cy - 22),
                    (cx - 12, cy),
                    (cx + 10, cy + 22),
                ]
            else:
                pts = [
                    (cx - 10, cy - 22),
                    (cx + 12, cy),
                    (cx - 10, cy + 22),
                ]

            col = (210, 225, 255) if enabled else (90, 90, 110)
            pygame.draw.polygon(self.screen, col, pts)

        draw_arrow(
            self._page_prev_rect,
            "left",
            self.page > 0,
        )

        draw_arrow(
            self._page_next_rect,
            "right",
            self.page < self.page_count - 1,
        )

        page_txt = self.fnt_sm.render(
            f"{self.page + 1} / {self.page_count}",
            True,
            (180, 190, 230),
        )

        self.screen.blit(
            page_txt,
            (self.W // 2 - page_txt.get_width() // 2, CARD_Y + CARD_H + 4),
        )

    def _card_rect(self, i) -> pygame.Rect:
        return pygame.Rect(self._x0 + i*(CARD_W+CARD_GAP), CARD_Y, CARD_W, CARD_H)

    # ── 카드 ────────────────────────────────────────────────────
    def _draw_card(self, slot_idx, char_idx, cls):
        r = self._card_rect(slot_idx)
        col = cls.PREVIEW_COLOR
        glw = tuple(min(255,c+80) for c in col)
        p1h = self.cursors[0]==char_idx
        p2h = self.cursors[1]==char_idx
        hov = p1h or p2h
        off = -int(abs(math.sin(self._t*2.2))*8) if hov else 0
        rx,ry = r.x, r.y+off

        # 배경
        card = pygame.Surface((CARD_W,CARD_H),pygame.SRCALPHA)
        for cy in range(CARD_H):
            a = int(30+(cy/CARD_H)*26)
            pygame.draw.line(card,(*col,a),(0,cy),(CARD_W,cy))
        pygame.draw.rect(card,(*glw,55 if hov else 22),(0,0,CARD_W,CARD_H),2,border_radius=14)
        self.screen.blit(card,(rx,ry))

        cur_y = ry + 10

        # 캐릭터 미리보기
        PREV_H = 116
        self._draw_preview(cls, rx+CARD_W//2, cur_y, PREV_H, col, glw)
        cur_y += PREV_H + 4

        # 이름
        nm = self.fnt_lg.render(cls.DISPLAY_NAME, True, (255,255,255))
        self.screen.blit(nm,(rx+CARD_W//2 - nm.get_width()//2, cur_y))
        cur_y += 22

        # 구분선
        pygame.draw.line(self.screen,(*glw,80),(rx+12,cur_y),(rx+CARD_W-12,cur_y),1)
        cur_y += 7

        # 스탯 바
        stats=[("SPD",min(1.0,cls.WALK_SPEED/8.5)),
               ("PWR",min(1.0,cls.ATTACK_DMG/18.0)),
               ("JMP",min(1.0,(abs(cls.JUMP_POWER)+(cls.MAX_JUMPS-2)*3)/22.0))]
        for lb,v in stats:
            self._draw_stat_bar(rx+12, cur_y, CARD_W-24, lb, v, col, glw)
            cur_y += 20

        cur_y += 6

        # 스킬 아이콘 4개 — 어느 플레이어가 선택 중인지 pid 전달
        _pid = 1 if p1h and not p2h else (2 if p2h and not p1h else None)
        self._draw_skill_icons(char_idx, cls, rx, cur_y, col, glw, pid=_pid)
        cur_y += 76

        # LOCKED 오버레이
        if (p1h and self.locked[0]) or (p2h and self.locked[1]):
            lo = pygame.Surface((CARD_W,CARD_H),pygame.SRCALPHA)
            pygame.draw.rect(lo,(*col,45),(0,0,CARD_W,CARD_H),border_radius=14)
            self.screen.blit(lo,(rx,ry))
            lt = self.fnt_md.render("LOCKED IN", True,(255,255,255))
            self.screen.blit(lt,(rx+CARD_W//2-lt.get_width()//2, ry+CARD_H-20))

    # ── 미리보기 ────────────────────────────────────────────────
    def _draw_preview(self, cls, cx, top_y, height, col, glw):
        cy  = top_y + height//2
        bob = int(math.sin(self._t*2.5)*3)
        th  = self._thumbs.get(cls.__name__)

        for rr,aa in [(52,20),(44,42)]:
            gs = pygame.Surface((rr*2,rr*2),pygame.SRCALPHA)
            pygame.draw.circle(gs,(*col,aa),(rr,rr),rr)
            self.screen.blit(gs,(cx-rr,cy-rr))

        if th is not None:
            tw,th2 = th.get_size()
            self.screen.blit(th,(cx-tw//2, top_y+bob))
            pygame.draw.circle(self.screen,glw,(cx,cy+bob//2),48,2)
        else:
            tc = cls.TRIM_COLOR
            pygame.draw.rect(self.screen,tc,(cx-13,cy+12+bob,10,13),border_radius=3)
            pygame.draw.rect(self.screen,tc,(cx+3, cy+12+bob,10,13),border_radius=3)
            pygame.draw.rect(self.screen,col,(cx-15,cy-5+bob, 30,19),border_radius=5)
            pygame.draw.rect(self.screen,tc, (cx-13,cy-3+bob, 7, 15),border_radius=2)
            pygame.draw.rect(self.screen,col,(cx-11,cy-25+bob,22,21),border_radius=8)
            pygame.draw.rect(self.screen,tc, (cx-9, cy-23+bob,18, 7),border_radius=4)
            pygame.draw.circle(self.screen,glw,(cx,cy),46,2)

    # ── 스탯 바 ─────────────────────────────────────────────────
    def _draw_stat_bar(self, x, y, w, label, ratio, col, glw):
        lb = self.fnt_xs.render(label, True,(170,170,210))
        self.screen.blit(lb,(x,y+2))
        bx,bw = x+30, w-34
        pygame.draw.rect(self.screen,(18,15,38),(bx,y+3,bw,9),border_radius=4)
        fw = int(bw*ratio)
        if fw>0:
            pygame.draw.rect(self.screen,col,(bx,y+3,fw,9),border_radius=4)
            pygame.draw.rect(self.screen,glw,(bx,y+3,fw,3),border_radius=4)
        pygame.draw.rect(self.screen,(70,60,120),(bx,y+3,bw,9),1,border_radius=4)

    # ── 스킬 아이콘 4개 ─────────────────────────────────────────
    def _draw_skill_icons(self, char_idx, cls, card_x, icon_y, col, glw, pid=None):
        n      = len(SKILL_SLOTS)
        ICON_W = 48
        ICON_H = 70
        pad    = (CARD_W - n*ICON_W) // (n+1)

        skills = self._get_skills(cls)

        for si, (sk_key, slot_name, p1_key, p2_key) in enumerate(SKILL_SLOTS):
            ix = card_x + pad + si*(ICON_W+pad)
            iy = icon_y
            skill = skills.get(sk_key)

            # ULT 슬롯은 금색 강조
            is_ult = (sk_key == "skill_R")
            border_col = (200,160,40,160) if is_ult else ((*glw,55) if skill else (50,50,70,55))

            # 박스
            pygame.draw.rect(self.screen,(30 if not is_ult else 40, 26,
                                          55 if is_ult else 50),(ix,iy,ICON_W,ICON_H),border_radius=6)
            bs = pygame.Surface((ICON_W,ICON_H),pygame.SRCALPHA)
            pygame.draw.rect(bs, border_col if isinstance(border_col,tuple) and len(border_col)==4
                             else (*border_col,55),
                             (0,0,ICON_W,ICON_H),1,border_radius=6)
            self.screen.blit(bs,(ix,iy))

            # 슬롯 라벨 (상단)
            lbl_col = (200,160,40) if is_ult else (glw if skill else (80,80,100))
            sl = self.fnt_xs.render(slot_name, True, lbl_col)
            self.screen.blit(sl,(ix+ICON_W//2-sl.get_width()//2, iy+3))

            if skill:
                # 스킬 아이콘 (가운데 26px)
                skill.draw_icon(self.screen, ix+(ICON_W-26)//2, iy+14, 26)

                # 쿨타임
                cd  = skill.cooldown/60 if skill.cooldown else 0
                cdt = self.fnt_xs.render(f"{cd:.1f}s", True,(180,180,220))
                self.screen.blit(cdt,(ix+ICON_W//2-cdt.get_width()//2, iy+43))

                # 키 힌트 — P1/P2 각자 키 표시
                if pid == 1:
                    hint_txt = p1_key
                    hint_col = (110, 170, 255)
                elif pid == 2:
                    hint_txt = p2_key
                    hint_col = (255, 130, 110)
                else:
                    # 두 플레이어 모두 선택 중이면 "P1/P2" 형태로
                    hint_txt = f"{p1_key}/{p2_key}"
                    hint_col = (150, 150, 180)
                kt = self.fnt_xs.render(hint_txt, True, hint_col)
                self.screen.blit(kt,(ix+ICON_W//2-kt.get_width()//2, iy+56))
            else:
                empty = self.fnt_xs.render("—", True,(60,60,80))
                self.screen.blit(empty,(ix+ICON_W//2-empty.get_width()//2, iy+30))
                # 빈 궁극기 슬롯 안내
                if is_ult:
                    na = self.fnt_xs.render("WIP", True,(120,100,40))
                    self.screen.blit(na,(ix+ICON_W//2-na.get_width()//2, iy+44))

            # 히트박스 갱신 (draw마다 갱신해서 off 애니메이션 반영)
            self._icon_rects[(char_idx, sk_key)] = pygame.Rect(ix-2, iy-14, ICON_W+4, ICON_H+14)

    # ── 스킬 딕셔너리 추출 ──────────────────────────────────────
    def _get_skills(self, cls) -> dict:
        try:
            dummy = object.__new__(cls)
            dummy.skills        = {}
            dummy.ATTACK_DMG    = cls.ATTACK_DMG
            dummy.ultimate_gauge = 0
            cls._init_skills(dummy)
            return dummy.skills
        except Exception:
            return {}

    # ── 커서 ────────────────────────────────────────────────────
    def _draw_cursor(self, pid):
        char_idx = self.cursors[pid]

        if not self._is_visible_index(char_idx):
            return

        slot_idx = self._slot_of_index(char_idx)

        r = self._card_rect(slot_idx)
        col = (110, 185, 255) if pid == 0 else (255, 130, 110)
        lbl = "P1" if pid == 0 else "P2"

        off = -int(abs(math.sin(self._t * 2.2)) * 8)
        rx, ry = r.x, r.y + off

        for bw, aa in [(5, 55), (2, 195)]:
            gs = pygame.Surface((CARD_W + 16, CARD_H + 16), pygame.SRCALPHA)
            pygame.draw.rect(
                gs,
                (*col, aa),
                (0, 0, CARD_W + 16, CARD_H + 16),
                bw,
                border_radius=16,
            )
            self.screen.blit(gs, (rx - 8, ry - 8))

        badge = pygame.Surface((38, 18), pygame.SRCALPHA)
        badge.fill((*col, 215))
        pygame.draw.rect(
            badge,
            (255, 255, 255, 45),
            badge.get_rect(),
            1,
            border_radius=4,
        )

        bt = self.fnt_xs.render(lbl, True, (255, 255, 255))
        badge.blit(bt, (19 - bt.get_width() // 2, 4))

        self.screen.blit(
            badge,
            (rx + (0 if pid == 0 else CARD_W - 38), ry - 22),
        )

        acx = rx + CARD_W // 2
        tip = ry - 28 - int(abs(math.sin(self._t * 3.5)) * 7)

        pygame.draw.polygon(
            self.screen,
            col,
            [
                (acx, tip),
                (acx - 8, tip + 12),
                (acx + 8, tip + 12),
            ],
        )
    # ── 하단 패널 ───────────────────────────────────────────────
    def _draw_bottom_panels(self):
        py  = CARD_Y + CARD_H + 12
        pw, ph = 210, 78

        for pid in range(2):
            idx = self.cursors[pid]
            cls = ROSTER[idx]
            col = cls.PREVIEW_COLOR
            glw = tuple(min(255,c+80) for c in col)
            pc  = (110,185,255) if pid==0 else (255,130,110)
            px  = 14 if pid==0 else self.W-pw-14

            panel = pygame.Surface((pw,ph),pygame.SRCALPHA)
            pygame.draw.rect(panel,(5,8,22,188),(0,0,pw,ph),border_radius=10)
            pygame.draw.rect(panel,(*pc,145),(0,0,4,ph),border_radius=10)
            pygame.draw.rect(panel,(*pc,45),(0,0,pw,ph),1,border_radius=10)
            self.screen.blit(panel,(px,py))

            nm = self.fnt_md.render(f"P{pid+1}  {cls.DISPLAY_NAME}", True, pc)
            self.screen.blit(nm,(px+10,py+7))

            for li,line in enumerate(cls.DESCRIPTION.split("\n")[:2]):
                lt = self.fnt_xs.render(line, True,(175,175,205))
                self.screen.blit(lt,(px+10,py+26+li*15))

            stat_txt = self.fnt_xs.render(
                f"Jump x{cls.MAX_JUMPS}   ATK {cls.ATTACK_DMG}%   SPD {cls.WALK_SPEED}",
                True, glw)
            self.screen.blit(stat_txt,(px+10,py+60))

    # ── 툴팁 ────────────────────────────────────────────────────
    def _draw_tooltip(self, char_idx: int, sk_key: str):
        cls   = ROSTER[char_idx]
        skill = self._get_skills(cls).get(sk_key)
        if skill is None:
            # 빈 슬롯 툴팁
            self._draw_empty_tooltip(sk_key)
            return

        TYPE_COL = {
            "beam":(80,160,255),"projectile":(255,200,60),
            "summon_zone":(220,80,80),"dash":(100,220,180),
            "teleport":(180,100,255),"enhance":(255,220,60),
            "ultimate":(255,160,40),
        }
        tc  = TYPE_COL.get(getattr(skill,"SKILL_TYPE",""), (150,150,180))
        desc_lines = _wrap(getattr(skill,"DESCRIPTION",""), self.fnt_xs, 210)

        rows = [
            (skill.name,                           self.fnt_md, (255,255,255)),
            (getattr(skill,"SKILL_TYPE","—").upper(),self.fnt_xs, tc),
            ("",None,None),   # 구분선
            (f"Damage   {skill.damage}%",          self.fnt_xs, (160,220,160)),
            (f"Cooldown {skill.cooldown/60:.1f}s" if skill.cooldown else "Cooldown —",
                                                    self.fnt_xs, (200,200,160)),
            ("",None,None),
            *[(l, self.fnt_xs, (190,190,215)) for l in desc_lines],
        ]

        TW  = 230
        TH  = sum(16 if r[1] else 8 for r in rows) + 16
        mx,my = self._mouse
        tx = min(mx+14, self.W-TW-8)
        ty = min(my+14, self.H-TH-8)

        tip = pygame.Surface((TW,TH),pygame.SRCALPHA)
        pygame.draw.rect(tip,(6,8,24,240),(0,0,TW,TH),border_radius=10)
        pygame.draw.rect(tip,(*tc,160),(0,0,TW,TH),1,border_radius=10)

        # 스킬 아이콘 (우상단)
        skill.draw_icon(tip, TW-36, 4, 32)

        cy2 = 8
        for text,fnt,color in rows:
            if fnt is None:
                pygame.draw.line(tip,(60,70,120),(10,cy2+3),(TW-10,cy2+3),1)
                cy2 += 8
            else:
                sf = fnt.render(text,True,color)
                tip.blit(sf,(10,cy2))
                cy2 += 16

        self.screen.blit(tip,(tx,ty))

    def _draw_empty_tooltip(self, sk_key: str):
        """빈 슬롯(주로 ULT) 툴팁."""
        TW,TH = 200,60
        mx,my = self._mouse
        tx = min(mx+14, self.W-TW-8)
        ty = min(my+14, self.H-TH-8)
        tip = pygame.Surface((TW,TH),pygame.SRCALPHA)
        pygame.draw.rect(tip,(6,8,24,230),(0,0,TW,TH),border_radius=10)
        pygame.draw.rect(tip,(200,160,40,140),(0,0,TW,TH),1,border_radius=10)
        t1 = self.fnt_md.render("Ultimate Skill", True,(200,160,40))
        t2 = self.fnt_xs.render("Not yet implemented.", True,(150,140,120))
        t3 = self.fnt_xs.render("Coming in a future update.", True,(120,120,100))
        tip.blit(t1,(10,8)); tip.blit(t2,(10,28)); tip.blit(t3,(10,42))
        self.screen.blit(tip,(tx,ty))

    # ── 가이드 ──────────────────────────────────────────────────
    def _draw_guide(self):
        rows = [
            ("P1:  A/D Move   F Select   G Cancel", (110, 185, 255)),
            ("P2:  ←/→ Move   L Select   ; Cancel", (255, 130, 110)),
            ("Mouse: click side arrows to change character page", (170, 170, 210)),
        ]
        for i, (txt, col) in enumerate(rows):
            sf = self.fnt_xs.render(txt, True, col)
            self.screen.blit(
                sf,
                (self.W // 2 - sf.get_width() // 2, self.H - 58 + i * 16),
            )
        if all(self.locked):
            fc  = (255,int(200+math.sin(self._t*6)*55),80)
            go  = self.fnt_lg.render("PRESS  ENTER  to continue",True,fc)
            self.screen.blit(go,(self.W//2-go.get_width()//2, self.H-76))
