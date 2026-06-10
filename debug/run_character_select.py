"""Run CharacterSelect scene directly."""
from common import run_scene, make_screen
from scenes.character_select import CharacterSelect


def main():
    screen = make_screen("Character Select Scene")
    run_scene(CharacterSelect(screen), "Character Select Scene")


if __name__ == "__main__":
    main()
