import requests
from result import Result


def handle(ctx, user_input: str) -> Result:
    print("🔍 Localisation en cours...")
    try:
        data = requests.get("https://ipinfo.io/json", timeout=5).json()
        lines = [
            f"🌍 IP : {data.get('ip', 'Inconnue')}",
            f"📍 Ville : {data.get('city', 'Inconnue')}",
            f"🗺️  Région : {data.get('region', 'Inconnue')}",
            f"🇺🇳 Pays : {data.get('country', 'Inconnu')}",
            f"🛰️  Coordonnées : {data.get('loc', 'Inconnues')}",
            f"🏢 Fournisseur : {data.get('org', 'Inconnu')}",
        ]
        return Result.success("\n".join(lines))
    except requests.RequestException:
        return Result.error("❌ Erreur de connexion à l'API.")
