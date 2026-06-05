"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
새 캐릭터 추가 방법 — 이 파일을 복사해서 사용하세요
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. 이 파일을 복사: doctor_yellow.py (이름 자유)
2. 클래스명 변경:  DoctorYellow
3. 스탯, 색상, 스킬 수정
4. scenes/character_select.py 상단 ROSTER에 추가:
       from entities.characters.doctor_yellow import DoctorYellow
       ROSTER = [DoctorBlue, DoctorRed, DoctorGreen, DoctorPurple, DoctorYellow]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
스탯 가이드 (캐릭터 선택창 바 표시에 영향)
    WALK_SPEED : 4.0(느림) ~ 8.5(빠름)
    JUMP_POWER : -12(낮음) ~ -18(높음)  ← 음수일수록 높이 뜀
    MAX_JUMPS  : 2(기본) or 3(3단 점프)
    ATTACK_DMG : 7(약함) ~ 18(강함)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
from entities.player import Player
from systems.skill import Skill


class DoctorTemplate(Player):
    # ── 스탯 ──────────────────────────────────────────────────
    WALK_SPEED = 6.5        # 이동 속도
    JUMP_POWER = -15.5      # 점프 파워 (음수, 클수록 높이 뜀)
    MAX_JUMPS  = 2          # 최대 점프 횟수 (2 or 3)
    ATTACK_DMG = 12         # 기본 공격 데미지 (%)
    ATK_FRAMES = 20         # 공격 모션 프레임 수 (클수록 느린 공격)
    ATK_CD     = 34         # 공격 쿨다운 프레임
    HIT_START  = 4          # 히트박스 활성 시작 프레임
    HIT_END    = 15         # 히트박스 활성 종료 프레임

    # ── 색상 (RGB) ────────────────────────────────────────────
    BODY_COLOR = (220, 200, 50)     # 몸통 메인 색
    TRIM_COLOR = (140, 120, 20)     # 가운·다리 트림 색
    GLOW_COLOR = (255, 240, 100)    # 파티클·스킬 글로우 색
    DARK_COLOR = (100,  85, 10)     # 발·어두운 부분

    # ── 캐릭터 선택창 표시 ────────────────────────────────────
    DISPLAY_NAME  = "Dr. Yellow"            # 선택창 이름
    DESCRIPTION   = "빠른 이동과 넓은 공격.\n균형형 닥터."   # 2줄 설명
    PREVIEW_COLOR = (220, 200, 50)          # 선택창 카드 컬러 (보통 BODY_COLOR)
    SKILL_NAME    = "Thunder Strike"        # 스킬 이름 (선택창에 표시)

    # ── 스킬 설정 ─────────────────────────────────────────────
    SKILL_DAMAGE      = 25   # 스킬 데미지 (%)
    SKILL_FATIGUE     = 30   # 스킬 피로도 소모량
    SKILL_COOLDOWN    = 90   # 스킬 쿨다운 (프레임, 60f = 1초)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 아래는 건드리지 않아도 됩니다
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def __init__(self, x, y, name="Player", player_id=1):
        super().__init__(x, y, name, player_id)
        self.color         = self.BODY_COLOR
        self.trim_color    = self.TRIM_COLOR
        self.glow_color    = self.GLOW_COLOR
        self.dark_color    = self.DARK_COLOR
        self.max_jumps     = self.MAX_JUMPS
        self.attack_damage = self.ATTACK_DMG
        self.skills["skill_1"] = Skill(
            name=self.SKILL_NAME,
            damage=self.SKILL_DAMAGE,
            fatigue_cost=self.SKILL_FATIGUE,
            cooldown=self.SKILL_COOLDOWN,
        )

    def get_char_name(self) -> str:
        return self.DISPLAY_NAME
