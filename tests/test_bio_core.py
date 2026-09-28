"""Structure checks for the data-resolved bio-core exploratory spec."""
from __future__ import annotations

from snntopo import runner
from snntopo.data import steinmetz


def test_bio_core_expands_whole_regions_and_disjoint_half_controls(monkeypatch):
    spec = runner.load_spec("sweeps/bio_core.py")
    monkeypatch.setattr(steinmetz, "list_sessions", lambda: [str(i) for i in range(13)])
    monkeypatch.setattr(steinmetz, "_session_data", lambda session: {
        "brain_area": __import__("numpy").array(["root"] * 5 + ["VISp"] * 50),
    })
    monkeypatch.setattr(steinmetz, "trial_arrays", lambda session, block: {
        "block": __import__("numpy").array([block] * 6),
        "response": __import__("numpy").array([1, -1, 0, 0, 1, -1]),
    })

    recipes, pairs = spec.expand()

    # Per session: 3 whole populations, 3 region populations, and two halves for each.
    assert len(recipes) == 13 * 12
    assert len(pairs) == 13 * 3
    assert {recipe["units"]["area"] for recipe in recipes if recipe["units"]["area"]} == {"VISp"}
    assert all(recipe["units"]["area"] != "root" for recipe in recipes)
    assert {pair["h"] for pair in pairs} == {1, 2, 3}
    assert all(pair["condition"] == "all" and pair["seeds"] == [0] for pair in pairs)
    assert all(pair["a"]["units"]["split"]["half"] == 0 for pair in pairs)
    assert all(pair["b"]["units"]["split"]["half"] == 1 for pair in pairs)
