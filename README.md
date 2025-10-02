# Weather Messenger Bot ☀️🌧️🧥

This Python bot generates a personalized weather forecasts messages with clothing recommendations for **today 18:00, tomorrow 06:00, 07: 00 and 11:00 (should be combined with cron jobs**. It uses [Open-Meteo](https://open-meteo.com/) for weather data and [Google Gemini AI](https://ai.google.dev/) for natural language generation.

The final message is sent as a notification using [ntfy.sh](https://ntfy.sh).

---

## ✨ Features

- Fetches hourly weather forecast:
  - This evening (closest hour after 18:00 today)
  - Tomorrow (06:00, 07:00, 11:00)
- Analyzes temperature, apparent temperature, wind, humidity, precipitation, etc.
- Generates a friendly message with outfit suggestions.
- Handles Gemini AI server errors with retry logic.
- Sends the final message via ntfy.sh.

---

## 🧠 Technologies

- Python 3
- [openmeteo-requests](https://pypi.org/project/openmeteo-requests/)
- Google Gemini API (`google.generativeai`)
- [ntfy.sh](https://ntfy.sh)

---

## 🚀 Setup

### 1. Clone the repo:

```bash
git clone https://github.com/yourusername/weather-messenger-bot.git
cd weather-messenger-bot
```

### 2. Create a `.env` file:

```env
GEMINI_API_KEY=<your_google_api_key>
RECEIVER=<receiver_name>
LATITUDE=<your_latitude>
LONGITUDE=<your_longitude>
TIMEZONE=<your_timezone>
NTFY_CHANNEL=https://ntfy.sh/<your-channel-name>
```

### 3. Create and activate a virtual environment:

**On Linux/macOS:**

```bash
python3 -m venv venv
source venv/bin/activate
```

**On Windows (PowerShell):**

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 4. Install dependencies:

```bash
pip install -r requirements.txt
```

---

## ▶️ Running the script

Scripts are divided by use case:

- `current.py` — current weather summary
- `four_pm.py` — to be run around 16:00; gives forecast for **today at 18:00 and tomorrow at 07:00**
- `nine_pm.py` — (optional) for late-night forecast

Example run:

```bash
python four_pm.py
```

---

## 📅 Automation

Recommended use with `cron`:

```bash
0 16 * * * /home/damian/weather-bot/venv/bin/python /home/damian/weather-bot/four_pm.py
```

---

## 🛡️ Gemini AI error handling

If Gemini AI returns a `ServerError`, the bot will:
- retry up to 3 times,
- wait with exponential backoff between attempts,
- send a fallback notification if all attempts fail.

---

## 📬 Notification

The generated message is pushed to your ntfy.sh channel. You can receive it:
- on mobile (ntfy app),
- via web browser,
- or integrate it with your workflow.

---

## 📂 Project structure

```bash
weather-bot/
├── current.py
├── four_pm.py
├── nine_pm.py
├── .env
├── .gitignore
├── requirements.txt
└── README.md
```

