import argparse
import os

import requests
from dotenv import load_dotenv


def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(description="Point Telegram webhook to Vercel.")
    parser.add_argument("base_url", help="Example: https://your-app.vercel.app")
    parser.add_argument("--path", default="api", help="Webhook path on Vercel")
    args = parser.parse_args()

    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    secret_token = os.getenv("WEBHOOK_SECRET_TOKEN", "").strip()
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is required")

    webhook_url = f"{args.base_url.rstrip('/')}/{args.path.strip('/')}"
    payload = {
        "url": webhook_url,
        "allowed_updates": ["message"],
        "drop_pending_updates": False,
    }
    if secret_token:
        payload["secret_token"] = secret_token

    response = requests.post(
        f"https://api.telegram.org/bot{token}/setWebhook",
        json=payload,
        timeout=30,
    )
    response.raise_for_status()
    print(response.json())


if __name__ == "__main__":
    main()
