"""Start directly at story stage select, skipping opening/mode/story intro."""
from common import run_game_object, make_screen
from modes.story_game import StoryGame, StoryState


def main():
    screen = make_screen("Story Stage Select")
    game = StoryGame(screen)
    game.state = StoryState.STAGE_SELECT
    run_game_object(game, "Story Stage Select")


if __name__ == "__main__":
    main()
