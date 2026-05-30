# Telegram Gemini AI Chatbot

Async Telegram chatbot built with `python-telegram-bot`, Google Gemini, and per-chat conversation memory.

## Features

- Works in private chats and groups
- In groups, responds only when mentioned or when someone replies to the bot
- `/start`, `/help`, and `/reset`
- Per-chat conversation memory
- Typing indicator while Gemini generates
- Markdown responses with plain-text fallback
- Automatic splitting for long Telegram messages
- Logging and error handling
- Secrets loaded from `.env`

## Project Structure

```text
.
+-- bot/
|   +-- config.py
|   +-- gemini.py
|   +-- handlers.py
|   +-- memory.py
|   +-- telegram_utils.py
+-- .env.example
+-- main.py
+-- README.md
+-- requirements.txt
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

Use `/reset` in any chat to clear that chat's memory.

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

## Deployment on Render Web Service

1. Push this project to GitHub.
2. Create a new **Web Service** on Render.
3. Connect the GitHub repo.
4. Set the runtime to Python 3.
5. Add environment variables:
   - `TELEGRAM_BOT_TOKEN`
   - `GEMINI_API_KEY`
   - `BOT_MODE=webhook`
   - `WEBHOOK_URL=https://your-render-service-name.onrender.com`
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

## Polling Deployment

For paid background workers or VPS hosting, you can keep polling mode:

```env
BOT_MODE=polling
```

or leave `BOT_MODE` unset. Then run:

```bash
python main.py
```

## Notes

- Conversation memory is in memory only. Restarting the bot clears it.
- Free web services may sleep when idle. If the service sleeps, the first Telegram message after idle time can be delayed while the app wakes up.
- The default Gemini model is `gemini-2.5-flash`. You can override it with:

```env
GEMINI_MODEL=gemini-2.5-flash
```
