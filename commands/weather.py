import requests
from result import Result


def _wc_emoji(code: int) -> tuple[str, str]:
    table = {
        0:  ("☀️",      "Ciel dégagé"),
        1:  ("🌤️",     "Plutôt clair"),
        2:  ("⛅",      "Partiellement nuageux"),
        3:  ("☁️",      "Couvert"),
        45: ("🌫️",     "Brouillard"),
        48: ("🌫️",     "Brouillard givrant"),
        51: ("🌦️",     "Bruine faible"),
        53: ("🌦️",     "Bruine"),
        55: ("🌦️",     "Bruine forte"),
        61: ("🌦️",     "Pluie faible"),
        63: ("🌧️",     "Pluie"),
        65: ("🌧️",     "Pluie forte"),
        66: ("🌧️❄️",  "Pluie verglaçante faible"),
        67: ("🌧️❄️",  "Pluie verglaçante forte"),
        71: ("❄️",      "Neige faible"),
        73: ("❄️",      "Neige"),
        75: ("❄️",      "Neige forte"),
        77: ("🌨️",     "Grains de neige"),
        80: ("🌦️",     "Averses faibles"),
        81: ("🌧️",     "Averses"),
        82: ("🌧️🌧️", "Averses fortes"),
        85: ("🌨️",     "Averses de neige faibles"),
        86: ("🌨️",     "Averses de neige fortes"),
        95: ("⛈️",      "Orage"),
        96: ("⛈️",      "Orage avec grêle"),
        99: ("⛈️",      "Orage avec forte grêle"),
    }
    return table.get(code, ("❓", "Inconnu"))


def handle(ctx, user_input: str) -> Result:
    print("⛅ Météo en cours...")
    try:
        loc = requests.get("https://ipinfo.io/json", timeout=5).json()
        lat, lon = loc["loc"].split(",")
        city = loc.get("city", "Inconnue")

        params = {"latitude": lat, "longitude": lon, "current_weather": "true"}
        data = requests.get(
            "https://api.open-meteo.com/v1/forecast", params=params, timeout=5
        ).json()
        current = data["current_weather"]

        emoji, desc = _wc_emoji(current["weathercode"])
        lines = [
            f"📍 {city}",
            f"{emoji} {desc}",
            f"🌡️  {current['temperature']}°C",
            f"💨 {current['windspeed']} km/h",
        ]
        return Result.success("\n".join(lines))
    except (requests.RequestException, KeyError):
        return Result.error("❌ Impossible de récupérer la météo.")
