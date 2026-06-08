"""
FontManager — 전역 한글 폰트 관리자

사용법:
    from systems.font_manager import font

    font(20)            → 20px 일반체
    font(20, bold=True) → 20px 볼드
"""
import pygame

_CANDIDATES = [
    "malgungothic",        # Windows 맑은고딕
    "malgunGothicregular",
    "gulim",               # Windows 굴림
    "dotum",               # Windows 돋움
    "nanumgothic",
    "applegothic",         # macOS
    "nanumgothicbold",
    "notosanscjkkr",       # Linux
    "notosanscjkjp",
    "dejavusans",
    "freesans",
]

_korean_font_name: str | None = None
_cache: dict[tuple, pygame.font.Font] = {}


def _detect():
    global _korean_font_name
    if _korean_font_name is not None:
        return
    avail = set(pygame.font.get_fonts())
    for name in _CANDIDATES:
        if name.lower() in avail:
            _korean_font_name = name
            print(f"[FontManager] 한글 폰트 감지: {name}")
            return
    _korean_font_name = ""
    print("[FontManager] 한글 폰트 없음 → pygame 기본 폰트 사용")


def font(size: int, bold: bool = False) -> pygame.font.Font:
    """캐시된 폰트 반환. pygame.init() 이후 호출해야 함."""
    _detect()
    key = (size, bold)
    if key not in _cache:
        if _korean_font_name:
            _cache[key] = pygame.font.SysFont(_korean_font_name, size, bold=bold)
        else:
            _cache[key] = pygame.font.SysFont(None, size, bold=bold)
    return _cache[key]
