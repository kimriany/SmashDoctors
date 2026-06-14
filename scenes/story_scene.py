from systems.font_manager import font
"""
StoryScene — 비주얼 노벨 엔진

지원 커맨드:
  bg          배경 이미지 변경 (fade / flash / fade_black / white_flash)
  show_char   캐릭터 표시 (slot: left/right)
  hide_char   캐릭터 숨김
  dialog      대사 출력 (speaker + text, 타이핑 효과)
  choice      선택지 (양자택일)
  label       goto 목적지 마커
  pause       n프레임 대기
  shake       화면 흔들기
  sound       BGM/SFX (파일 없으면 무시)
  battle_start  전투 시작 트리거
  ending      엔딩 트리거
  end         씬 종료

result:
  "battle"   → game.py에서 전투 시작
  "battle_2" → 2번째 전투
  "end"      → 다음 씬으로
  "ending_null" / "ending_eternity" / "ending_normal"
"""
import pygame
import json
import os
import math


# ── 타이핑 속도 ─────────────────────────────────────────────
CHAR_PER_FRAME = 1   # 프레임당 출력 글자 수


def _load_img(path, size=None) -> pygame.Surface | None:
    if not path or not os.path.exists(path):
        return None
    try:
        img = pygame.image.load(path).convert_alpha()
        if size:
            img = pygame.transform.smoothscale(img, size)
        return img
    except Exception as e:
        print(f"[StoryScene] 이미지 로드 실패: {path} / {e}")
        return None


