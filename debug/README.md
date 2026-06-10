# Debug Launchers

Run from the project root:

```bash
python debug/run_pvp.py
python debug/run_story.py
python debug/run_battle.py --p1 curie --p2 hoking --stage 1
python debug/run_story_scene.py --stage 0
```

Mode-level launchers:
- `run_pvp.py`: opens PVP character select directly.
- `run_story.py`: skips main menu and story intro, opens story stage select directly.
- `run_battle.py`: starts a battle immediately with chosen characters and stage.
- `run_story_scene.py`: runs one visual-novel story script directly.

Scene-level launchers:
- `run_character_select.py`: character select only.
- `run_stage_select.py`: normal stage select only.
- `run_story_intro.py`: story intro only.
- `run_story_stage_select.py`: story chapter select only.

Examples:

```bash
python debug/run_battle.py --p1 schrodinger --p2 curie --stage 2
python debug/run_battle.py --p1 nobel --p2 hoking --stage 4
python debug/run_story_scene.py --script data/story/scripts/stage_04.json
```

Known character keys:
`pita`, `pythagoras`, `nobel`, `einstein`, `schrodinger`, `schrödinger`, `turing`, `hoking`, `hawking`, `curie`.
