"""
Story Stage Select — 스토리 스테이지 슬라이더 선택창

구성:
  - 수평 슬라이더 (챕터 노드)
  - 선택된 챕터 상세 패널 (보스명, 맵, 배경 미리보기, 설명)
  - 클리어 여부 / 잠금 표시
  - 진행도 바
"""
import pygame
import math
import random
import os

from systems.story_save   import StorySave
from systems.story_loader import StoryLoader
from systems.stage_loader import StageLoader


class StoryStageSelect:
    """
    result: 선택된 chapter dict | None
    done:   True이면 확정
    """

    def __init__(self, screen: pygame.Surface, save: StorySave, loader: StoryLoader):
        self.screen = screen
        self.W = screen.get_width()
        self.H = screen.get_height()
        self.save   = save
        self.loader = loader

        self.fnt_title = pygame.font.SysFont("Arial", 34, bold=True)
        self.fnt_lg    = pygame.font.SysFont("Arial", 20, bold=True)
        self.fnt_md    = pygame.font.SysFont("Arial", 14, bold=True)
        self.fnt_sm    = pygame.font.SysFont("Arial", 12, bold=True)
        self.fnt_xs    = pygame.font.SysFont("Arial", 11)

        self.cursor = self._default_cursor()
        self.done   = False
        self.result = None
        self._t     = 0.0

        # 슬라이더 애니메이션용 실제 위치 (부드러운 이동)
        self._slider_x = float(self.cursor)

        rng = random.Random(33)
        self._stars = [(rng.randint(0,self.W), rng.randint(0,self.H),
                        rng.uniform(0.3,1.5), rng.uniform(0.15,0.65)) for _ in range(120)]
        self._bg = self._bake_bg()

        # 챕터 배경 썸네일 캐시
        THUMB_W, THUMB_H = 340, 180
        self._thumbs: dict[int, pygame.Surface|None] = {}
        for ch in self.loader.chapters:
            path  = ch.get("bg_image","")
            thumb = None
            if path and os.path.exists(path):
                try:
                    img   = pygame.image.load(path).convert()
                    thumb = pygame.transform.smoothscale(img,(THUMB_W,THUMB_H))
                except Exception: pass
            self._thumbs[ch["id"]] = thumb

        # 플랫폼 데이터 캐시 (미니맵용)
        self._platforms: dict[int, list] = {}
        for ch in self.loader.chapters:
            try:
                data = StageLoader(ch["stage_json"]).load()
                self._platforms[ch["id"]] = data.get("platforms",[])
            except Exception:
                self._platforms[ch["id"]] = []

    def _default_cursor(self) -> int:
        """저장 데이터 기준 가장 마지막 미클리어 챕터로 초기 커서 설정."""
        for i, ch in enumerate(self.loader.chapters):
            if not self.save.is_cleared(ch["id"]):
                return i
        return len(self.loader.chapters) - 1

    def _bake_bg(self) -> pygame.Surface:
        sf = pygame.Surface((self.W, self.H))
        for y in range(self.H):
            t = y/self.H
            pygame.draw.line(sf,(int(5+t*10),int(6+t*10),int(16+t*22)),(0,y),(self.W,y))
        return sf

    # ── 이벤트 ──────────────────────────────────────────────────
    def handle_event(self, event: pygame.event.Event):
        if event.type != pygame.KEYDOWN:
            return
        k = event.key
        n = len(self.loader.chapters)

        if k in (pygame.K_a, pygame.K_LEFT):
            self.cursor = max(0, self.cursor - 1)
        elif k in (pygame.K_d, pygame.K_RIGHT):
            self.cursor = min(n-1, self.cursor + 1)

        elif k in (pygame.K_RETURN, pygame.K_f):
            ch = self.loader.chapters[self.cursor]
            if self.save.is_unlocked(ch):
                self.result = ch
                self.done   = True

        elif k == pygame.K_ESCAPE:
            self.result = None
            self.done   = True

    def update(self):
        self._t += 0.03
        # 슬라이더 부드러운 이동
        self._slider_x += (self.cursor - self._slider_x) * 0.18

    # ── draw ────────────────────────────────────────────────────
    def draw(self):
        self.screen.blit(self._bg,(0,0))
        for sx,sy,sr,sa in self._stars:
            fl = sa + math.sin(self._t*2+sx*0.01)*0.16
            c  = int(max(0,min(255,fl*255)))
            pygame.draw.circle(self.screen,(c,c,c),(sx,sy),int(sr))

        # 선택 챕터 테마 컬러 워시
        ch = self.loader.chapters[self.cursor]
        col = ch.get("theme_color",[60,80,180])
        wash = pygame.Surface((self.W,self.H),pygame.SRCALPHA)
        for y in range(self.H):
            a = int(14*(1-y/self.H))
            pygame.draw.line(wash,(*col,a),(0,y),(self.W,y))
        self.screen.blit(wash,(0,0))

        self._draw_title()
        self._draw_progress_bar()
        self._draw_slider()
        self._draw_detail_panel()
        self._draw_guide()

    # ── 타이틀 ──────────────────────────────────────────────────
    def _draw_title(self):
        t = self.fnt_title.render("SELECT  CHAPTER", True, (255,255,255))
        self.screen.blit(t,(self.W//2-t.get_width()//2, 18))
        pygame.draw.line(self.screen,(70,100,220),
                         (self.W//2-160,58),(self.W//2+160,58),1)

    # ── 전체 진행도 바 ───────────────────────────────────────────
    def _draw_progress_bar(self):
        total   = max(1, self.loader.total)
        cleared = self.save.cleared_count()
        bx,by   = 40, 70
        bw      = self.W - 80

        pygame.draw.rect(self.screen,(16,16,32),(bx,by,bw,8),border_radius=4)
        fw = int(bw*(cleared/total))
        if fw>0:
            pygame.draw.rect(self.screen,(60,120,255),(bx,by,fw,8),border_radius=4)
            pygame.draw.rect(self.screen,(120,180,255),(bx,by,fw,3),border_radius=4)
        pygame.draw.rect(self.screen,(50,70,140),(bx,by,bw,8),1,border_radius=4)

        pt = self.fnt_xs.render(f"Progress  {cleared}/{total}", True,(130,150,200))
        self.screen.blit(pt,(bx,by-16))

    # ── 슬라이더 ────────────────────────────────────────────────
    def _draw_slider(self):
        """
        챕터 노드들을 수평으로 배치하는 슬라이더.
        선택된 노드는 확대되고 위로 살짝 올라옴.
        """
        n      = len(self.loader.chapters)
        SLIDER_Y = 178
        NODE_R   = 28     # 기본 노드 반지름
        SEL_R    = 38     # 선택 노드 반지름

        # 노드 간격 계산
        margin  = 100
        spacing = (self.W - margin*2) / max(1, n-1)

        # 연결선 먼저
        for i in range(n-1):
            x1 = int(margin + i * spacing)
            x2 = int(margin + (i+1) * spacing)
            ch1 = self.loader.chapters[i]
            cleared1 = self.save.is_cleared(ch1["id"])
            line_col = (60,120,255) if cleared1 else (40,45,65)
            pygame.draw.line(self.screen, line_col, (x1,SLIDER_Y),(x2,SLIDER_Y), 3)

        # 노드
        for i,ch in enumerate(self.loader.chapters):
            node_x   = int(margin + i * spacing)
            is_sel   = (i == self.cursor)
            cleared  = self.save.is_cleared(ch["id"])
            unlocked = self.save.is_unlocked(ch)
            col      = ch.get("theme_color",[60,80,180])
            glw      = tuple(min(255,c+80) for c in col)

            r = SEL_R if is_sel else NODE_R

            # 선택 노드 위로 떠오름
            bob_off = -int(abs(math.sin(self._t*2.5))*8) if is_sel else 0
            ny      = SLIDER_Y + bob_off

            # 글로우 (선택된 노드)
            if is_sel:
                gr = pygame.Surface((r*4,r*4),pygame.SRCALPHA)
                pygame.draw.circle(gr,(*glw,50),(r*2,r*2),r*2)
                self.screen.blit(gr,(node_x-r*2, ny-r*2))

            # 노드 원
            if not unlocked:
                pygame.draw.circle(self.screen,(30,30,40),(node_x,ny),r)
                pygame.draw.circle(self.screen,(60,60,75),(node_x,ny),r,2)
            elif cleared:
                pygame.draw.circle(self.screen,col,(node_x,ny),r)
                pygame.draw.circle(self.screen,glw,(node_x,ny),r,2)
            else:
                pygame.draw.circle(self.screen,(35,35,55),(node_x,ny),r)
                pygame.draw.circle(self.screen,(*col,180),(node_x,ny),r,2)

            # 노드 아이콘
            if not unlocked:
                lock = self.fnt_sm.render("🔒",True,(80,80,100))
                self.screen.blit(lock,(node_x-lock.get_width()//2,
                                       ny-lock.get_height()//2))
            elif cleared:
                check = self.fnt_lg.render("✔",True,(255,255,255))
                self.screen.blit(check,(node_x-check.get_width()//2,
                                        ny-check.get_height()//2))
            else:
                num = self.fnt_lg.render(str(ch["id"]),True,
                    (255,255,255) if is_sel else (*glw,))
                self.screen.blit(num,(node_x-num.get_width()//2,
                                     ny-num.get_height()//2))

            # 챕터 타이틀 (노드 아래)
            title_sf = self.fnt_xs.render(ch["title"], True,
                (255,255,255) if is_sel else (150,150,170))
            self.screen.blit(title_sf,(node_x-title_sf.get_width()//2, ny+r+6))

    # ── 상세 패널 ───────────────────────────────────────────────
    def _draw_detail_panel(self):
        ch      = self.loader.chapters[self.cursor]
        col     = ch.get("theme_color",[60,80,180])
        glw     = tuple(min(255,c+80) for c in col)
        cleared = self.save.is_cleared(ch["id"])
        locked  = not self.save.is_unlocked(ch)
        thumb   = self._thumbs.get(ch["id"])
        plats   = self._platforms.get(ch["id"],[])

        # 패널 배경
        PW, PH = self.W - 80, 280
        px, py = 40, 235

        panel = pygame.Surface((PW,PH),pygame.SRCALPHA)
        pygame.draw.rect(panel,(4,6,18,210),(0,0,PW,PH),border_radius=12)
        pygame.draw.rect(panel,(*col,70),(0,0,PW,PH),1,border_radius=12)
        self.screen.blit(panel,(px,py))

        # ── 왼쪽: 배경 썸네일 or 미니맵 ──
        TPW, TPH = 340, 180
        tx, ty   = px+12, py+12

        if thumb:
            self.screen.blit(thumb,(tx,ty))
            # 플랫폼 오버레이
            self._draw_minimap_overlay(plats, ch, tx, ty, TPW, TPH, col, glw, alpha=160)
            # 이미지 테두리
            pygame.draw.rect(self.screen,(*glw,100),(tx,ty,TPW,TPH),1,border_radius=6)
        else:
            # 미니맵만
            bg = pygame.Surface((TPW,TPH),pygame.SRCALPHA)
            pygame.draw.rect(bg,(8,10,24,200),(0,0,TPW,TPH),border_radius=6)
            pygame.draw.rect(bg,(*glw,60),(0,0,TPW,TPH),1,border_radius=6)
            self.screen.blit(bg,(tx,ty))
            self._draw_minimap_overlay(plats, ch, tx, ty, TPW, TPH, col, glw, alpha=255)

        # 클리어/잠금 배지
        if cleared:
            badge = self.fnt_sm.render(" CLEARED ✔ ", True,(255,255,255))
            bb = pygame.Surface((badge.get_width()+6,20),pygame.SRCALPHA)
            pygame.draw.rect(bb,(30,100,60,220),bb.get_rect(),border_radius=5)
            bb.blit(badge,(3,2))
            self.screen.blit(bb,(tx+4,ty+4))
        elif locked:
            badge = self.fnt_sm.render(" LOCKED 🔒 ", True,(200,200,220))
            bb = pygame.Surface((badge.get_width()+6,20),pygame.SRCALPHA)
            pygame.draw.rect(bb,(60,40,80,220),bb.get_rect(),border_radius=5)
            bb.blit(badge,(3,2))
            self.screen.blit(bb,(tx+4,ty+4))

        # ── 오른쪽: 텍스트 정보 ──
        ix = tx + TPW + 20
        iy = py + 14

        # 챕터 타이틀
        t1 = self.fnt_lg.render(ch["title"], True, glw)
        self.screen.blit(t1,(ix,iy))
        iy += 26

        # 부제
        t2 = self.fnt_md.render(ch.get("subtitle",""), True, (220,220,240))
        self.screen.blit(t2,(ix,iy))
        iy += 22

        pygame.draw.line(self.screen,(*glw,80),(ix,iy),(ix+PW-TPW-50,iy),1)
        iy += 10

        # 설명
        for line in ch.get("description","").split("\n")[:3]:
            lt = self.fnt_sm.render(line, True,(175,175,205))
            self.screen.blit(lt,(ix,iy))
            iy += 17

        iy += 6

        # 보스 정보
        boss_lbl = self.fnt_sm.render("BOSS", True, glw)
        boss_val = self.fnt_md.render(ch.get("boss_name","???"), True,(255,200,200))
        self.screen.blit(boss_lbl,(ix,iy))
        self.screen.blit(boss_val,(ix+48,iy))
        iy += 20

        # 보스 스톡
        stk_lbl = self.fnt_sm.render("STOCKS", True, glw)
        stk_val = self.fnt_md.render(str(ch.get("boss_stocks",3)), True,(255,220,160))
        self.screen.blit(stk_lbl,(ix,iy))
        self.screen.blit(stk_val,(ix+58,iy))
        iy += 20

        # 플레이 횟수
        pc = self.save.play_count(ch["id"])
        if pc > 0:
            pc_txt = self.fnt_sm.render(f"Attempts: {pc}", True,(140,140,160))
            self.screen.blit(pc_txt,(ix,iy))

        # 잠금 조건 표시
        if locked:
            cond = ch.get("unlock_condition",{})
            req  = cond.get("clear_chapter")
            if req:
                lock_txt = self.fnt_sm.render(
                    f"Clear Chapter {req} to unlock", True,(180,120,120))
                self.screen.blit(lock_txt,(ix, py+PH-30))

        # 확정 버튼 힌트
        if not locked:
            hint_col = (255,220,80) if not cleared else (100,220,100)
            hint_txt = "ENTER to challenge" if not cleared else "ENTER to replay"
            ht = self.fnt_md.render(hint_txt, True, hint_col)
            self.screen.blit(ht,(px + PW - ht.get_width() - 14, py+PH-26))

    def _draw_minimap_overlay(self, plats, ch, px, py, PW, PH, col, glw, alpha=255):
        if not plats:
            return
        min_x = min(p.x for p in plats); max_x = max(p.x+p.w for p in plats)
        min_y = min(p.y for p in plats); max_y = max(p.y+p.h for p in plats)
        sw = max(max_x-min_x,1); sh = max(max_y-min_y,1)
        mg = 12
        scale = min((PW-mg*2)/sw,(PH-mg*2)/sh)*0.88

        for p in plats:
            sx = px+mg+int((p.x-min_x)*scale)
            sy = py+mg+int((p.y-min_y)*scale)
            pw_s = max(4,int(p.w*scale)); ph_s = max(3,int(p.h*scale))
            is_main = p.h>30
            bc = tuple(min(255,c+(20 if is_main else 0)) for c in col)
            tc = tuple(min(255,c+80) for c in col)
            ps2 = pygame.Surface((pw_s,ph_s),pygame.SRCALPHA)
            pygame.draw.rect(ps2,(*bc,alpha),(0,0,pw_s,ph_s),border_radius=3)
            pygame.draw.rect(ps2,(*tc,alpha),(0,0,pw_s,3),border_radius=3)
            self.screen.blit(ps2,(sx,sy))

        # 스폰 위치
        sp1 = ch.get("player_spawn",[220,340]); sp2 = ch.get("boss_spawn",[900,340])
        for sp_xy,sp_col in [(sp1,(110,185,255)),(sp2,(255,130,110))]:
            sx = px+mg+int((sp_xy[0]-min_x)*scale)
            sy = py+mg+int((sp_xy[1]-min_y)*scale)
            if px<=sx<=px+PW and py<=sy<=py+PH:
                dot = pygame.Surface((14,14),pygame.SRCALPHA)
                pygame.draw.circle(dot,(*sp_col,alpha),(7,7),5)
                pygame.draw.circle(dot,(255,255,255,alpha),(7,7),5,1)
                self.screen.blit(dot,(sx-7,sy-7))

    # ── 가이드 ──────────────────────────────────────────────────
    def _draw_guide(self):
        rows = ["A / D  or  ← / →   select chapter",
                "ENTER  confirm   |   ESC  back"]
        for i,txt in enumerate(rows):
            sf = self.fnt_xs.render(txt, True,(100,100,130))
            self.screen.blit(sf,(self.W//2-sf.get_width()//2,self.H-42+i*18))
