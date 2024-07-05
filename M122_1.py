import openmeteo_requests
import requests_cache
import pandas as pd
from retry_requests import retry
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from Password import AppPassword

# Einrichten des Open-Meteo API-Clients mit Cache und Fehlerwiederholung
cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)

# Sicherstellen, dass alle benötigten Wettervariablen hier aufgeführt sind
# Die Reihenfolge der Variablen in hourly oder daily ist wichtig, um sie unten korrekt zuzuordnen
url = "https://api.open-meteo.com/v1/forecast"
params = {
    "latitude": 47.376888,
    "longitude": 8.541694,
    "current": ["temperature_2m", "relative_humidity_2m", "precipitation", "rain", "wind_speed_10m"],
    "daily": ["temperature_2m_max", "temperature_2m_min", "rain_sum"],
    "timezone": "Europe/Berlin"
}
responses = openmeteo.weather_api(url, params=params)


# Verarbeite den ersten Standort. Füge eine Schleife für mehrere Standorte oder Wettermodelle hinzu
response = responses[0]


# Aktuelle Werte. Die Reihenfolge der Variablen muss dieselbe sein wie angefordert.
current = response.Current()
current_temperature_2m = current.Variables(0).Value()
current_relative_humidity_2m = current.Variables(1).Value()
current_precipitation = current.Variables(2).Value()
current_rain = current.Variables(3).Value()
current_wind_speed_10m = current.Variables(4).Value()



# Verarbeite die täglichen Daten. Die Reihenfolge der Variablen muss dieselbe sein wie angefordert.
daily = response.Daily()
daily_temperature_2m_max = daily.Variables(0).ValuesAsNumpy()
daily_temperature_2m_min = daily.Variables(1).ValuesAsNumpy()
daily_rain_sum = daily.Variables(2).ValuesAsNumpy()



daily_data = {
    "Datum": pd.date_range(
        start=pd.to_datetime(daily.Time(), unit="s", utc=True),
        end=pd.to_datetime(daily.TimeEnd(), unit="s", utc=True),
        freq=pd.Timedelta(seconds=daily.Interval()),
        inclusive="left"
    )
}

 

daily_data["temperature_2m_max"] = daily_temperature_2m_max
daily_data["temperature_2m_min"] = daily_temperature_2m_min
daily_data["rain_sum"] = daily_rain_sum


daily_dataframe = pd.DataFrame(data=daily_data)

# E-Mail-Inhalt vorbereiten
email_content = f"""
Koordinaten: {response.Latitude()}°N {response.Longitude()}°E
Höhe: {response.Elevation()} m über dem Meeresspiegel


Aktuelle Temperatur (2m): {current_temperature_2m}
Aktuelle relative Luftfeuchtigkeit (2m): {current_relative_humidity_2m}
Aktuelle Niederschläge: {current_precipitation}
Aktueller Regen: {current_rain}
Aktuelle Windgeschwindigkeit (10m): {current_wind_speed_10m}

Tägliche Daten:
{daily_dataframe.to_string(index=False)}
"""

# E-Mail-Einstellungen
sender_email = "m122apiweather@gmail.com"
receiver_email = "diinisberisha@gmail.com"
password = AppPassword # Ersetze dies durch das generierte App-Passwort

# E-Mail erstellen
msg = MIMEMultipart()
msg["From"] = sender_email
msg["To"] = receiver_email
msg["Subject"] = "Tägliches Wetterupdate"

msg.attach(MIMEText(email_content, "plain"))

# E-Mail senden
try:
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        print("E-Mail erfolgreich gesendet")
except Exception as e:
    print(f"Fehler beim Senden der E-Mail: {e}")
