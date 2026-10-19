
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
from dotenv import load_dotenv

# --------------------------------------------------
# Configuration
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
MENU_FILE = BASE_DIR / "menu.json"

load_dotenv(BASE_DIR / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

TZ_NAME = os.getenv("TIMEZONE", "Asia/Kolkata")
TZ = ZoneInfo(TZ_NAME)

REMINDERS = {
    "07:30": "breakfast",
    "12:00": "lunch",
    "16:30": "snacks",
    "19:30": "dinner",
}


# --------------------------------------------------
# Menu functions
# --------------------------------------------------

def load_menu():
    """Load the weekly menu from menu.json."""
    if not MENU_FILE.exists():
        raise FileNotFoundError(
            f"Menu file not found: {MENU_FILE}"
        )

    with MENU_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def format_menu(items):
    """Convert menu items into a WhatsApp-friendly string."""
    if not items:
        return "Menu not added yet. Check the hostel mess notice."

    if isinstance(items, list):
        text = ", ".join(str(item) for item in items)
    else:
        text = str(items)

    # Keep the template variable reasonably short.
    return text[:900]


# --------------------------------------------------
# WhatsApp Cloud API
# --------------------------------------------------

def send_template_message(to_number, meal, day, items):
    """Send a personalized meal reminder using the approved template."""

    token = os.getenv("WHATSAPP_ACCESS_TOKEN")
    phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
    api_version = os.getenv("WHATSAPP_API_VERSION", "v23.0")
    template_name = os.getenv(
        "WHATSAPP_TEMPLATE_NAME",
        "mess_meal_reminder",
    )
    template_language = os.getenv(
        "WHATSAPP_TEMPLATE_LANGUAGE",
        "en",
    )

    if not token:
        raise RuntimeError(
            "WHATSAPP_ACCESS_TOKEN is missing from .env"
        )

    if not phone_number_id:
        raise RuntimeError(
            "WHATSAPP_PHONE_NUMBER_ID is missing from .env"
        )

    if not to_number:
        raise RuntimeError("WhatsApp recipient number is missing.")

    url = (
        f"https://graph.facebook.com/"
        f"{api_version}/{phone_number_id}/messages"
    )

    menu_text = format_menu(items)

    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {
                "code": template_language,
            },
            "components": [
                {
                    "type": "body",
                    "parameters": [
                        {
                            "type": "text",
                            "text": meal.title(),
                        },
                        {
                            "type": "text",
                            "text": day.lower(),
                        },
                        {
                            "type": "text",
                            "text": menu_text,
                        },
                    ],
                },
            ],
        },
    }

    try:
        response = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=20,
        )

        try:
            result = response.json()
        except ValueError:
            result = {"response": response.text}

        if not response.ok:
            error = result.get("error", result)

            logging.error(
                "WhatsApp API failed (HTTP %s): %s",
                response.status_code,
                json.dumps(error),
            )
            return False

        message_id = (
            result.get("messages", [{}])[0].get("id", "unknown")
        )

        logging.info(
            "Meta accepted the reminder request. Message ID: %s",
            message_id,
        )
        print("Reminder request accepted by Meta.")
        print(f"Meal: {meal.title()}")
        print(f"Day: {day}")
        print(f"Menu: {menu_text}")
        print("Check WhatsApp for the message.")

        return True

    except requests.RequestException as exc:
        logging.error("WhatsApp network/request error: %s", exc)
        return False


# --------------------------------------------------
# Reminder execution
# --------------------------------------------------

def run_once(now=None, force_meal=None, dry_run=False):
    """Send a reminder if one is due, or test a selected meal."""

    now = now or datetime.now(TZ)
    menu_data = load_menu()

    day = now.strftime("%A")
    local_time = now.strftime("%H:%M")
    meal = force_meal or REMINDERS.get(local_time)

    if not meal:
        logging.info(
            "No reminder due at %s %s. Nothing sent.",
            day,
            local_time,
        )
        return

    items = (
        menu_data.get("days", {})
        .get(day, {})
        .get(meal, [])
    )

    if dry_run:
        print(
            f"[DRY RUN] {day} {local_time} — "
            f"{meal.title()}: {format_menu(items)}"
        )
        return

    recipient = os.getenv("WHATSAPP_TO", "").strip()

    if not recipient:
        raise RuntimeError("WHATSAPP_TO is missing from .env")

    send_template_message(
        recipient,
        meal,
        day,
        items,
    )


# --------------------------------------------------
# Command-line interface
# --------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="SRM KTR hostel mess WhatsApp reminders"
    )

    parser.add_argument(
        "--test",
        action="store_true",
        help="Print the menu without sending a WhatsApp message",
    )

    parser.add_argument(
        "--meal",
        choices=["breakfast", "lunch", "snacks", "dinner"],
        help="Choose a meal to test or send immediately",
    )

    args = parser.parse_args()

    run_once(
        force_meal=args.meal,
        dry_run=args.test,
    )
