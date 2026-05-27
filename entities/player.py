import pygame

from settings import PLAYER_SPEED, PLAYER_JUMP_POWER
from entities.base_entity import BaseEntity
from systems.skill import Skill


class Player(BaseEntity):
    def __init__(self, x, y, name="Player"):
        super().__init__(x, y, 44, 64, name)

        self.color = (90, 170, 255)

        self.max_fatigue = 100
        self.fatigue = 0

        self.job = "default"

        # 스킬은 나중에 과학자 job에 따라 교체 가능
        self.skills = {
            "skill_1": Skill(
                name="Energy Burst",
                damage=20,
                fatigue_cost=25,
                cooldown=90,
            )
        }

    def handle_input(self, keys):
        if self.dead:
            return

        moving = False

        if keys[pygame.K_a]:
            self.vel.x = -PLAYER_SPEED
            self.facing = -1
            moving = True

        if keys[pygame.K_d]:
            self.vel.x = PLAYER_SPEED
            self.facing = 1
            moving = True

        if not moving:
            self.vel.x *= 0.75
            if abs(self.vel.x) < 0.2:
                self.vel.x = 0

    def handle_keydown(self, key, event_bus):
        if self.dead:
            return

        if key == pygame.K_w:
            self.jump()

        if key == pygame.K_f:
            self.start_attack()

        if key == pygame.K_g:
            self.use_skill("skill_1", event_bus)

    def jump(self):
        if self.on_ground:
            self.vel.y = PLAYER_JUMP_POWER

    def use_skill(self, skill_key, event_bus):
        skill = self.skills.get(skill_key)
        if skill is None:
            return

        if skill.can_use(self.fatigue):
            skill.use()
            self.fatigue += skill.fatigue_cost

            # 실제 이펙트, 투사체, 광역 공격은 이 이벤트를 받아서 구현
            event_bus.emit(
                "skill_used",
                {
                    "user": self,
                    "skill": skill,
                },
            )

            # 임시로 스킬을 강한 공격으로 처리
            self.attack_damage = skill.damage
            self.start_attack()
            self.attack_damage = 10

    def update(self, dt, platforms, event_bus):
        super().update(dt, platforms, event_bus)

        # 피로도는 시간이 지나면 천천히 회복
        if self.fatigue > 0:
            self.fatigue -= 0.25
            self.fatigue = max(0, int(self.fatigue))

        for skill in self.skills.values():
            skill.update()
