import openmeteo_requests
from openmeteo_sdk.Variable import Variable
import requests
import os
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta
import time
from google import genai
from google.genai import errors
import pandas as pd

load_dotenv()
gemini_api_key = os.getenv("GEMINI_API_KEY")
receiver = os.getenv("RECEIVER")
ntfy_channel = os.getenv("NTFY_CHANNEL")

latitude = os.getenv("LATITUDE")
longitude = os.getenv("LONGITUDE")
greeting = (
    f"Napisz wiadomość przeznaczoną dla {receiver} na podstawie poniższych prognoz pogody. "
    "Opisz te prognozy."
    f"Skoncentruj się na tym, jak {receiver} powinna się ubrać."
    "Użyj markdown, aby zaznaczyć najważniejsze informacje."
    "Wiadomość ma nie przekraczać 1300 znaków."
)

current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

current_date = datetime.now()

om = openmeteo_requests.Client()

tomorrow_date_str = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%d")

tomorrow_params = {
    "latitude": latitude,
    "longitude": longitude,
    "hourly": [
        "temperature_2m",
        "relative_humidity_2m",
        "precipitation",
        "wind_speed_10m",
        "cloud_cover",
        "apparent_temperature",
        "precipitation_probability",
    ],
    "timezone": os.getenv("TIMEZONE"),

}


def get_evening_and_tomorrow_weather(parameters):
    responses = om.weather_api(
        "https://api.open-meteo.com/v1/forecast", params=parameters
    )
    response = responses[0]
    hourly = response.Hourly()

    start_ts = hourly.Time()
    end_ts = hourly.TimeEnd()
    interval = hourly.Interval()

    # datetimes UTC
    datetimes = pd.date_range(
        start=pd.to_datetime(start_ts, unit="s", utc=True),
        end=pd.to_datetime(end_ts, unit="s", utc=True),
        freq=pd.Timedelta(seconds=interval),
        inclusive="left",
    )

    now_utc = datetime.now(timezone.utc)
    today_18 = now_utc.replace(hour=18, minute=0, second=0, microsecond=0)

    tomorrow_07 = now_utc.replace(hour=7, minute=0, second=0, microsecond=0) + timedelta(days=1)

    try:
        index_18 = datetimes.get_indexer([today_18], method="nearest")[0]
        index_07 = datetimes.get_indexer([tomorrow_07], method="nearest")[0]
    except IndexError:
        raise ValueError("Brak prognozy na dziś 18:00 lub jutro 07:00.")

    variable_map = {
        "temperature": Variable.temperature,
        "humidity": Variable.relative_humidity,
        "precipitation": Variable.precipitation,
        "wind_speed": Variable.wind_speed,
        "cloud_cover": Variable.cloud_cover,
        "apparent_temperature": Variable.apparent_temperature,
        "precipitation_probability": Variable.precipitation_probability,
    }

    hourly_variables = [hourly.Variables(i) for i in range(hourly.VariablesLength())]

    def build_forecast(index):
        forecast = {}
        for name, variable_type in variable_map.items():
            match = [
                v for v in hourly_variables
                if v.Variable() == variable_type and (v.Altitude() in (2, 10) or v.Altitude() == 0)
            ]
            if match:
                forecast[name] = round(match[0].Values(index), 2)
        return forecast

    forecast_18 = build_forecast(index_18)
    forecast_07 = build_forecast(index_07)

    # print(f"[DEBUG] today_18: {today_18} -> {datetimes[index_18]}")
    # print(f"[DEBUG] tomorrow_07: {tomorrow_07} -> {datetimes[index_07]}")
    # print(f"[DEBUG] forecast_18: {forecast_18}")
    # print(f"[DEBUG] forecast_07: {forecast_07}")

    return forecast_18, forecast_07


def describe_tomorrow_forecast():
    client = genai.Client(api_key=gemini_api_key)
    forecast_18, forecast_07 = get_evening_and_tomorrow_weather(tomorrow_params)

    if not forecast_18 or not forecast_07:
        fallback_message = "Brak danych pogodowych na dziś 18:00 lub jutro 07:00"
        print(fallback_message)
        send_ntfy(fallback_message)
        return None

    prompt = evening_and_tomorrow_forecast_to_text(forecast_18, forecast_07)

    max_retries = 3
    base_delay = 60

    for attempt in range(1, max_retries + 1):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash", contents=prompt
            )
            return response.text

        except errors.ServerError as server_error:
            print(f"Attempt {attempt}/{max_retries} — Gemini AI error")
            print(f"Server error code: {server_error.code}")
            print(f"Server error message: {server_error.message}")

            if attempt < max_retries:
                retry_delay = base_delay * (2 ** (attempt - 1))
                print(f"Waiting {retry_delay} seconds until retrying...")
                time.sleep(retry_delay)
            else:
                fallback_message_if_error = (
                    "Prognoza nie mogła zostać wygenerowana po 3 próbach — błąd Gemini AI"
                )
                send_ntfy(fallback_message_if_error)
                return None
    return None


def evening_and_tomorrow_forecast_to_text(forecast_today_18, forecast_tomorrow_07):
    text = f"{current_datetime}\n{greeting}\n"

    def format_block(forecast, hour_label):
        block = f"\n{hour_label} — temperatura {forecast['temperature']}°C"
        if forecast["apparent_temperature"] != forecast["temperature"]:
            block += f", odczuwalna {forecast['apparent_temperature']}°C"

        block += f", wilgotność {forecast['humidity']}%, "
        block += f"zachmurzenie {forecast['cloud_cover']}%, "
        block += f"wiatr {forecast['wind_speed']} km/h"

        if forecast["precipitation_probability"] > 50:
            block += f", możliwe opady ({forecast['precipitation_probability']}%)"
        else:
            block += (
                f", małe szanse na opady ({forecast['precipitation_probability']}%)"
            )

        if forecast["precipitation"] > 0:
            block += f", prognozowany opad: {forecast['precipitation']} mm"

        block += "."
        return block

    text += format_block(forecast_today_18, "18:00 dziś")
    text += format_block(forecast_tomorrow_07, "07:00 jutro")

    return text


def send_ntfy(prompt):
    requests.post(
        ntfy_channel,
        headers={
            "Markdown": "yes",
            "Title": "Prognoza pogody (dzisiaj 18:00 i rano 07:00)",
            "Tags": "city_sunrise",
        },
        data=prompt.encode(encoding="utf-8"),
    )


if __name__ == "__main__":
    weather_result = describe_tomorrow_forecast()
    if weather_result is not None:
        send_ntfy(weather_result)