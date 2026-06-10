"""Run StoryStageSelect scene directly."""
from common import run_scene, make_screen
from scenes.story_stage_select import StoryStageSelect
from systems.story_save import StorySave
from systems.story_loader import StoryLoader


def main():
    screen = make_screen("Story Stage Select Scene")
    run_scene(StoryStageSelect(screen, StorySave(), StoryLoader()), "Story Stage Select Scene")


if __name__ == "__main__":
    main()
