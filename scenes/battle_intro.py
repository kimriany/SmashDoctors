"""
BattleIntro — 전투 시작 전 연출

흐름:
  1. 배경 암전 + 스테이지명 플래시
  2. VS 화면 (두 캐릭터 이름 + 색상)
  3. 3 → 2 → 1 → FIGHT! 카운트다운
  4. done = True → 전투 시작

done 되기 전까지 BattleSession.draw()는 호출하지 않음
"""
import pygame
import math
import os
from systems.font_manager import font


COUNTDOWN_FRAMES = 42   # 숫자 하나당 프레임
FIGHT_FRAMES     = 38


class BattleIntro:
    def __init__(self,
                 screen: pygame.Surface,
                 stage_name: str,
                 stage_bg: pygame.Surface | None,
                 p1_name: str, p1_color: tuple,
                 p2_name: str, p2_color: tuple):
        self.screen = screen
        self.W = screen.get_width()
        self.H = screen.get_height()

        self.stage_name = stage_name
        self.stage_bg   = stage_bg
        self.p1_name    = p1_name
        self.p1_color   = p1_color
        self.p2_name    = p2_name
        self.p2_color   = p2_color

        self.fnt_vs      = font(90, bold=True)
        self.fnt_name    = font(32, bold=True)
        self.fnt_stage   = font(22, bold=True)
        self.fnt_count   = font(110, bold=True)
        self.fnt_fight   = font(80, bold=True)
        self.fnt_sm      = font(14)

        self._frame = 0
        self.done   = False

        # 전체 길이: 암전(30) + VS화면(80) + 3(42) + 2(42) + 1(42) + FIGHT(38)
        self._phase_ends = [30, 110, 152, 194, 236, 274]

    @property
    def _phase(self) -> int:
        for i,end in enumerate(self._phase_ends):
            if self._frame < end:
                return i
        return len(self._phase_ends)

    def update(self):
        if self.done:
            return
        self._frame += 1
        if self._frame >= self._phase_ends[-1]:
            self.done = True

    def handle_event(self, event: pygame.event.Event):
        # 스킵 (ENTER)
        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            self.done = True

    def draw(self):
        ph = self._phase
        f  = self._frame
        W, H = self.W, self.H

        # ── Phase 0: 암전 ──
        if ph == 0:
            prog = f / self._phase_ends[0]
            self.screen.fill((0,0,0))
            if prog > 0.3 and self.stage_bg:
                a = int(255 * min(1.0, (prog-0.3)/0.4))
                bg = self.stage_bg.copy()
                bg.set_alpha(a)
                self.screen.blit(bg,(0,0))
            ov = pygame.Surface((W,H),pygame.SRCALPHA)
            ov.fill((0,0,0,int(200*(1-prog*0.5))))
            self.screen.blit(ov,(0,0))

            # 스테이지명
            if prog > 0.5:
                a = int(255*min(1.0,(prog-0.5)/0.3))
                sf = self.fnt_stage.render(self.stage_name,True,(200,210,255))
                sf.set_alpha(a)
                self.screen.blit(sf,(W//2-sf.get_width()//2, H//2-14))
            return

        # 배경 (이후 모든 페이즈)
        if self.stage_bg:
            self.screen.blit(self.stage_bg,(0,0))
        else:
            self.screen.fill((8,10,22))
        ov = pygame.Surface((W,H),pygame.SRCALPHA)
        ov.fill((0,0,0,160))
        self.screen.blit(ov,(0,0))

        # ── Phase 1: VS 화면 ──
        if ph == 1:
            rel = f - self._phase_ends[0]
            dur = self._phase_ends[1] - self._phase_ends[0]
            p   = min(1.0, rel / 20)   # 0→1 in 20f

            # P1 이름 (왼쪽에서 슬라이드인)
            p1x = int((1-p) * (-W//3) + p * (W//4 - 150))
            p1_sf = self.fnt_name.render(self.p1_name, True, self.p1_color)
            self.screen.blit(p1_sf,(p1x, H//2 - 80))

            # P2 이름 (오른쪽에서 슬라이드인)
            p2x = int((1-p) * (W + W//3) + p * (W*3//4 + 10))
            p2_sf = self.fnt_name.render(self.p2_name, True, self.p2_color)
            self.screen.blit(p2_sf,(p2x, H//2 - 80))

            # VS
            vs_alpha = int(255 * min(1.0, rel/25))
            vs_scale = 0.6 + 0.4 * min(1.0, rel/25)
            vs_sf    = self.fnt_vs.render("VS", True,(255,255,255))
            vs_w     = int(vs_sf.get_width() * vs_scale)
            vs_h     = int(vs_sf.get_height() * vs_scale)
            vs_sc    = pygame.transform.smoothscale(vs_sf,(vs_w,vs_h))
            vs_sc.set_alpha(vs_alpha)
            self.screen.blit(vs_sc,(W//2-vs_w//2, H//2-vs_h//2))

            # 가로 구분선
            if rel > 20:
                la = int(255*min(1.0,(rel-20)/15))
                lw = int((W-80)*min(1.0,(rel-20)/20))
                ls = pygame.Surface((lw,2),pygame.SRCALPHA)
                ls.fill((255,255,255,la//3))
                self.screen.blit(ls,(W//2-lw//2, H//2+50))

            # P1 컬러 바 (왼쪽)
            bw = int(W//2 * min(1.0,(rel)/30))
            if bw>0:
                bs = pygame.Surface((bw,4),pygame.SRCALPHA)
                bs.fill((*self.p1_color,180))
                self.screen.blit(bs,(0, H//2+55))
            # P2 컬러 바 (오른쪽)
            if bw>0:
                bs2 = pygame.Surface((bw,4),pygame.SRCALPHA)
                bs2.fill((*self.p2_color,180))
                self.screen.blit(bs2,(W-bw, H//2+55))
            return

        # ── Phase 2~4: 카운트다운 ──
        if ph in (2,3,4):
            count_num = 4 - ph   # 3, 2, 1
            phase_start = self._phase_ends[ph-1]
            rel  = f - phase_start
            prog = rel / COUNTDOWN_FRAMES

            # 펄스 스케일 (나타났다 사라짐)
            if prog < 0.25:
                scale = 0.5 + 1.5 * (prog/0.25)
                alpha = int(255 * (prog/0.25))
            elif prog < 0.7:
                scale = 2.0 - 0.4 * ((prog-0.25)/0.45)
                alpha = 255
            else:
                scale = 1.6 - 0.6 * ((prog-0.7)/0.3)
                alpha = int(255 * (1-(prog-0.7)/0.3))

            col = [(80,150,255),(80,220,150),(255,160,60)][count_num-1]
            sf  = self.fnt_count.render(str(count_num),True,col)
            w   = int(sf.get_width()*scale)
            h   = int(sf.get_height()*scale)
            sc  = pygame.transform.smoothscale(sf,(max(1,w),max(1,h)))
            sc.set_alpha(int(alpha))

            # 글로우
            gw = w+40; gh = h+40
            gs = pygame.Surface((gw,gh),pygame.SRCALPHA)
            pygame.draw.ellipse(gs,(*col,int(60*alpha/255)),(0,0,gw,gh))
            self.screen.blit(gs,(W//2-gw//2, H//2-gh//2))
            self.screen.blit(sc,(W//2-w//2, H//2-h//2))
            return

        # ── Phase 5: FIGHT! ──
        if ph == 5:
            phase_start = self._phase_ends[4]
            rel  = f - phase_start
            prog = rel / FIGHT_FRAMES

            if prog < 0.3:
                scale = 0.3 + 2.0*(prog/0.3)
                alpha = int(255*(prog/0.3))
            elif prog < 0.7:
                scale = 2.3 - 0.3*((prog-0.3)/0.4)
                alpha = 255
            else:
                scale = 2.0
                alpha = int(255*(1-(prog-0.7)/0.3))

            col = (255,220,60)
            sf  = self.fnt_fight.render("FIGHT!", True, col)
            w   = int(sf.get_width()*scale)
            h   = int(sf.get_height()*scale)
            sc  = pygame.transform.smoothscale(sf,(max(1,w),max(1,h)))
            sc.set_alpha(int(alpha))

            gs = pygame.Surface((w+60,h+60),pygame.SRCALPHA)
            pygame.draw.ellipse(gs,(*col,int(50*alpha/255)),gs.get_rect())
            self.screen.blit(gs,(W//2-(w+60)//2, H//2-(h+60)//2))
            self.screen.blit(sc,(W//2-w//2, H//2-h//2))

            # 진동선
            for j in range(6):
                llen = int((W*0.6) * (1 - prog) * (j%2==0 and 1 or 0.6))
                la   = int(120*(1-prog))
                if llen>0:
                    pygame.draw.line(self.screen,(*col,la),
                        (W//2-llen//2, H//2 - 60 + j*22),
                        (W//2+llen//2, H//2 - 60 + j*22),1)

        # 스킵 힌트
        hint = self.fnt_sm.render("ENTER to skip",True,(80,85,110))
        self.screen.blit(hint,(W-hint.get_width()-16,H-28))
