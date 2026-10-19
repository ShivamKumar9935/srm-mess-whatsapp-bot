# SRM KTR Mess WhatsApp Reminder Bot

A small Python bot that sends a WhatsApp Cloud API template at breakfast, lunch, snacks, and dinner times. Menu entries repeat by weekday, not by the date printed on the original menu.

## Schedule (Asia/Kolkata)
- Breakfast: 07:30
- Lunch: 12:00
- Evening snacks: 16:30
- Dinner: 19:30

The included Render Cron Job runs every 15 minutes in UTC. These four local times align to the UTC schedule.

## 1. Set up Meta WhatsApp Cloud API
1. Open the Meta for Developers dashboard and create an app with WhatsApp enabled.
2. In WhatsApp > API Setup, obtain a Phone Number ID and access token. For a real deployment, create a suitable long-lived/system-user token and keep it secret.
3. Add and verify your recipient number / opt-in as required by the account setup.
4. Create a message template in WhatsApp Manager and wait for approval.

Suggested template (body text):
`Hi! Your hostel mess reminder for {{1}} on {{2}}. Menu: {{3}}. Enjoy your meal!`

Use variables in this order:
1. Meal (Breakfast/Lunch/Snacks/Dinner)
2. Weekday
3. Menu text

Set the template name to `mess_meal_reminder` and language to `en_US`, or change the environment variables to match your approved template. Template category and approval are decided by Meta; don't assume this sample will be approved unchanged.

## 2. Update the menu
Edit `menu.json`. Each weekday has `breakfast`, `lunch`, `snacks`, and `dinner` arrays. Keep each item as a string. Empty arrays intentionally produce a message saying the menu has not been added yet. Only some lunch entries were available when this starter project was generated; verify and fill the remaining dishes rather than guessing.

## 3. Test locally
Python 3.10+ recommended.

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` with real values, then print a test without sending:
```bash
python main.py --test --meal lunch
```

Send a real test template (only after your template is approved and credentials are set):
```bash
python main.py --meal lunch
```

To test the current time slot without forcing a meal, run:
```bash
python main.py
```

## 4. Deploy to Render
1. Push this folder to a private GitHub repository.
2. In Render, create a new Cron Job from the repository or use the included `render.yaml`.
3. Add the environment variables from `.env.example` in Render's Environment settings. Never commit `.env` or a token.
4. Check the first run's logs. Render evaluates cron schedules in UTC, not IST.

The job runs every 15 minutes but only sends when the local clock exactly matches one of the four configured times. It should finish quickly; don't configure retries that can accidentally duplicate messages.

## Important WhatsApp rules
- Proactive scheduled messages outside the customer-service window generally need an approved template. This code sends a template rather than arbitrary free-form text.
- Only message a number that has opted in and follows WhatsApp Business Platform rules.
- Keep the access token private. If it leaks, revoke/rotate it in Meta.
- This starter sends reminders only. Incoming commands like `menu` require a public HTTPS webhook service and webhook verification, which can be added as a next step.
