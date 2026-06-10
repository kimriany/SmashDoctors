"""Start directly at PVP character select."""
from common import run_game_object, make_screen
from modes.pvp_game import PVPGame


def main():
    screen = make_screen("PVP Character Select")
    run_game_object(PVPGame(screen), "PVP Character Select")


if __name__ == "__main__":
    main()
