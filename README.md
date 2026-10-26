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
`set_meal`, `add_shopping_item`, `check_shopping_item`, `remove_shopping_item`, `clear_checked_shopping`, `add_chore`, `update_chore`, `complete_chore`, `redeem_reward`, `remove_chore`. Item IDs are visible in the sensor attributes. See `services.yaml`.

## Recipes & companion share app
Recipes live in `sensor.jvrwall_recipes` (services `add_recipe`, `remove_recipe`) and in the card's **Recipes** tab.

The integration also serves an installable companion web app (PWA) at `https://<your-ha>/jvrwall/companion/index.html`:
1. Open that URL on your Android phone in Chrome, tap **Install app** / *Add to Home screen*.
2. In the app's Settings enter your HA URL and a long-lived access token (Profile → Security).
3. In Facebook, tap **Share** on a post → pick **JVR Recipes**. Review the name/link and tap **Save recipe**.

**Import saved posts:** Facebook offers no API for saved posts (and scraping is against its terms). Instead, request *Download your information → Saved items and collections* as JSON, open the companion app → **Import saved posts**, choose the file, review the recipe-like items that were pre-selected, and add them all at once.

### Mobile app (.NET MAUI – Android & iOS)
`companion-maui/` contains a native MAUI app (`dotnet build companion-maui -f net8.0-android`; needs the `maui` workload).
- **Android:** appears in Facebook's Share sheet as *JVR Recipes*; review and save.
- **iOS:** use *Paste from clipboard* (Share → Copy link in Facebook); a real Share Extension needs a separate Xcode-signed target.
- **Import saved posts:** pick the Facebook "Saved items and collections" JSON export; recipe-like items are pre-selected.
- Settings: HTTPS Home Assistant URL + long-lived token (kept in SecureStorage).

Requires HTTPS access to Home Assistant (needed for PWA install/share target).

## Development
`pip install pytest && pytest` runs the data-model tests (no Home Assistant needed).


## Chore rewards

Chores accept `assignee`, `reward_minutes` and `reward_points` (both default 0). Existing stored chores are migrated automatically with 0 rewards.

```yaml
service: jvrwall.add_chore
data: {title: Do dishes, assignee: Sam, reward_minutes: 15, reward_points: 5}
```

### Balances
Completing a chore (`jvrwall.complete_chore`) adds its rewards to the assignee's balance once (re-completing does nothing; un-completing reverts it). Balances are stored with the other JVRWall data and exposed as sensors per member (members configured in the integration options, plus anyone who has earned a reward): `sensor.jvrwall_<member>_xbox_minutes` and `sensor.jvrwall_<member>_points`. After granting time in the Xbox app, subtract it with `jvrwall.redeem_reward` (`member`, `minutes`, `points`) or the **Redeem** button on the card's Chores tab.

### Event
`jvrwall_chore_completed` is fired on completion with:
`chore_id`, `chore_name`, `assignee`, `reward_minutes`, `reward_points`, `timestamp` (ISO 8601 UTC).

### Example automation
The Xbox Family app has no public API, so granting time is still a manual step; the notification just opens the app.

```yaml
alias: "Chore Completed: Grant Xbox Time"
trigger:
  - platform: event
    event_type: jvrwall_chore_completed
condition:
  - condition: template
    value_template: "{{ trigger.event.data.reward_minutes | int > 0 }}"
action:
  - service: notify.mobile_app_your_phone
    data:
      title: "Chore Completed! 🎮"
      message: "{{ trigger.event.data.assignee }} finished {{ trigger.event.data.chore_name }}. Add {{ trigger.event.data.reward_minutes }} min of Xbox time."
      data:
        url: "ms-xbox-family-settings://"            # iOS (unverified, please test)
        clickAction: "app://com.microsoft.xboxfamilysettings"  # Android (verify package name)
mode: parallel
```
