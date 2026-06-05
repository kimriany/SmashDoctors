class Skill:
    def __init__(self, name, damage, fatigue_cost, cooldown=0, duration=30):
        self.name = name
        self.damage = damage
        self.fatigue_cost = fatigue_cost

        # None이면 쿨타임 없는 스킬
        self.cooldown = cooldown
        self.current_cooldown = 0

        self.duration = duration
        self.timer = 0
        self.has_hit = False

    @property
    def active(self):
        return self.timer > 0

    def has_cooldown(self):
        return self.cooldown is not None and self.cooldown > 0

    def can_use(self, owner):
        # 일반 쿨타임 검사
        if self.has_cooldown() and self.current_cooldown > 0:
            return False

        # 피로도 검사
        if owner.fatigue + self.fatigue_cost > owner.max_fatigue:
            return False

        # 스킬별 추가 조건
        if not self.can_activate(owner):
            return False

        return True

    def can_activate(self, owner):
        """
        스킬별 특수 발동 조건.
        일반 스킬은 기본적으로 항상 True.
        """
        return True

    def use(self, owner, event_bus=None, psys=None):
        if self.has_cooldown():
            self.current_cooldown = self.cooldown

        owner.fatigue = min(
            owner.max_fatigue,
            owner.fatigue + self.fatigue_cost
        )

        self.timer = self.duration
        self.has_hit = False

        self.on_start(owner, event_bus, psys)

    def update_cooldown(self):
        if self.has_cooldown() and self.current_cooldown > 0:
            self.current_cooldown -= 1

    def update_active(self, owner, event_bus=None, psys=None):
        if self.timer > 0:
            self.on_update(owner, event_bus, psys)
            self.timer -= 1

    def on_start(self, owner, event_bus=None, psys=None):
        pass

    def on_update(self, owner, event_bus=None, psys=None):
        pass

    def draw_behind(self, owner, screen, camera, dr, bob, z):
        pass

    def draw_front(self, owner, screen, camera, dr, bob, z):
        pass

    def get_hitbox(self, owner):
        return None

    def on_hit(self, owner, target, event_bus, psys=None, fsys=None):
        if self.has_hit:
            return

        self.has_hit = True

        event_bus.emit("attack_hit", {
            "attacker": owner,
            "target": target,
            "damage": self.damage,
            "is_skill": True,
            "particle_system": psys,
            "floater_system": fsys,
        })

class UltimateSkill(Skill):
    def __init__(self, name, damage, fatigue_cost=0, duration=60):
        super().__init__(
            name=name,
            damage=damage,
            fatigue_cost=fatigue_cost,
            cooldown=None,
            duration=duration
        )

    def can_activate(self, owner):
        # 예시 1: 궁극기 게이지가 100 이상일 때만 발동
        return getattr(owner, "ultimate_gauge", 0) >= 100

    def use(self, owner, event_bus=None, psys=None):
        # 쿨타임은 없고, 대신 궁극기 게이지를 소모
        owner.ultimate_gauge = 0

        self.timer = self.duration
        self.has_hit = False

        self.on_start(owner, event_bus, psys)

class CC_Skill(Skill):
    def __init__(self):
        super().__init__(
            name="Beam",
            damage=28,
            fatigue_cost=32,
            cooldown=100,
            duration=30
        )
