"""Constants for JVRWall."""

DOMAIN = "jvrwall"
STORAGE_KEY = "jvrwall.data"
STORAGE_VERSION = 1
SIGNAL_UPDATED = "jvrwall_updated"
EVENT_CHORE_COMPLETED = "jvrwall_chore_completed"

CONF_CALENDARS = "calendars"
CONF_MEMBERS = "members"

DAYS = [
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
]
MEAL_SLOTS = ["breakfast", "lunch", "dinner"]

CARD_URL = "/jvrwall/jvrwall-card.js"
COMPANION_URL = "/jvrwall/companion"
