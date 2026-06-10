"""Run one story script directly.

Usage:
    python debug/run_story_scene.py --stage 0
    python debug/run_story_scene.py --script data/story/scripts/stage_04.json
"""
from __future__ import annotations

import argparse

from common import run_scene, make_screen
from scenes.story_scene import StoryScene


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", type=int, default=0)
    parser.add_argument("--script", default=None)
    args = parser.parse_args()

    script = args.script or f"data/story/scripts/stage_{args.stage:02d}.json"
    screen = make_screen(f"Story Scene {script}")
    scene = StoryScene(screen, script)
    scene.script_data.setdefault("_total_stages", 6)
    scene.script_data.setdefault("_current_stage", args.stage)
    run_scene(scene, f"Story Scene {script}")


if __name__ == "__main__":
    main()
