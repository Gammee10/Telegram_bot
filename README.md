# Telegram Gemini AI Chatbot

Async Telegram chatbot built with `python-telegram-bot`, Google Gemini, and per-chat conversation memory.

## Features

- Works in private chats and groups
- In groups, responds only when mentioned or when someone replies to the bot
- `/start`, `/help`, and `/reset`
- Per-chat conversation memory
- Voice message support
- Typing indicator while Gemini generates
- Markdown responses with plain-text fallback
- Automatic splitting for long Telegram messages
- Logging and error handling
- Secrets loaded from `.env`

## Project Structure

```text
.
+-- bot/
|   +-- app_factory.py
|   +-- config.py
|   +-- gemini.py
|   +-- handlers.py
|   +-- memory.py
|   +-- telegram_utils.py
+-- api/
|   +-- webhook.py
+-- scripts/
|   +-- set_webhook.py
+-- .env.example
+-- main.py
+-- README.md
+-- requirements.txt
+-- vercel.json
```

## Requirements

- Python 3.11
- Telegram bot token from [BotFather](https://t.me/BotFather)
- Gemini API key from Google AI Studio

## Local Setup

1. Create and activate a virtual environment:

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create `.env` from the example:

```bash
cp .env.example .env
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

4. Fill in your secrets:

```env
TELEGRAM_BOT_TOKEN=your_telegram_token_here
GEMINI_API_KEY=your_gemini_api_key_here
```

5. Run the bot:

```bash
python main.py
```

## Group Behavior

In a group, the bot ignores normal chatter. It responds only when:

- A message mentions the bot, for example: `@BotName explain OOP`
- A user replies to one of the bot's messages, for example: `Can you explain more?`
- A voice message is sent as a reply to one of the bot's messages

Use `/reset` in any chat to clear that chat's memory.

## Voice Messages

In private chats, send a Telegram voice message and the bot will transcribe it with Gemini, remember the transcript, and reply conversationally.

In groups, voice messages are answered only when they are replies to the bot. This keeps normal group voice notes from triggering the bot by accident.

The default inline voice limit is about 14 MB. You can change it with:

```env
MAX_VOICE_BYTES=14680064
```

## Deployment on Railway

1. Push this project to GitHub.
2. Create a new Railway project and choose **Deploy from GitHub repo**.
3. Add environment variables in Railway:
   - `TELEGRAM_BOT_TOKEN`
   - `GEMINI_API_KEY`
4. Set the start command:

```bash
python main.py
```

5. Deploy. Railway will keep the polling process running.

## Deployment on Vercel

Vercel uses serverless functions, so this project exposes a Telegram webhook at:

```text
/api/webhook
```

1. Push this project to GitHub.
2. Go to Vercel and create a new project from the GitHub repo.
3. Keep the default framework setting as **Other** if Vercel asks.
4. Add environment variables:
   - `TELEGRAM_BOT_TOKEN`
   - `GEMINI_API_KEY`
   - `BOT_MODE=serverless`
   - `WEBHOOK_SECRET_TOKEN=any-long-random-string`
5. Deploy the project.
6. Copy your production Vercel URL, for example:

```text
https://your-project.vercel.app
```

7. Point Telegram to the Vercel webhook from your local terminal:

```bash
python scripts/set_webhook.py https://your-project.vercel.app
```

8. Check that Telegram accepted it:

```bash
python -c "import os, requests; from dotenv import load_dotenv; load_dotenv(); token=os.environ['TELEGRAM_BOT_TOKEN']; print(requests.get(f'https://api.telegram.org/bot{token}/getWebhookInfo').json())"
```

The webhook URL should end with:

```text
/api/webhook
```

### Persistent Memory on Vercel

Serverless memory is not guaranteed to last between requests. For reliable conversation history on Vercel, create a free Upstash Redis database and add these Vercel environment variables:

```env
UPSTASH_REDIS_REST_URL=your_upstash_rest_url
UPSTASH_REDIS_REST_TOKEN=your_upstash_rest_token
```

Without Upstash, the bot still replies, but conversation memory can reset when Vercel starts a fresh function instance.

## Deployment on Render Web Service

1. Push this project to GitHub.
2. Create a new **Web Service** on Render.
3. Connect the GitHub repo.
4. Set the runtime to Python 3.
5. Add environment variables:
   - `TELEGRAM_BOT_TOKEN`
   - `GEMINI_API_KEY`
   - `BOT_MODE=webhook`
   - `WEBHOOK_URL=https://your-actual-render-service-name.onrender.com`
   - `WEBHOOK_SECRET_TOKEN=any-long-random-string`
6. Set the build command:

```bash
pip install -r requirements.txt
```

7. Set the start command:

```bash
python main.py
```

8. Deploy the web service.

Render provides the `PORT` variable automatically. The bot uses that port and registers this Telegram webhook:

```text
https://your-render-service-name.onrender.com/telegram-webhook
```

If you change `WEBHOOK_PATH`, the final path changes too.

Do not use the example URL literally. Copy your real service URL from the Render dashboard. If `WEBHOOK_URL` is not set, the bot will try to use Render's automatic `RENDER_EXTERNAL_URL` variable.

## Polling Deployment

For paid background workers or VPS hosting, you can keep polling mode:

```env
BOT_MODE=polling
```

or leave `BOT_MODE` unset. Then run:

```bash
python main.py
```

## Turning Off Render

Only one webhook host should own the Telegram bot at a time. After moving to Vercel:

1. Open the Render dashboard.
2. Open the old bot service.
3. Go to **Settings**.
4. Choose **Suspend Service** or **Delete Service**.
5. Confirm the action.

Then run the Vercel webhook command again:

```bash
python scripts/set_webhook.py https://your-project.vercel.app
```

## Notes

- Conversation memory uses Upstash Redis when `UPSTASH_REDIS_REST_URL` and `UPSTASH_REDIS_REST_TOKEN` are set. Otherwise it falls back to in-memory storage.
- Free web services may sleep when idle. If the service sleeps, the first Telegram message after idle time can be delayed while the app wakes up.
- The default Gemini model is `gemini-2.5-flash`. You can override it with:

```env
GEMINI_MODEL=gemini-2.5-flash
```
