from entities.base_entity import BaseEntity


class Boss(BaseEntity):
    def __init__(self, x, y, name="Boss"):
        super().__init__(x, y, 70, 90, name)

        self.color = (230, 90, 90)
        self.hp = 200

        self.ai_timer = 0
        self.attack_range = 120

    def update(self, dt, platforms, event_bus):
        if self.dead:
            return

        self.ai_timer += 1
        self.basic_ai()

        super().update(dt, platforms, event_bus)

    def basic_ai(self):
        # 임시 자동 움직임:
        # 일정 시간마다 좌우 이동 방향을 바꿈
        if self.ai_timer % 180 < 90:
            self.vel.x = -2.2
            self.facing = -1
        else:
            self.vel.x = 2.2
            self.facing = 1

        # 일정 주기로 공격
        if self.ai_timer % 120 == 0:
            self.start_attack()
