"""Home Assistant independent data model for JVRWall."""
from __future__ import annotations

from typing import Any
from uuid import uuid4

from .const import DAYS, MEAL_SLOTS


class JVRWallData:
    """Holds meals, shopping items and chores, and mutates them."""

    def __init__(self, data: dict[str, Any] | None = None) -> None:
        data = data or {}
        self.meals: dict[str, dict[str, str]] = data.get("meals", {})
        self.shopping: list[dict[str, Any]] = data.get("shopping", [])
        self.chores: list[dict[str, Any]] = data.get("chores", [])

    def as_dict(self) -> dict[str, Any]:
        return {
            "meals": self.meals,
            "shopping": self.shopping,
            "chores": self.chores,
        }

    # Meals
    def set_meal(self, day: str, meal: str, slot: str = "dinner") -> None:
        day = day.lower()
        if day not in DAYS:
            raise ValueError(f"Invalid day: {day}")
        if slot not in MEAL_SLOTS:
            raise ValueError(f"Invalid slot: {slot}")
        if meal.strip():
            self.meals.setdefault(day, {})[slot] = meal.strip()
        else:
            self.meals.get(day, {}).pop(slot, None)

    def week_plan(self) -> dict[str, dict[str, str]]:
        return {d: dict(self.meals.get(d, {})) for d in DAYS}

    # Shopping
    def add_shopping_item(self, name: str) -> dict[str, Any]:
        if not name.strip():
            raise ValueError("Item name is required")
        item = {"id": uuid4().hex, "name": name.strip(), "checked": False}
        self.shopping.append(item)
        return item

    def _find(self, items: list[dict[str, Any]], item_id: str) -> dict[str, Any]:
        for item in items:
            if item["id"] == item_id:
                return item
        raise KeyError(item_id)

    def set_shopping_checked(self, item_id: str, checked: bool) -> None:
        self._find(self.shopping, item_id)["checked"] = checked

    def remove_shopping_item(self, item_id: str) -> None:
        self.shopping.remove(self._find(self.shopping, item_id))

    def clear_checked_shopping(self) -> None:
        self.shopping = [i for i in self.shopping if not i["checked"]]

    # Chores / todos
    def add_chore(
        self, title: str, assignee: str | None = None, due: str | None = None
    ) -> dict[str, Any]:
        if not title.strip():
            raise ValueError("Title is required")
        chore = {
            "id": uuid4().hex,
            "title": title.strip(),
            "assignee": assignee or None,
            "due": due or None,
            "done": False,
        }
        self.chores.append(chore)
        return chore

    def update_chore(self, chore_id: str, **fields: Any) -> None:
        chore = self._find(self.chores, chore_id)
        for key in ("title", "assignee", "due"):
            if fields.get(key) is not None:
                chore[key] = fields[key] or None

    def set_chore_done(self, chore_id: str, done: bool) -> None:
        self._find(self.chores, chore_id)["done"] = done

    def remove_chore(self, chore_id: str) -> None:
        self.chores.remove(self._find(self.chores, chore_id))
