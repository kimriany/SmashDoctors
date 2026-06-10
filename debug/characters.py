"""Character lookup for debug launchers."""
from __future__ import annotations

from entities.characters.Pita import Pita
from entities.characters.Nobel import Nobel
from entities.characters.Einstein import Einstein
from entities.characters.Schrödinger import Schrödinger
from entities.characters.Turing import Turing
from entities.characters.Hoking import Hoking
from entities.characters.Curie import Curie

CHARACTERS = {
    "pita": Pita,
    "pythagoras": Pita,
    "nobel": Nobel,
    "einstein": Einstein,
    "schrodinger": Schrödinger,
    "schrödinger": Schrödinger,
    "turing": Turing,
    "hoking": Hoking,
    "hawking": Hoking,
    "curie": Curie,
}


def get_character(name: str):
    key = name.strip().lower()
    if key not in CHARACTERS:
        known = ", ".join(sorted(CHARACTERS))
        raise SystemExit(f"Unknown character '{name}'. Known: {known}")
    return CHARACTERS[key]
