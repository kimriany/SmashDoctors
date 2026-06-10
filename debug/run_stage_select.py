"""Run StageSelect scene directly."""
from common import run_scene, make_screen
from scenes.stage_select import StageSelect


def main():
    screen = make_screen("Stage Select Scene")
    run_scene(StageSelect(screen), "Stage Select Scene")


if __name__ == "__main__":
    main()
