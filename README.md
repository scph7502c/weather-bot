# Weather Messenger Bot ☀️🌧️🧥

This Python script generates a personalized weather message with clothing suggestions based on current weather conditions. It uses the [Open-Meteo](https://open-meteo.com/) API for weather data and [Gemini](https://ai.google.dev/) for natural language generation.

The generated message is sent via [ntfy.sh](https://ntfy.sh) as a notification.

## ✨ Features

- Retrieves current weather data: temperature, humidity, wind, precipitation, etc.
- Uses Gemini to create a natural-sounding message tailored to a specific person.
- Suggests how to dress based on the weather.
- Sends the message via ntfy notification service.

## 🧠 Technologies Used

- Python 3
- [openmeteo-requests](https://pypi.org/project/openmeteo-requests/)
- Google Gemini AI (via `google.genai`)
- ntfy.sh for push notifications

## 🚀 Setup

### 1. Clone the repo:

```bash
git clone https://github.com/yourusername/weather-messenger-bot.git
cd weather-messenger-bot
```

### 2. Create a .env file:

```bash
GEMINI_API_KEY=<your_google_api_key>
RECEIVER=<name_of_receiver>
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

```bash
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Run the script:

```bash
python weather_bot.py
```

## 📅 Scheduled Use

You can automate this script with a cron job, systemd timer, or other scheduler to send daily messages in the morning.