class StoryScene:
    def __init__(self, screen: pygame.Surface, script_path: str):
        self.screen = screen
        self.script_path = script_path
        self.W = screen.get_width()
        self.H = screen.get_height()

        # 폰트
        self.fnt_speaker = font(20, bold=True)
        self.fnt_dialog  = font(24)
        self.fnt_choice  = font(19, bold=True)
        self.fnt_system  = font(16, bold=True)
        self.fnt_sm      = font(13)

        # 스크립트 로드
        self.script_data = {}
        self.commands    = []
        self._load_script(script_path)

        # 실행 상태
        self._idx         = 0        # 현재 커맨드 인덱스
        self._waiting     = False    # 클릭 대기 중
        self._pause_timer = 0
        self._labels: dict[str, int] = {}  # label id → idx

        # 타이핑
        self._full_text   = ""
        self._shown_chars = 0
        self._typing      = False
        self._speaker     = ""
        self._speaker_slot = None  # "left" / "right" / None

        # 선택지
        self._choices: list[dict] = []
        self._choice_cursor = 0
        self._in_choice     = False

        # 비주얼
        self._bg:       pygame.Surface | None = None
        self._bg_next:  pygame.Surface | None = None
        self._chars: dict[str, pygame.Surface | None] = {"left": None, "right": None}
        self._character_db = self._build_character_db()
        self._transition      = None    # "fade" / "flash" / "fade_black" / "white_flash"
        self._trans_progress  = 0.0
        self._shake_timer     = 0
        self._shake_x         = 0
        # 타이틀 카드
        self._title_card = None
        self._title_timer = 0
        self._center_image = None

        # 결과
        self.done   = False
        self.result = None   # "battle" / "battle_2" / "end" / "ending_*"

        # 레이블 인덱스 미리 빌드
        self._build_labels()
        # 첫 커맨드 실행
        self._run_next()

        self._ideology_timer = 0
        self._ideology_text = ""

    # ── 스크립트 로드 ───────────────────────────────────────────
    def _build_character_db(self) -> dict[str, dict[str, str]]:
        protagonist_slot = "right" if os.path.basename(self.script_path) == "stage_00.json" else "left"
        return {
            "Hora": {"slot": protagonist_slot, "image": "assets/images/story/charmain.png"},
            "주인공": {"slot": "left", "image": "assets/images/story/charmain.png"},
            "미래의 주인공": {"slot": "right", "image": "assets/images/story/charmain.png"},
            "거울 속 주인공": {"slot": "right", "image": "assets/images/story/charmain.png"},

            "과학자 A": {"slot": "left", "image": "assets/images/story/question.png"},
            "과학자 B": {"slot": "left", "image": "assets/images/story/question.png"},
            "RO2T": {"slot": "right", "image": "assets/images/story/RO2T.png"},
            "???": {"slot": "right", "image": "assets/images/story/question.png"},

            "크릭": {"slot": "right", "image": "assets/images/story/Crick.png"},
            "크릭의 잔상": {"slot": "right", "image": "assets/images/story/Crick.png"},
            "다윈": {"slot": "right", "image": "assets/images/story/Darwin.png"},
            "다윈의 잔상": {"slot": "right", "image": "assets/images/story/Darwin.png"},
            "퀴리": {"slot": "right", "image": "assets/images/story/Curie.png"},
            "퀴리의 잔상": {"slot": "right", "image": "assets/images/story/Curie.png"},
            "슈뢰딩거": {"slot": "right", "image": "assets/images/story/Schrödinger.png"},
            "슈뢰딩거의 잔상": {"slot": "right", "image": "assets/images/story/Schrödinger.png"},
            "뉴턴": {"slot": "right", "image": "assets/images/story/Newton.png"},
            "아인슈타인": {"slot": "right", "image": "assets/images/story/Einstein.png"},
            "호킹": {"slot": "right", "image": "assets/images/story/Hoking.png"},
        }

    def _load_script(self, path: str):
        key = "script_pre_battle"
        if not os.path.exists(path):
            print(f"[StoryScene] 스크립트 없음: {path}")
            self.commands = [{"cmd": "end"}]
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                self.script_data = json.load(f)
            # pre_battle 우선, 없으면 script
            for k in ("script_pre_battle", "script"):
                if k in self.script_data:
                    self.commands = self.script_data[k]
                    return
            self.commands = [{"cmd": "end"}]
        except Exception as e:
            print(f"[StoryScene] 스크립트 로드 실패: {e}")
            self.commands = [{"cmd": "end"}]

    def load_post_battle(self, battle_num: int = 1):
        """전투 후 후반부 스크립트로 교체."""
        key = "script_post_battle" if battle_num <= 1 else f"script_post_battle_{battle_num}"
        if key not in self.script_data:
            key = "script_post_battle"
        if key in self.script_data:
            self.commands = self.script_data[key]
        else:
            self.commands = [{"cmd": "end"}]
        self._idx = 0
        self._labels = {}
        self._build_labels()
        self.done   = False
        self.result = None
        self._run_next()

    def _build_labels(self):
        self._labels = {}
        for i, cmd in enumerate(self.commands):
            if cmd.get("cmd") == "label":
                self._labels[cmd["id"]] = i

    # ── 이벤트 ──────────────────────────────────────────────────
    def handle_event(self, event: pygame.event.Event):
        if self._transition is not None:
            return

        if self._in_choice:
            if event.type == pygame.KEYDOWN:
                n = len(self._choices)
                if event.key in (pygame.K_a, pygame.K_LEFT, pygame.K_UP, pygame.K_w):
                    self._choice_cursor = (self._choice_cursor - 1) % n
                elif event.key in (pygame.K_d, pygame.K_RIGHT, pygame.K_DOWN, pygame.K_s):
                    self._choice_cursor = (self._choice_cursor + 1) % n
                elif event.key in (pygame.K_RETURN, pygame.K_f, pygame.K_SPACE):
                    self._confirm_choice()
            return

        if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
            if event.type == pygame.KEYDOWN and event.key not in (
                pygame.K_RETURN, pygame.K_SPACE, pygame.K_f, pygame.K_z
            ):
                return



            self._on_click()

    def _on_click(self):
        if self._typing:
            # 타이핑 즉시 완성
            self._shown_chars = len(self._full_text)
            self._typing      = False
            self._waiting     = True
        elif self._waiting:
            self._waiting = False
            self._run_next()

    def _confirm_choice(self):
        ch = self._choices[self._choice_cursor]
        self._in_choice = False
        self._choices   = []
        goto = ch.get("goto")
        if goto and goto in self._labels:
            self._idx = self._labels[goto]
        self._run_next()

    # ── 업데이트 ────────────────────────────────────────────────
    def update(self):
        # 타이틀 카드 표시 중
        if self._title_timer > 0:
            self._title_timer -= 1

            if self._title_timer <= 0:
                self._title_card = None
                self._run_next()

            return

        # 전환 효과
        if self._transition is not None:
            self._trans_progress += 0.045
            if self._trans_progress >= 1.0:
                self._bg        = self._bg_next
                self._bg_next   = None
                self._transition = None
                self._trans_progress = 0.0
                self._run_next()
            return

        # 일시 정지
        if self._pause_timer > 0:
            self._pause_timer -= 1
            if self._pause_timer <= 0:
                self._run_next()
            return

        # 타이핑
        if self._typing:
            self._shown_chars = min(
                self._shown_chars + CHAR_PER_FRAME,
                len(self._full_text)
            )
            if self._shown_chars >= len(self._full_text):
                self._typing  = False
                self._waiting = True

        # 화면 흔들기
        if self._shake_timer > 0:
            self._shake_timer -= 1
            self._shake_x = int(math.sin(self._shake_timer * 1.2) * 8)
        else:
            self._shake_x = 0

        if self._ideology_timer > 0:
            self._ideology_timer -= 1

            if self._ideology_timer == 0:
                self._run_next()

            return

    # ── 커맨드 실행 ─────────────────────────────────────────────
    def _run_next(self):
        """다음 커맨드를 처리. 대기가 필요한 커맨드는 중단."""
        while self._idx < len(self.commands):
            cmd = self.commands[self._idx]
            self._idx += 1
            action = cmd.get("cmd", "")

            if action == "bg":
                self._do_bg(cmd)
                if self._transition is not None:
                    return  # 전환 끝날 때까지 대기


            elif action == "show_char":

                slot = cmd.get("slot", "left")

                path = cmd.get("image")

                img = _load_img(path)

                if img:
                    target_w = 350  # 원하는 가로 크기

                    ratio = target_w / img.get_width()

                    target_h = int(img.get_height() * ratio)

                    img = pygame.transform.smoothscale(

                        img,

                        (target_w, target_h)

                    )

                self._chars[slot] = img

            elif action == "hide_char":
                slot = cmd.get("slot", "left")
                self._chars[slot] = None

            elif action == "title_card":
                self._title_card = {
                    "text": cmd.get("text", ""),
                    "background": _load_img(
                        cmd.get("background_image") or cmd.get("image"),
                        (self.W, self.H)
                    )
                }

                self._title_timer = cmd.get("duration", 180)

                return

            elif action == "dialog":
                self._speaker = cmd.get("speaker", "")

                self._auto_show_speaker(self._speaker)

                self._full_text = cmd.get("text", "")
                # "left", "right", "both", "none"
                self._speaker_slot = cmd.get("slot", "both")

                if self._speaker_slot is None:
                    self._speaker_slot = "both"

                self._shown_chars = 0
                self._typing = True
                self._waiting = False
                return

            elif action == "choice":
                self._choices       = cmd.get("options", [])
                self._choice_cursor = 0
                self._in_choice     = True
                return   # 선택 완료 대기

            elif action == "show_image":

                self._center_image = _load_img(
                    cmd.get("image")
                )

            elif action == "hide_image":

                self._center_image = None

            elif action == "label":
                pass   # 레이블은 그냥 통과

            elif action == "goto":
                target = cmd.get("target") or cmd.get("goto") or cmd.get("label")
                if target in self._labels:
                    self._idx = self._labels[target]

            elif action == "ideology_shift":

                self._ideology_timer = 180
                return

            elif action == "pause":
                self._pause_timer = cmd.get("duration", 60)
                return

            elif action == "shake":
                self._shake_timer = 28

            elif action == "sound":
                pass   # 파일 없으면 무시 (추후 구현)

            elif action == "battle_start":
                self.result = "battle"
                self.done   = True
                return

            elif action == "battle_start_2":
                self.result = "battle_2"
                self.done   = True
                return

            elif action.startswith("battle_start_"):
                try:
                    battle_num = int(action.rsplit("_", 1)[-1])
                except ValueError:
                    battle_num = 1
                self.result = f"battle_{battle_num}"
                self.done   = True
                return

            elif action == "ending":
                etype = cmd.get("type","null")
                self.result = f"ending_{etype}"
                self.done   = True
                return

            elif action == "end":
                self.result = "end"
                self.done   = True
                return

        # 커맨드 소진
        self.result = "end"
        self.done   = True

    def _auto_show_speaker(self, speaker):
        self._chars["left"] = None
        self._chars["right"] = None

        # SYSTEM이나 내레이션이면 캐릭터를 표시하지 않음
        if speaker in ("", "SYSTEM"):
            return

        info = self._character_db.get(
            speaker,
            {"slot": "right", "image": "assets/images/story/question.png"}
        )

        slot = info["slot"]

        img = _load_img(info["image"])

        if not img:
            img = _load_img("assets/images/story/question.png")

        if not img:
            return

        # ──────────────
        # 가로폭 고정
        # ──────────────
        TARGET_W = 450

        scale = TARGET_W / img.get_width()

        new_w = TARGET_W
        new_h = int(img.get_height() * scale)

        img = pygame.transform.smoothscale(
            img,
            (new_w, new_h)
        )

        self._chars[slot] = img

    def _do_bg(self, cmd):
        path       = cmd.get("image")
        transition = cmd.get("transition", "fade")

        if path:
            self._bg_next = _load_img(path, (self.W, self.H))
        else:
            self._bg_next = None

        if transition in ("fade", "flash", "fade_black", "white_flash"):
            self._transition      = transition
            self._trans_progress  = 0.0
        else:
            self._bg = self._bg_next
            self._bg_next = None

    # ── 렌더링 ──────────────────────────────────────────────────
    def draw(self):
        sx = self._shake_x

        # ── 배경 ──
        self._draw_bg(sx)

        # ── 캐릭터 ──
        self._draw_chars(sx)

        if self._title_card:
            self._draw_title_card()

        # ── 전환 오버레이 ──
        if self._transition is not None:
            self._draw_transition()
            return

        if self._ideology_timer > 0:
            self._draw_ideology_shift()
            return

        # ── 대사창 ──
        if self._full_text or self._waiting:
            self._draw_dialog_box(sx)

        # ── 선택지 ──
        if self._in_choice:
            self._draw_choices()

        if self._center_image:
            self._draw_center_image()

        # ── 진행 현황 바 (상단) ──
        self._draw_progress_bar()

        # ── 클릭 힌트 ──
        if self._waiting and not self._in_choice:
            self._draw_click_hint()

    def _draw_bg(self, sx):
        if self._bg:
            self.screen.blit(self._bg, (sx, 0))
        else:
            self.screen.fill((8, 10, 22))

    def _make_inactive_char(self, img: pygame.Surface) -> pygame.Surface:
        """말하지 않거나 비활성화된 캐릭터를 어둡게 만든 이미지."""
        dark_img = img.copy()

        shade = pygame.Surface(dark_img.get_size()).convert()
        shade.fill((100, 100, 100))  # 숫자가 낮을수록 더 어두움

        dark_img.blit(shade, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
        return dark_img

    def _draw_chars(self, sx):
        highlight = self._speaker_slot

        for slot in ("left", "right"):
            img = self._chars.get(slot)
            if not img:
                continue

            draw_img = img

            if highlight == "none":
                # 둘 다 어둡게
                draw_img = self._make_inactive_char(img)

            elif highlight in ("left", "right"):
                # 말하는 쪽만 밝게
                if slot != highlight:
                    draw_img = self._make_inactive_char(img)

            elif highlight in ("both", "all"):
                # 둘 다 밝게
                pass

            else:
                # 이상한 값이 들어오면 기본값: 둘 다 밝게
                pass

            if slot == "left":
                x = sx + 60
            else:
                x = self.W + sx - 60 - draw_img.get_width()

            BOX_H = 180
            BOX_Y = self.H - BOX_H

            y = BOX_Y - draw_img.get_height()

            self.screen.blit(draw_img, (x, y))

    def _draw_dialog_box(self, sx):
        """
        하단 대사창 — 이미지처럼:
        - 반투명 검정 바
        - 상단: 화자 이름 박스
        - 본문: 타이핑 텍스트 (줄바꿈 처리)
        """
        BOX_H  = 180
        BOX_Y  = self.H - BOX_H
        PAD    = 28

        # 메인 박스
        box = pygame.Surface((self.W, BOX_H), pygame.SRCALPHA)
        box.fill((0, 0, 0, 185))
        # 상단 얇은 선
        pygame.draw.line(box, (80, 100, 160, 180), (0, 0), (self.W, 0), 2)
        self.screen.blit(box, (sx, BOX_Y))

        # 화자 이름 박스
        is_system = self._speaker in ("SYSTEM", "")
        if self._speaker:
            spk_col = (100, 200, 255) if is_system else (255, 255, 200)
            spk_sf  = self.fnt_speaker.render(self._speaker, True, spk_col)
            # 이름 뒤 배경
            name_box = pygame.Surface((spk_sf.get_width() + 24, 30), pygame.SRCALPHA)
            name_col = (20, 30, 80, 220) if is_system else (20, 20, 20, 220)
            name_box.fill(name_col)
            pygame.draw.rect(name_box, (*spk_col, 120), name_box.get_rect(), 1)
            self.screen.blit(name_box, (sx + PAD - 4, BOX_Y - 30))
            self.screen.blit(spk_sf,   (sx + PAD + 8, BOX_Y - 26))

        # 본문 (타이핑 + 줄바꿈)
        shown = self._full_text[:self._shown_chars]
        lines = self._wrap_text(shown, self.fnt_dialog, self.W - PAD * 2)
        text_col = (180, 230, 255) if is_system else (240, 240, 240)
        for i, line in enumerate(lines[:5]):
            sf = self.fnt_dialog.render(line, True, text_col)
            self.screen.blit(sf, (sx + PAD, BOX_Y + 22 + i * 28))

    def _draw_choices(self):
        """양자택일 선택창 — 화면 하단 중앙에 카드 형태로."""
        n    = len(self._choices)
        CW   = 280
        CH   = 52
        GAP  = 20
        total_w = n * CW + (n-1) * GAP
        bx   = self.W // 2 - total_w // 2
        by   = self.H - 210

        for i, ch in enumerate(self._choices):
            x   = bx + i * (CW + GAP)
            sel = (i == self._choice_cursor)

            card = pygame.Surface((CW, CH), pygame.SRCALPHA)
            if sel:
                card.fill((40, 60, 140, 220))
                pygame.draw.rect(card, (100, 160, 255, 255), (0,0,CW,CH), 2, border_radius=8)
            else:
                card.fill((15, 15, 35, 200))
                pygame.draw.rect(card, (60, 80, 140, 160), (0,0,CW,CH), 1, border_radius=8)
            self.screen.blit(card, (x, by))

            col = (255, 255, 255) if sel else (160, 170, 200)
            sf  = self.fnt_choice.render(ch["text"], True, col)
            self.screen.blit(sf, (x + CW//2 - sf.get_width()//2,
                                   by + CH//2 - sf.get_height()//2))

        # 가이드
        guide = self.fnt_sm.render("A/D or ←/→  select   ENTER confirm",
                                    True, (120,120,150))
        self.screen.blit(guide, (self.W//2 - guide.get_width()//2, by + CH + 8))

    def _draw_progress_bar(self):
        """상단 스테이지 진행 현황 바."""
        total   = self.script_data.get("_total_stages", 5)
        current = self.script_data.get("_current_stage", 1)

        bw = 320; bh = 6
        bx = self.W // 2 - bw // 2; by = 8

        pygame.draw.rect(self.screen, (20,20,40), (bx,by,bw,bh), border_radius=3)
        fw = int(bw * (current / max(1, total)))
        if fw > 0:
            pygame.draw.rect(self.screen, (70,120,255), (bx,by,fw,bh), border_radius=3)
        pygame.draw.rect(self.screen, (50,70,140), (bx,by,bw,bh), 1, border_radius=3)

        # 스테이지 이름
        title = self.script_data.get("title","")
        if title:
            ts = self.fnt_sm.render(title, True, (140,160,200))
            self.screen.blit(ts, (self.W//2 - ts.get_width()//2, by + bh + 4))

    def _draw_click_hint(self):
        t   = pygame.time.get_ticks() / 600
        a   = int(140 + 100 * abs(math.sin(t)))
        sf  = self.fnt_sm.render("▶  SPACE / ENTER  to continue", True, (200,200,220))
        sf.set_alpha(a)
        self.screen.blit(sf, (self.W - sf.get_width() - 18, self.H - 28))

    def _draw_transition(self):
        p = min(1.0, self._trans_progress)

        if self._transition == "fade":
            # 이전 bg → 새 bg 크로스페이드
            if self._bg_next:
                self._bg_next.set_alpha(int(255 * p))
                self.screen.blit(self._bg_next, (0, 0))

        elif self._transition == "fade_black":
            ov = pygame.Surface((self.W, self.H))
            ov.fill((0,0,0))
            ov.set_alpha(int(255 * p))
            self.screen.blit(ov, (0, 0))

        elif self._transition == "white_flash":
            ov = pygame.Surface((self.W, self.H))
            ov.fill((255,255,255))
            ov.set_alpha(int(255 * (1 - abs(p * 2 - 1))))
            self.screen.blit(ov, (0, 0))

        elif self._transition == "flash":
            ov = pygame.Surface((self.W, self.H))
            ov.fill((255,255,255))
            ov.set_alpha(int(255 * (1 - p)))
            self.screen.blit(ov, (0, 0))

    # ── 텍스트 줄바꿈 ────────────────────────────────────────────
    @staticmethod
    def _wrap_text(text: str, font: pygame.font.Font, max_w: int) -> list[str]:
        lines = []
        for paragraph in text.split("\n"):
            words = paragraph.split()
            line  = ""
            for word in words:
                test = (line + " " + word).strip()
                if font.size(test)[0] <= max_w:
                    line = test
                else:
                    if line:
                        lines.append(line)
                    line = word
            lines.append(line)
        return lines

    def _draw_title_card(self):

        bg = self._title_card.get("background")
        if bg:
            self.screen.blit(bg, (0, 0))

        overlay = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 80))
        self.screen.blit(overlay, (0, 0))

        txt = self._title_card["text"]

        title_font = font(54, bold=True)

        lines = txt.split("\n")

        start_y = self.H // 2 - len(lines) * 35

        for i, line in enumerate(lines):
            shadow = title_font.render(line, True, (0, 0, 0))
            main = title_font.render(line, True, (255, 255, 255))

            x = self.W // 2
            y = start_y + i * 70

            sr = shadow.get_rect(center=(x + 3, y + 3))
            mr = main.get_rect(center=(x, y))

            self.screen.blit(shadow, sr)
            self.screen.blit(main, mr)

    def _draw_center_image(self):

        img = self._center_image

        scale = min(
            self.W * 0.6 / img.get_width(),
            self.H * 0.55 / img.get_height()
        )

        w = int(img.get_width() * scale)
        h = int(img.get_height() * scale)

        img = pygame.transform.smoothscale(img, (w, h))

        rect = img.get_rect(
            center=(self.W // 2, self.H // 2 - 40)
        )

        self.screen.blit(img, rect)

    def _draw_ideology_shift(self):

        self.screen.fill((0, 0, 0))

        pulse = abs(math.sin(
            pygame.time.get_ticks() / 120
        ))

        size = int(80 + pulse * 20)

        f = font(size, bold=True)

        txt = f.render(
            "사상 변화",
            True,
            (255, 0, 0)
        )

        rect = txt.get_rect(
            center=(self.W // 2, self.H // 2)
        )

        self.screen.blit(txt, rect)
