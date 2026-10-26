"""Home Assistant independent data model for JVRWall."""
from __future__ import annotations

from datetime import datetime, timezone
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
        self.recipes: list[dict[str, Any]] = data.get("recipes", [])
        self.balances: dict[str, dict[str, int]] = data.get("balances", {})
        for chore in self.chores:  # migrate items stored before rewards existed
            chore["reward_minutes"] = int(chore.get("reward_minutes") or 0)
            chore["reward_points"] = int(chore.get("reward_points") or 0)
            chore.setdefault("rewarded", False)

    def as_dict(self) -> dict[str, Any]:
        return {
            "meals": self.meals,
            "shopping": self.shopping,
            "chores": self.chores,
            "recipes": self.recipes,
            "balances": self.balances,
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
        self,
        title: str,
        assignee: str | None = None,
        due: str | None = None,
        reward_minutes: int = 0,
        reward_points: int = 0,
    ) -> dict[str, Any]:
        if not title.strip():
            raise ValueError("Title is required")
        if reward_minutes < 0 or reward_points < 0:
            raise ValueError("Rewards cannot be negative")
        chore = {
            "id": uuid4().hex,
            "title": title.strip(),
            "assignee": assignee or None,
            "due": due or None,
            "done": False,
            "reward_minutes": int(reward_minutes),
            "reward_points": int(reward_points),
            "rewarded": False,
        }
        self.chores.append(chore)
        return chore

    def update_chore(self, chore_id: str, **fields: Any) -> None:
        chore = self._find(self.chores, chore_id)
        for key in ("reward_minutes", "reward_points"):
            if fields.get(key) is not None and fields[key] < 0:
                raise ValueError("Rewards cannot be negative")
        for key in ("title", "assignee", "due"):
            if fields.get(key) is not None:
                chore[key] = fields[key] or None
        for key in ("reward_minutes", "reward_points"):
            if fields.get(key) is not None:
                chore[key] = int(fields[key])

    # Balances
    def balance(self, member: str) -> dict[str, int]:
        return self.balances.setdefault(member, {"minutes": 0, "points": 0})

    def _adjust(self, member: str, minutes: int, points: int) -> None:
        bal = self.balance(member)
        bal["minutes"] = max(0, bal["minutes"] + minutes)
        bal["points"] = max(0, bal["points"] + points)

    def set_chore_done(self, chore_id: str, done: bool) -> dict[str, Any] | None:
        """Mark a chore done/undone. Returns an event payload when a reward is granted."""
        chore = self._find(self.chores, chore_id)
        chore["done"] = done
        assignee = chore.get("assignee")
        minutes = chore.get("reward_minutes", 0)
        points = chore.get("reward_points", 0)
        if done and not chore.get("rewarded"):
            chore["rewarded"] = True
            if assignee:
                self._adjust(assignee, minutes, points)
            return {
                "chore_id": chore["id"],
                "chore_name": chore["title"],
                "assignee": assignee,
                "reward_minutes": minutes if assignee else 0,
                "reward_points": points if assignee else 0,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        if not done and chore.get("rewarded"):
            chore["rewarded"] = False
            if assignee:
                self._adjust(assignee, -minutes, -points)
        return None

    def redeem(self, member: str, minutes: int = 0, points: int = 0) -> dict[str, int]:
        if minutes < 0 or points < 0:
            raise ValueError("Redeem amounts cannot be negative")
        bal = self.balance(member)
        if minutes > bal["minutes"] or points > bal["points"]:
            raise ValueError("Insufficient balance")
        bal["minutes"] -= minutes
        bal["points"] -= points
        return bal

    def remove_chore(self, chore_id: str) -> None:
        self.chores.remove(self._find(self.chores, chore_id))

    # Recipes
    def add_recipe(
        self,
        name: str,
        url: str | None = None,
        notes: str | None = None,
        source: str | None = None,
    ) -> dict[str, Any]:
        name = (name or "").strip()
        url = (url or "").strip() or None
        if not name and url:
            name = url
        if not name:
            raise ValueError("Recipe name or url is required")
        if url and not url.lower().startswith(("http://", "https://")):
            raise ValueError("Recipe url must start with http:// or https://")
        recipe = {
            "id": uuid4().hex,
            "name": name,
            "url": url,
            "notes": (notes or "").strip() or None,
            "source": source or None,
        }
        self.recipes.append(recipe)
        return recipe

    def remove_recipe(self, recipe_id: str) -> None:
        self.recipes.remove(self._find(self.recipes, recipe_id))
