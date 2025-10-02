import openmeteo_requests
from openmeteo_sdk.Variable import Variable
import requests
import os
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta
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
    f"Napisz wiadomość przeznaczoną dla {receiver} na podstawie poniższej prognozy pogody. "
    "Opisz jaka jest obecnie pogoda."
    f"Skoncentruj się na tym, jak {receiver} powinna się ubrać. "
)

current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

current_date = datetime.now()

om = openmeteo_requests.Client()

current_params = {
    "latitude": latitude,
    "longitude": longitude,
    "current": [
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


def get_current_weather(parameters):
    responses = om.weather_api(
        "https://api.open-meteo.com/v1/forecast", params=parameters
    )
    response = responses[0]

    # Current values
    current = response.Current()
    current_variables = list(
        map(lambda i: current.Variables(i), range(0, current.VariablesLength()))
    )
    current_temperature_2m = next(
        filter(
            lambda x: x.Variable() == Variable.temperature and x.Altitude() == 2,
            current_variables,
        )
    )
    current_relative_humidity_2m = next(
        filter(
            lambda x: x.Variable() == Variable.relative_humidity and x.Altitude() == 2,
            current_variables,
        )
    )

    current_precipitation = next(
        filter(
            lambda x: x.Variable() == Variable.precipitation,
            current_variables,
        )
    )

    current_wind_speed_10m = next(
        filter(
            lambda x: x.Variable() == Variable.wind_speed and x.Altitude() == 10,
            current_variables,
        )
    )

    current_cloud_cover = next(
        filter(
            lambda x: x.Variable() == Variable.cloud_cover,
            current_variables,
        )
    )

    current_apparent_temperature = next(
        filter(
            lambda x: x.Variable() == Variable.apparent_temperature,
            current_variables,
        )
    )

    current_precipitation_probability = next(
        filter(
            lambda x: x.Variable() == Variable.precipitation_probability,
            current_variables,
        )
    )

    forecast_dict = {
        "temperature": round(current_temperature_2m.Value(), 2),
        "humidity": current_relative_humidity_2m.Value(),
        "precipitation": current_precipitation.Value(),
        "wind_speed": round(current_wind_speed_10m.Value(), 2),
        "cloud_cover": round(current_cloud_cover.Value(), 2),
        "apparent_temperature": round(current_apparent_temperature.Value(), 2),
        "precipitation_probability": round(
            current_precipitation_probability.Value(), 2
        ),
    }

    return forecast_dict


def describe_current_forecast():
    client = genai.Client(api_key=gemini_api_key)
    forecast = get_current_weather(current_params)
    prompt = current_forecast_to_text(forecast)
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash", contents=prompt
        )
        return response.text
    except errors.ServerError as server_error:
        fallback_message_if_error = (
            "Prognoza nie mogła zostac wygenerowana z powodu błędu Gemini AI"
        )
        print(f"Server error code: {server_error.code}")
        print(f"Server error message: {server_error.message}")
        send_ntfy(fallback_message_if_error)
        return None


def current_forecast_to_text(forecast):
    text = f"{current_datetime}\n{greeting}\nAktualna temperatura wynosi {forecast['temperature']}°C"

    if forecast["apparent_temperature"] != forecast["temperature"]:
        text += f", ale temperatura odczuwalna to {forecast['apparent_temperature']}°C"

    text += f". Wilgotność wynosi {forecast['humidity']}%, "
    text += f"zachmurzenie {forecast['cloud_cover']}%, "
    text += f"wiatr wieje z prędkością {forecast['wind_speed']} km/h"

    if forecast["precipitation_probability"] > 50:
        text += f", a prawdopodobieństwo opadów to {forecast['precipitation_probability']}% — możliwy deszcz"
    else:
        text += f", prawdopodobieństwo opadów jest niewielkie ({forecast['precipitation_probability']}%)"

    if forecast["precipitation"] > 0:
        text += f". Obecnie pada — opad: {forecast['precipitation']} mm"

    text += "."

    return text


def send_ntfy(prompt):
    requests.post(
        ntfy_channel,
        headers={"Markdown": "yes", "Title": "Aktualna pogoda", "Tags": "thermometer"},
        data=prompt.encode(encoding="utf-8"),
    )


if __name__ == "__main__":
    weather_result = describe_current_forecast()
    if weather_result is not None:
        send_ntfy(weather_result)
