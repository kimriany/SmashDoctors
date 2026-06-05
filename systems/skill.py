class Skill:
    def __init__(self, name, damage, fatigue_cost, cooldown):
        self.name = name
        self.damage = damage
        self.fatigue_cost = fatigue_cost
        self.cooldown = cooldown
        self.current_cooldown = 0

    def can_use(self, current_fatigue):
        if self.current_cooldown > 0:
            return False

        if current_fatigue + self.fatigue_cost > 100:
            return False

        return True

    def use(self):
        self.current_cooldown = self.cooldown

    def update(self):
        if self.current_cooldown > 0:
            self.current_cooldown -= 1

class Ultimate_Skill(Skill):
    def __init__(self, name, damage, fatigue_cost, cooldown):
        self.name = name
        self.damage = damage
        self.fatigue_cost = fatigue_cost
        


class CC_Skill(Skill):
    def __init__(self, name, damage, fatigue_cost, cooldown):
        self.name = name
        self.damage = damage
        self.fatigue_cost = fatigue_cost



class Enchance_Skill(Skill):
    def __init__(self, name, damage, fatigue_cost, cooldown):
        self.name = name
        self.damage = damage
        self.fatigue_cost = fatigue_cost
