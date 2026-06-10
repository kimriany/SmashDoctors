"""Run StoryIntro scene directly."""
from common import run_scene, make_screen
from scenes.story_intro import StoryIntro


def main():
    screen = make_screen("Story Intro Scene")
    run_scene(StoryIntro(screen), "Story Intro Scene")


if __name__ == "__main__":
    main()
