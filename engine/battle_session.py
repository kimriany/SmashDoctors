# engine/battle_session.py

import pygame

from settings import SCREEN_WIDTH, SCREEN_HEIGHT, BLAST_MARGIN
from systems.font_manager import font

from engine.camera import Camera
from engine.renderer import Renderer

from systems.event_bus import EventBus
from systems.stage_loader import StageLoader
from systems.particle import ParticleSystem
from systems.floater import FloaterSystem
from systems.domain_system import DomainSystem
from systems.finisher_system import FinisherSystem


class BattleSession:
    """
    전투 한 판만 담당하는 클래스.

    mode="pvp":
        - player1, player2 둘 다 입력을 받음
        - 결과: "p1_win", "p2_win", "back"

    mode="story":
        - player1만 입력을 받음
        - player2는 보스/AI
        - 결과: "p1_dead", "p2_dead", "back"
    """

    RESPAWN_EDGE_INSET = 140

    def __init__(
        self,
        screen,
        stage_info,
        player1_cls,
        player2_cls,
        mode="pvp",
        player1_name=None,
        player2_name=None,
        player1_stocks=3,
        player2_stocks=3,
        dual_domain_bg_path="assets/images/Double_domain.jpeg",
        story_boss_profile=None,
        story_player_skills=None,
    ):
        self.screen = screen
        self.stage_info = stage_info
        self.player1_cls = player1_cls
        self.player2_cls = player2_cls
        self.mode = mode

        self.player1_name = player1_name or ("Player" if mode == "story" else "Player 1")
        self.player2_name = player2_name or ("Boss" if mode == "story" else "Player 2")

        self.player1_stocks = player1_stocks
        self.player2_stocks = player2_stocks

        self.camera = Camera(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.renderer = Renderer(self.screen)

        self.event_bus = EventBus()
        self.particle_sys = ParticleSystem()
        self.floater_sys = FloaterSystem()

        self.domain_sys = None

        self.platforms = []
        self.player1 = None
        self.player2 = None

        self.result = None
        self.winner_name = ""
        self.winner_color = (255, 255, 255)

        self.dual_domain_bg_path = dual_domain_bg_path
        self.story_boss_profile = story_boss_profile or {}
        self.story_player_skills = story_player_skills or {}

        self.story_state = "INTRO"
        self.boss_domain_started = False
        self.boss_domain_broken = False
        self.story_domain_rules = {}
        self.domain_survive_timer = 0
        self.double_domain_timer = 0
        self.domain_survive_required = 30 * 60
        self.story_message = ""
        self.story_message_timer = 0

        self._setup_battle()

    # ─────────────────────────────────────────────
    # 초기화
    # ─────────────────────────────────────────────
    def _setup_battle(self):
        data = StageLoader(self.stage_info["path"]).load()

        self.platforms = data["platforms"]
        self.blast_bounds = self._make_blast_bounds(self.platforms)

        sp1 = data.get("player_spawn", [220, 340])
        sp2 = data.get("boss_spawn", [940, 340])

        if self.player2_cls is None:
            from entities.characters.Einstein import Einstein
            self.player2_cls = Einstein

        self.player1 = self.player1_cls(
            sp1[0],
            sp1[1],
            name=self.player1_name,
            player_id=1,
        )

        self.player2 = self.player2_cls(
            sp2[0],
            sp2[1],
            name=self.player2_name,
            player_id=2,
        )

        if self.mode == "story" and hasattr(self.player1, "configure_story_skills"):
            self.player1.configure_story_skills(self.story_player_skills)

        if self.mode == "story" and hasattr(self.player2, "configure_profile"):
            self.player2.configure_profile(self.story_boss_profile)

        self.player1.spawn_x = sp1[0]
        self.player1.spawn_y = sp1[1]
        self.player2.spawn_x = sp2[0]
        self.player2.spawn_y = sp2[1]

        self._snap_spawn_to_platform(self.player1)
        self._snap_spawn_to_platform(self.player2)
        self._set_fixed_respawn_points()

        self.player1.stocks = self.player1_stocks
        self.player2.stocks = self.player2_stocks

        if self.mode == "story":
            self._configure_story_battle()

        stage_id = self.stage_info.get("id")
        if stage_id is not None:
            self.renderer.load_stage_background(stage_id)

        self.domain_sys = DomainSystem(
            screen=self.screen,
            renderer=self.renderer,
            camera=self.camera,
            event_bus=self.event_bus,
            particle_sys=self.particle_sys,
            dual_domain_bg_path=self.dual_domain_bg_path,
        )
        self.finisher_sys = FinisherSystem(
            screen=self.screen,
            camera=self.camera,
            event_bus=self.event_bus,
            particle_sys=self.particle_sys,
        )

        self.event_bus.subscribe("domain_request", self.domain_sys.on_domain_request)
        self.event_bus.subscribe("attack_hit", self.domain_sys.on_attack_hit)

        self.event_bus.subscribe("attack_hit", self._on_attack_hit)
        self.event_bus.subscribe("entity_dead", self._on_entity_dead)

        self.event_bus.subscribe("stock_lost", self._on_stock_lost)

    def _configure_story_battle(self):
        self.story_domain_rules = self._build_story_domain_rules()
        self.story_state = "PHASE_1"
        self.boss_domain_started = False
        self.boss_domain_broken = False
        self.player_counter_domain_unlocked = False
        self.domain_survive_timer = 0
        self.double_domain_timer = 0
        self.domain_survive_required = int(self._story_domain_rule("counter_domain_delay_frames", 30 * 60))
        self.story_message = "Boss battle started"
        self.story_message_timer = 150

        self.player1.stocks = 3
        self.player1.domain_locked = True
        self.player1.domain_charge_stack = 0.0
        self.player1.domain_ready = False
        self.player1.finisher_charge_stack = 0.0
        self.player1.finisher_ready = False
        self.player1.finisher_locked = True

        self.player2.stocks = 1
        if hasattr(self.player2, "boss_domain_max_hp"):
            domain_hp = float(self._story_domain_rule("boss_domain_hp", getattr(self.player2, "boss_domain_max_hp", 320.0)))
            self.player2.boss_domain_max_hp = domain_hp
            self.player2.boss_domain_hp = domain_hp
        if hasattr(self.player2, "set_target"):
            self.player2.set_target(self.player1)
        if hasattr(self.player2, "final_lock"):
            self.player2.final_lock = bool(self._story_domain_rule("final_lock", True))

    def _build_story_domain_rules(self):
        rules = {}
        boss_rules = getattr(self.player2, "STORY_DOMAIN_RULES", None)
        if isinstance(boss_rules, dict):
            rules.update(boss_rules)

        profile_rules = {}
        if isinstance(self.story_boss_profile, dict):
            profile_rules = self.story_boss_profile.get("domain_rules") or {}
        if isinstance(profile_rules, dict):
            rules.update(profile_rules)

        if "requires_finisher" in rules:
            rules["final_lock"] = bool(rules["requires_finisher"])

        if "counter_domain_cooldown_sec" in rules:
            rules["counter_domain_delay_frames"] = int(float(rules["counter_domain_cooldown_sec"]) * 60)
        if "counter_domain_cooldown_frames" in rules:
            rules["counter_domain_delay_frames"] = rules["counter_domain_cooldown_frames"]
        if "counter_domain_unlock_hp_ratio" in rules:
            rules["counter_domain_boss_hp_ratio"] = rules["counter_domain_unlock_hp_ratio"]

        return rules

    def _story_domain_rule(self, key, default=None):
        value = self.story_domain_rules.get(key, default)
        return default if value is None else value

    def _snap_spawn_to_platform(self, player):
        if player is None or not self.platforms:
            return

        center_x = player.rect.centerx
        bottom_y = player.rect.bottom

        candidates = [
            p for p in self.platforms
            if p.left <= center_x <= p.right
        ]

        if not candidates:
            candidates = self.platforms

        platform = min(
            candidates,
            key=lambda p: (
                abs(p.top - bottom_y),
                abs(p.centerx - center_x),
            ),
        )

        player.rect.bottom = platform.top
        player.spawn_x = player.rect.x
        player.spawn_y = player.rect.y

    def _set_fixed_respawn_points(self):
        if not self.platforms:
            return

        for player, side in ((self.player1, "left"), (self.player2, "right")):
            if player is None:
                continue

            platform = self._respawn_platform_for_side(side)
            max_inset = max(0, platform.w // 2 - player.rect.w // 2)
            inset = min(self.RESPAWN_EDGE_INSET, max_inset)
            if side == "left":
                center_x = platform.left + inset
            else:
                center_x = platform.right - inset

            player.spawn_x = int(center_x - player.rect.w // 2)
            player.spawn_y = int(platform.top - player.rect.h)

    def _respawn_platform_for_side(self, side):
        max_width = max(p.w for p in self.platforms)
        widest = [p for p in self.platforms if p.w == max_width]
        if side == "left":
            return min(widest, key=lambda p: p.centerx)
        return max(widest, key=lambda p: p.centerx)

    def _make_blast_bounds(self, platforms):
        if not platforms:
            return pygame.Rect(
                -BLAST_MARGIN,
                -BLAST_MARGIN,
                SCREEN_WIDTH + BLAST_MARGIN * 2,
                SCREEN_HEIGHT + BLAST_MARGIN * 2,
            )

        left = min(p.left for p in platforms) - BLAST_MARGIN
        right = max(p.right for p in platforms) + BLAST_MARGIN
        top = min(p.top for p in platforms) - BLAST_MARGIN
        bottom = max(p.bottom for p in platforms) + BLAST_MARGIN
        return pygame.Rect(left, top, right - left, bottom - top)

    def _on_stock_lost(self, data):
        lost_player = data.get("player")
        killer = data.get("killer")

        if killer is None:
            if lost_player is self.player1:
                killer = self.player2
            elif lost_player is self.player2:
                killer = self.player1

        if self.mode == "story":
            self._on_story_stock_lost(lost_player, killer, data)
            return

        # 모든 영역 배경/상태 제거
        if hasattr(self, "domain_sys") and self.domain_sys:
            if hasattr(self.domain_sys, "force_clear_all"):
                cutscene = data.get("reason") != "finisher"
                self.domain_sys.force_clear_all(winner=killer, cutscene=cutscene)

        # 양쪽 플레이어 영역 스탯/스택 전부 초기화
        for p in (self.player1, self.player2):
            if hasattr(p, "reset_domain_state"):
                p.reset_domain_state()

    def _on_story_stock_lost(self, lost_player, killer, data):
        if lost_player is self.player1:
            was_counter_domain_active = bool(data.get("was_domain_active"))
            pid = getattr(self.player1, "player_id", None)
            if self.domain_sys and pid in getattr(self.domain_sys, "active_domains", {}):
                self.domain_sys.break_domain(self.player1)

            if hasattr(self.player1, "reset_domain_state"):
                self.player1.reset_domain_state(
                    domain_locked=bool(data.get("was_domain_locked")),
                    finisher_locked=True,
                )

            if self.player1.stocks > 0 and self.boss_domain_started and not self.boss_domain_broken:
                if was_counter_domain_active:
                    self.player_counter_domain_unlocked = True
                    self.player1.domain_locked = False
                    self.player1.domain_charge_stack = 0.0
                    self.player1.domain_ready = False
                    self._set_story_message("Counter domain lost. Rebuild stacks.", 180)
                else:
                    self.player1.domain_locked = True
                    self._set_story_message("Boss domain remains active", 150)
                self.player1.finisher_locked = True
                self.player1.finisher_ready = False
                self.player1.finisher_charge_stack = 0.0
            return

        if lost_player is self.player2:
            if self.domain_sys and hasattr(self.domain_sys, "force_clear_all"):
                cutscene = data.get("reason") != "finisher"
                self.domain_sys.force_clear_all(winner=killer, cutscene=cutscene)
            for p in (self.player1, self.player2):
                if hasattr(p, "reset_domain_state"):
                    p.reset_domain_state()
    # ─────────────────────────────────────────────
    # 외부 호출
    # ─────────────────────────────────────────────
    def update(self, events):
        if self.result is not None:
            return self.result

        # 현재 프레임에서 각 플레이어의 상대를 지정
        # R키 필살기, 호밍 투사체 등이 target을 알기 위해 필요함
        self.player1._skill_target = self.player2
        self.player2._skill_target = self.player1

        self._handle_events(events)
        self._update_frame()
        return self.result
    def draw(self):
        self._draw_game()

    def draw_win(self):
        self._draw_game()
        self.renderer.draw_win_screen(self.winner_name, self.winner_color)

    # ─────────────────────────────────────────────
    # 입력
    # ─────────────────────────────────────────────
    def _handle_events(self, events):
        for event in events:
            if event.type != pygame.KEYDOWN:
                continue

            k = event.key

            if k == pygame.K_ESCAPE:
                self.result = "back"
                return

            if (self.domain_sys and self.domain_sys.gameplay_frozen) or \
                    (self.finisher_sys and self.finisher_sys.gameplay_frozen):
                continue

            if self.mode == "pvp":
                self.player1.handle_keydown(k, self.event_bus, self.particle_sys)
                self.player2.handle_keydown(k, self.event_bus, self.particle_sys)

            elif self.mode == "story":
                self.player1.handle_keydown(k, self.event_bus, self.particle_sys)

    # ─────────────────────────────────────────────
    # 업데이트
    # ─────────────────────────────────────────────
    def _update_frame(self):
        if self.domain_sys:
            self.domain_sys.update()
        if self.finisher_sys:
            self.finisher_sys.update()
            if not self.finisher_sys.active:
                self._check_result()

        if (self.domain_sys and self.domain_sys.gameplay_frozen) or \
                (self.finisher_sys and self.finisher_sys.gameplay_frozen):
            self.particle_sys.update()
            self.floater_sys.update()
            return

        keys = pygame.key.get_pressed()

        self.player1.handle_input(keys)

        if self.mode == "pvp":
            self.player2.handle_input(keys)

        elif self.mode == "story":
            self._update_story_boss_ai()

        ps = self.particle_sys
        fs = self.floater_sys

        self.player1.update(0, self.platforms, self.event_bus, ps)
        self.player2.update(0, self.platforms, self.event_bus, ps)

        if self.mode == "story" and hasattr(self.player2, "resolve_target_body_collision"):
            self.player2.resolve_target_body_collision(self.player1, self.platforms)

        if self._can_attack_target(self.player1, self.player2):
            self.player1.check_attack_collision(self.player2, self.event_bus, ps, fs)
        self.player2.check_attack_collision(self.player1, self.event_bus, ps, fs)

        if self._can_attack_target(self.player1, self.player2):
            self.player1.check_skill_collision(self.player2, self.event_bus, ps, fs)
        self.player2.check_skill_collision(self.player1, self.event_bus, ps, fs)

        self._check_blast_zones()

        if self.mode == "story":
            self._update_story_boss_flow()

        ps.update()
        fs.update()

        self._update_camera()

    def _update_story_boss_ai(self):
        if hasattr(self.player2, "ai_update"):
            self.player2.ai_update(
                self.player1,
                self.platforms,
                self.event_bus,
                self.particle_sys,
            )

        elif hasattr(self.player2, "handle_ai"):
            self.player2.handle_ai(self.player1)

    def _can_attack_target(self, attacker, target):
        if self.mode == "story" and target is self.player2:
            return bool(getattr(target, "targetable", True))
        return True

    def _update_story_boss_flow(self):
        boss = self.player2
        player = self.player1
        if boss is None or player is None or boss.dead or player.dead:
            return

        if self.story_message_timer > 0:
            self.story_message_timer -= 1

        hp_ratio = getattr(boss, "hp_ratio", 1.0)
        if not self.boss_domain_started:
            domain_start_ratio = self._story_domain_rule("boss_domain_start_hp_ratio", 0.50)
            phase2_ratio = self._story_domain_rule("boss_phase2_hp_ratio", 0.75)
            if domain_start_ratio is not None and hp_ratio <= float(domain_start_ratio):
                self._start_boss_domain()
            elif phase2_ratio is not None and hp_ratio <= float(phase2_ratio):
                self.story_state = "PHASE_2"
            else:
                self.story_state = "PHASE_1"
            return

        boss_domain_active = getattr(boss, "domain_active", False)
        player_domain_active = getattr(player, "domain_active", False)

        if boss_domain_active and not player_domain_active and not self.boss_domain_broken:
            self.story_state = "SURVIVE_DOMAIN"
            self.domain_survive_timer = min(
                self.domain_survive_required,
                self.domain_survive_timer + 1,
            )
            if self._can_unlock_player_domain():
                if self.player_counter_domain_unlocked:
                    player.domain_locked = False
                    player.finisher_locked = True
                    player.finisher_ready = False
                else:
                    self._unlock_player_domain()
            return

        if boss_domain_active and player_domain_active and not self.boss_domain_broken:
            self.story_state = "DOUBLE_DOMAIN"
            self.double_domain_timer += 1
            player.finisher_locked = True
            player.finisher_ready = False
            if self._should_break_boss_domain():
                self._break_boss_domain()
            return

        if self.boss_domain_broken and player_domain_active:
            self.story_state = "PLAYER_ULTIMATE_READY"
            if bool(self._story_domain_rule("finisher_ready_on_break", True)):
                self._force_player_finisher_ready()

    def _start_boss_domain(self):
        self.boss_domain_started = True
        self.domain_survive_timer = 0
        self.double_domain_timer = 0
        self.story_state = "BOSS_DOMAIN"
        self._set_story_message("Boss domain expansion", 180)

        if hasattr(self.player2, "boss_domain_max_hp"):
            domain_hp = float(self._story_domain_rule("boss_domain_hp", getattr(self.player2, "boss_domain_max_hp", 320.0)))
            self.player2.boss_domain_max_hp = domain_hp
            self.player2.boss_domain_hp = domain_hp

        if hasattr(self.player2, "open_domain"):
            self.player2.open_domain(self.event_bus)

    def _can_unlock_player_domain(self):
        boss = self.player2
        player = self.player1
        if self.domain_survive_timer < self.domain_survive_required:
            return False

        boss_hp_ratio = self.story_domain_rules.get("counter_domain_boss_hp_ratio")
        if boss_hp_ratio is not None and getattr(boss, "hp_ratio", 1.0) > float(boss_hp_ratio):
            return False

        boss_hp = self.story_domain_rules.get("counter_domain_boss_hp")
        if boss_hp is not None and getattr(boss, "hp", 0.0) > float(boss_hp):
            return False

        player_damage_min = self.story_domain_rules.get("counter_domain_player_damage_pct_min")
        if player_damage_min is not None and getattr(player, "damage_pct", 0.0) < float(player_damage_min):
            return False

        return True

    def _should_break_boss_domain(self):
        boss = self.player2
        if getattr(boss, "boss_domain_hp", 0.0) <= 0:
            return True

        break_after = self.story_domain_rules.get("double_domain_break_delay_frames")
        if break_after is not None and self.double_domain_timer >= int(break_after):
            return True

        break_hp_ratio = self.story_domain_rules.get("double_domain_break_boss_hp_ratio")
        if break_hp_ratio is not None and getattr(boss, "hp_ratio", 1.0) <= float(break_hp_ratio):
            return True

        break_hp = self.story_domain_rules.get("double_domain_break_boss_hp")
        if break_hp is not None and getattr(boss, "hp", 0.0) <= float(break_hp):
            return True

        return False

    def _unlock_player_domain(self):
        player = self.player1
        if getattr(player, "domain_ready", False) and not getattr(player, "domain_locked", False):
            self.story_state = "PLAYER_DOMAIN_READY"
            return

        player.domain_locked = False
        self.player_counter_domain_unlocked = True
        player.domain_charge_stack = getattr(player, "domain_charge_required", 8.0)
        player.domain_ready = True
        player.finisher_locked = True
        player.finisher_ready = False
        player.finisher_charge_stack = 0.0
        self.story_state = "PLAYER_DOMAIN_READY"
        self._set_story_message("R: Counter Domain ready", 180)

    def _damage_boss_domain(self, amount):
        boss = self.player2
        if self.boss_domain_broken:
            return
        if not getattr(boss, "domain_active", False):
            return
        if not getattr(self.player1, "domain_active", False):
            return

        scale = float(self._story_domain_rule("boss_domain_damage_scale", 1.0))
        boss.boss_domain_hp = max(0.0, getattr(boss, "boss_domain_hp", 0.0) - float(amount) * scale)
        if self._should_break_boss_domain():
            self._break_boss_domain()

    def _break_boss_domain(self):
        boss = self.player2
        self.boss_domain_broken = True
        self.story_state = "BOSS_DOMAIN_BROKEN"
        self._set_story_message("Boss domain broken. Finish it.", 210)

        boss.domain_broken = True
        boss.weakened_timer = max(getattr(boss, "weakened_timer", 0), 240)
        boss.stagger_timer = max(getattr(boss, "stagger_timer", 0), 80)
        if bool(self._story_domain_rule("release_final_lock_on_domain_break", False)):
            boss.final_lock = False

        if self.domain_sys:
            self.domain_sys.break_domain(boss)

        if bool(self._story_domain_rule("finisher_ready_on_break", True)):
            self._force_player_finisher_ready()

    def _force_player_finisher_ready(self):
        player = self.player1
        player.finisher_locked = False
        player.finisher_charge_stack = getattr(player, "finisher_charge_required", 5.0)
        player.finisher_ready = True

    def _set_story_message(self, text, frames=150):
        self.story_message = text
        self.story_message_timer = frames

    def _counter_domain_status_text(self):
        remain_frames = max(0, self.domain_survive_required - self.domain_survive_timer)
        parts = []
        if remain_frames > 0:
            parts.append(f"{remain_frames // 60}s")

        boss_hp_ratio = self.story_domain_rules.get("counter_domain_boss_hp_ratio")
        if boss_hp_ratio is not None and getattr(self.player2, "hp_ratio", 1.0) > float(boss_hp_ratio):
            parts.append(f"boss HP <= {int(float(boss_hp_ratio) * 100)}%")

        boss_hp = self.story_domain_rules.get("counter_domain_boss_hp")
        if boss_hp is not None and getattr(self.player2, "hp", 0.0) > float(boss_hp):
            parts.append(f"boss HP <= {int(float(boss_hp))}")

        player_damage_min = self.story_domain_rules.get("counter_domain_player_damage_pct_min")
        if player_damage_min is not None and getattr(self.player1, "damage_pct", 0.0) < float(player_damage_min):
            parts.append(f"damage >= {int(float(player_damage_min))}%")

        if parts:
            return "Boss domain active  |  Counter requires " + ", ".join(parts)
        return "R: Counter Domain available"

    def _update_camera(self):
        active = []

        for entity in (self.player1, self.player2):
            if entity.dead:
                continue

            if getattr(entity, "respawning", False):
                continue

            active.append(entity.rect)

        if active:
            self.camera.update(active)

    # ─────────────────────────────────────────────
    # 장외 판정
    # ─────────────────────────────────────────────
    def _check_blast_zones(self):
        for p in (self.player1, self.player2):
            if p.dead:
                continue

            if getattr(p, "respawning", False):
                continue

            if (
                p.rect.right < self.blast_bounds.left
                or p.rect.left > self.blast_bounds.right
                or p.rect.bottom < self.blast_bounds.top
                or p.rect.top > self.blast_bounds.bottom
            ):
                if hasattr(p, "lose_stock"):
                    if self.mode == "story" and p is self.player2:
                        p.rect.x = p.spawn_x
                        p.rect.y = p.spawn_y
                        p.vel = pygame.Vector2(0, 0)
                    else:
                        p.lose_stock(self.event_bus)

    # ─────────────────────────────────────────────
    # 이벤트 버스 콜백
    # ─────────────────────────────────────────────
    def _on_attack_hit(self, data):
        attacker = data["attacker"]
        target = data["target"]
        damage = float(data["damage"])
        if hasattr(target, "modify_incoming_damage"):
            damage = float(target.modify_incoming_damage(damage, attacker=attacker, data=data))

        ps = data.get("particle_system")
        fs = data.get("floater_system")

        if not data.get("skip_damage", False):
            target.take_damage(damage)

        if not data.get("skip_knockback", False):
            target.apply_knockback(attacker, damage)

        if (
            self.mode == "story"
            and attacker is self.player1
            and target is self.player2
            and bool(data.get("is_skill", False))
        ):
            self._damage_boss_domain(float(damage) * 1.25)

        if ps:
            ps.spawn_hit(
                target.rect.centerx,
                target.rect.centery,
                target.color,
            )

        if fs:
            col = (80, 200, 255) if data.get("is_skill") else (255, 220, 50)

            fs.spawn(
                target.rect.centerx,
                target.rect.top - 14,
                damage,
                col,
                is_skill=data.get("is_skill", False),
            )

        is_skill = bool(data.get("is_skill", False))
        skill_type = data.get("skill_type", None)

        # 기본공격은 1, 스킬은 종류별로 조절
        if is_skill:
            domain_charge = float(data.get("charge_value", 1.0))
            finisher_charge = float(data.get("finisher_charge_value", 1.0))
        else:
            domain_charge = 1.0
            finisher_charge = 1.0

        # 다단히트/투사체 밸런스용 기본값
        if skill_type == "projectile":
            domain_charge *= 0.7
            finisher_charge *= 0.7
        elif skill_type == "summon_zone":
            domain_charge *= 1.3
            finisher_charge *= 1.2
        elif skill_type == "beam":
            domain_charge *= 1.0
            finisher_charge *= 1.0

        if hasattr(attacker, "gain_domain_charge"):
            attacker.gain_domain_charge(domain_charge)
        if hasattr(attacker, "gain_finisher_charge"):
            attacker.gain_finisher_charge(finisher_charge)

        print(
            f"[HIT DEBUG] attacker={getattr(attacker, 'name', '?')} "
            f"target={getattr(target, 'name', '?')} "
            f"is_skill={is_skill} "
            f"domain={getattr(attacker, 'domain_charge_stack', 'NO_ATTR')} "
            f"finisher={getattr(attacker, 'finisher_charge_stack', 'NO_ATTR')}"
        )

    def _on_entity_dead(self, _data):
        if self.finisher_sys and self.finisher_sys.active:
            return
        self._check_result()

    # ─────────────────────────────────────────────
    # 결과 판정
    # ─────────────────────────────────────────────
    def _check_result(self):
        p1_dead = self.player1.dead and self.player1.stocks <= 0
        p2_dead = self.player2.dead and self.player2.stocks <= 0

        if not p1_dead and not p2_dead:
            return

        if self.mode == "pvp":
            if p1_dead:
                self.winner_name = "Player 2"
                self.winner_color = self.player2.glow_color
                self.result = "p2_win"

            elif p2_dead:
                self.winner_name = "Player 1"
                self.winner_color = self.player1.glow_color
                self.result = "p1_win"

        elif self.mode == "story":
            if p1_dead:
                self.result = "p1_dead"

            elif p2_dead:
                self.result = "p2_dead"

    # ─────────────────────────────────────────────
    # 렌더링
    # ─────────────────────────────────────────────
    def _draw_game(self):
        if self.domain_sys:
            self.domain_sys.draw_background()
        else:
            self.renderer.draw_background()

        if hasattr(self.player2, "draw_background_layer"):
            self.player2.draw_background_layer(self.screen, self.camera)

        self.renderer.draw_platforms(self.platforms, self.camera)

        self.particle_sys.draw(self.screen, self.camera)

        self.player1.draw(self.screen, self.camera)
        self.player2.draw(self.screen, self.camera)

        self.floater_sys.draw(self.screen, self.camera)

        if self.finisher_sys:
            self.finisher_sys.draw_overlay()

        self.renderer.draw_hud([self.player1, self.player2])

        if self.mode == "story":
            self._draw_story_boss_ui()

    def _draw_story_boss_ui(self):
        boss = self.player2
        player = self.player1
        W = self.screen.get_width()

        hp = max(0.0, float(getattr(boss, "hp", 0.0)))
        max_hp = max(1.0, float(getattr(boss, "max_hp", 1.0)))
        ratio = max(0.0, min(1.0, hp / max_hp))

        x, y, bw, bh = 260, 54, W - 520, 20
        pygame.draw.rect(self.screen, (14, 10, 20), (x, y, bw, bh), border_radius=8)
        if ratio > 0:
            fill_col = (225, 62, 74) if ratio > 0.2 else (255, 122, 68)
            pygame.draw.rect(self.screen, fill_col, (x, y, int(bw * ratio), bh), border_radius=8)
        pygame.draw.rect(self.screen, (255, 185, 165), (x, y, bw, bh), 1, border_radius=8)

        name_f = font(18, bold=True)
        sm_f = font(13, bold=True)
        boss_key = getattr(boss, "profile_key", "boss")
        name = name_f.render(
            f"{boss.name}  [{boss_key}]  PHASE {getattr(boss, 'phase', 1)}",
            True,
            (255, 210, 200),
        )
        self.screen.blit(name, (x, y - 28))
        hp_txt = sm_f.render(f"{int(hp)} / {int(max_hp)}", True, (245, 230, 225))
        self.screen.blit(hp_txt, (x + bw - hp_txt.get_width(), y - 22))

        if self.boss_domain_started and not self.boss_domain_broken:
            if getattr(boss, "domain_active", False) and not getattr(player, "domain_active", False):
                text = self._counter_domain_status_text()
                col = (255, 210, 120)
            elif getattr(boss, "domain_active", False) and getattr(player, "domain_active", False):
                dhp = max(0.0, getattr(boss, "boss_domain_hp", 0.0))
                dmax = max(1.0, getattr(boss, "boss_domain_max_hp", 1.0))
                text = f"Double Domain  |  Boss Domain HP {int(dhp)} / {int(dmax)}"
                col = (120, 235, 255)
            else:
                text = self.story_state.replace("_", " ")
                col = (205, 205, 225)

            status = sm_f.render(text, True, col)
            self.screen.blit(status, (W // 2 - status.get_width() // 2, y + 30))

        if self.story_message_timer > 0 and self.story_message:
            alpha = min(220, int(220 * self.story_message_timer / 45)) if self.story_message_timer < 45 else 220
            msg = font(24, bold=True).render(self.story_message, True, (255, 245, 220))
            bg = pygame.Surface((msg.get_width() + 34, msg.get_height() + 18), pygame.SRCALPHA)
            bg.fill((0, 0, 0, alpha // 2))
            pygame.draw.rect(bg, (255, 220, 160, alpha), bg.get_rect(), 1, border_radius=8)
            bg.blit(msg, (17, 9))
            self.screen.blit(bg, (W // 2 - bg.get_width() // 2, 96))
