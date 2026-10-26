"""Sensors exposing JVRWall data to Lovelace and automations."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_CALENDARS, CONF_MEMBERS, DOMAIN, SIGNAL_UPDATED


class _Base(SensorEntity):
    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, manager, entry: ConfigEntry, key: str, name: str) -> None:
        self._manager = manager
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_name = name

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            async_dispatcher_connect(self.hass, SIGNAL_UPDATED, self._refresh)
        )

    @callback
    def _refresh(self) -> None:
        self.async_write_ha_state()


class MealPlanSensor(_Base):
    @property
    def native_value(self) -> int:
        return sum(len(v) for v in self._manager.data.meals.values())

    @property
    def extra_state_attributes(self):
        return {"plan": self._manager.data.week_plan()}


class ShoppingSensor(_Base):
    @property
    def native_value(self) -> int:
        return sum(1 for i in self._manager.data.shopping if not i["checked"])

    @property
    def extra_state_attributes(self):
        return {"items": self._manager.data.shopping}


class ChoresSensor(_Base):
    @property
    def native_value(self) -> int:
        return sum(1 for c in self._manager.data.chores if not c["done"])

    @property
    def extra_state_attributes(self):
        return {
            "chores": self._manager.data.chores,
            "balances": self._manager.data.balances,
            "members": list(self._entry.options.get(CONF_MEMBERS, [])),
        }


class BalanceSensor(_Base):
    """Per-member Xbox minutes or points balance."""

    _attr_state_class = "total"

    def __init__(self, manager, entry, member: str, kind: str) -> None:
        super().__init__(
            manager,
            entry,
            f"{member}_{kind}",
            f"{member} {'Xbox minutes' if kind == 'minutes' else 'points'}",
        )
        self._member = member
        self._kind = kind
        if kind == "minutes":
            self._attr_native_unit_of_measurement = "min"

    @property
    def native_value(self) -> int:
        return self._manager.data.balances.get(self._member, {}).get(self._kind, 0)

    @property
    def extra_state_attributes(self):
        return {"member": self._member}


class RecipesSensor(_Base):
    @property
    def native_value(self) -> int:
        return len(self._manager.data.recipes)

    @property
    def extra_state_attributes(self):
        return {"recipes": self._manager.data.recipes}


class ConfigSensor(_Base):
    """Exposes configured calendars so the card can auto-discover them."""

    @property
    def native_value(self) -> int:
        return len(self._entry.options.get(CONF_CALENDARS, []))

    @property
    def extra_state_attributes(self):
        return {"calendars": list(self._entry.options.get(CONF_CALENDARS, []))}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    manager = hass.data[DOMAIN][entry.entry_id]
    members = list(entry.options.get(CONF_MEMBERS, []))
    for m in manager.data.balances:
        if m not in members:
            members.append(m)
    balance_sensors = [
        BalanceSensor(manager, entry, m, kind)
        for m in members
        for kind in ("minutes", "points")
    ]
    async_add_entities(
        balance_sensors
        + [
            MealPlanSensor(manager, entry, "meals", "Meal plan"),
            ShoppingSensor(manager, entry, "shopping", "Shopping list"),
            ChoresSensor(manager, entry, "chores", "Chores"),
            RecipesSensor(manager, entry, "recipes", "Recipes"),
            ConfigSensor(manager, entry, "calendars", "Family calendars"),
        ]
    )
