from systems.skill import Skill


class JobSystem:
    '''
    과학자 Job 시스템용 파일.

    예시:
    - Newton: 중력 스킬
    - Tesla: 전기 스킬
    - Einstein: 시간/공간 계열 스킬

    실제 구현에서는 player.job에 따라 player.skills를 교체하면 된다.
    '''

    @staticmethod
    def apply_job(player, job_name):
        player.job = job_name

        if job_name == "newton":
            player.skills = {
                "skill_1": Skill("Gravity Push", damage=18, fatigue_cost=20, cooldown=80),
                "skill_2": Skill("Apple Drop", damage=25, fatigue_cost=35, cooldown=130),
            }

        elif job_name == "tesla":
            player.skills = {
                "skill_1": Skill("Electric Shock", damage=16, fatigue_cost=20, cooldown=70),
                "skill_2": Skill("Lightning Field", damage=28, fatigue_cost=40, cooldown=150),
            }

        else:
            player.skills = {
                "skill_1": Skill("Energy Burst", damage=20, fatigue_cost=25, cooldown=90),
            }
