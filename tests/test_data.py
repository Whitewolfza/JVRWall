import importlib.util
import sys
import types
from pathlib import Path

base = Path(__file__).parent.parent / "custom_components" / "jvrwall"
pkg = types.ModuleType("jvrwall")
pkg.__path__ = [str(base)]
sys.modules["jvrwall"] = pkg
for name in ("const", "data"):
    spec = importlib.util.spec_from_file_location(f"jvrwall.{name}", base / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[f"jvrwall.{name}"] = mod
    spec.loader.exec_module(mod)

import pytest  # noqa: E402
from jvrwall.data import JVRWallData  # noqa: E402


def test_meals():
    d = JVRWallData()
    d.set_meal("Monday", "Pasta")
    assert d.week_plan()["monday"] == {"dinner": "Pasta"}
    d.set_meal("monday", "", "dinner")
    assert d.week_plan()["monday"] == {}
    with pytest.raises(ValueError):
        d.set_meal("funday", "x")


def test_shopping():
    d = JVRWallData()
    i = d.add_shopping_item(" Milk ")
    assert i["name"] == "Milk"
    d.set_shopping_checked(i["id"], True)
    d.clear_checked_shopping()
    assert d.shopping == []
    with pytest.raises(KeyError):
        d.remove_shopping_item("nope")


def test_chores_roundtrip():
    d = JVRWallData()
    c = d.add_chore("Dishes", "Sam")
    d.set_chore_done(c["id"], True)
    d.update_chore(c["id"], assignee="Alex")
    d2 = JVRWallData(d.as_dict())
    assert d2.chores[0]["done"] and d2.chores[0]["assignee"] == "Alex"
    d2.remove_chore(c["id"])
    assert d2.chores == []


def test_recipes():
    d = JVRWallData()
    r = d.add_recipe("Pie", "https://facebook.com/x", "yum", "facebook-share")
    assert d.as_dict()["recipes"][0]["url"] == "https://facebook.com/x"
    assert d.add_recipe("", "https://a.b")["name"] == "https://a.b"
    with pytest.raises(ValueError):
        d.add_recipe("x", "javascript:alert(1)")
    with pytest.raises(ValueError):
        d.add_recipe("")
    d.remove_recipe(r["id"])
    assert len(d.recipes) == 1
