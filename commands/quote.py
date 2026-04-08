import requests
import random
from result import Result

_API_URL = "https://zenquotes.io/api/random"

_FALLBACK = [
    ("La vie, c'est comme une bicyclette, il faut avancer pour ne pas perdre l'équilibre.", "Albert Einstein"),
    ("Le succès, c'est d'aller d'échec en échec sans perdre son enthousiasme.", "Winston Churchill"),
    ("Celui qui déplace des montagnes commence par enlever de petites pierres.", "Confucius"),
    ("La seule façon de faire du bon travail est d'aimer ce que vous faites.", "Steve Jobs"),
    ("Un voyage de mille lieues commence toujours par un premier pas.", "Lao Tseu"),
    ("Ce n'est pas parce que les choses sont difficiles que nous n'osons pas. C'est parce que nous n'osons pas qu'elles sont difficiles.", "Sénèque"),
    ("Il n'y a pas de vent favorable pour celui qui ne sait pas où il va.", "Sénèque"),
]


def handle(ctx, user_input: str) -> Result:
    try:
        data = requests.get(_API_URL, timeout=5).json()
        text = data[0]["q"]
        author = data[0]["a"]
    except (requests.RequestException, KeyError, IndexError):
        text, author = random.choice(_FALLBACK)

    return Result.success(f"💬 « {text} »\n    — {author}")
