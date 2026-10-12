# JVRWall

A FamilyWall-style family dashboard for Home Assistant, designed for wall tablets. HACS-compatible custom integration plus a large-touch-target Lovelace card.

## Features
- **Meal planner** – local weekly plan (breakfast/lunch/dinner per day).
- **Shopping list** – add, check off, remove, clear checked.
- **Chores / to-dos** – optional assignee and due date, completion tracking.
- **Calendar** – read-only family view of any Home Assistant `calendar` entities (e.g. the built-in **Google Calendar** integration).

Data is stored locally in HA storage and exposed as sensors:
`sensor.jvrwall_meal_plan`, `sensor.jvrwall_shopping_list`, `sensor.jvrwall_chores`, `sensor.jvrwall_family_calendars` (state = count; full data in attributes).

## Install
1. HACS → Custom repositories → add `Whitewolfza/JVRWall` (category *Integration*) → install, restart Home Assistant.
2. First set up the core **Google Calendar** integration (Settings → Devices & services) so your calendars exist as `calendar.*` entities.
3. Settings → Devices & services → Add integration → **JVRWall**; pick calendars and enter family member names (editable later via *Configure*).
4. The card resource is registered automatically. Add it to a dashboard (use a panel/single-card view for a tablet):
   ```yaml
   type: custom:jvrwall-card
   # optional overrides:
   # calendars: [calendar.family]
   ```

## Services (`jvrwall.*`)
`set_meal`, `add_shopping_item`, `check_shopping_item`, `remove_shopping_item`, `clear_checked_shopping`, `add_chore`, `update_chore`, `complete_chore`, `remove_chore`. Item IDs are visible in the sensor attributes. See `services.yaml`.

## Development
`pip install pytest && pytest` runs the data-model tests (no Home Assistant needed).
