import requests
import unicodedata

CANALES_URL = "https://raw.githubusercontent.com/gastonledesma328-dot/agendascrap/refs/heads/main/canales%20(8).json"


def normalizar_texto(texto):
    texto = texto.lower()
    texto = unicodedata.normalize("NFD", texto)
    texto = texto.encode("ascii", "ignore").decode("utf-8")
    texto = texto.replace("+", "")
    texto = texto.replace(" ", "")
    return texto


def cargar_canales():
    r = requests.get(CANALES_URL, timeout=10)
    r.raise_for_status()
    return r.json()


def buscar_canal_propio(nombre_detectado):
    canales = cargar_canales()

    nombre_detectado = normalizar_texto(nombre_detectado)

    for canal in canales:
        if nombre_detectado in normalizar_texto(canal["name"]):
            return canal["streamUrl"]

    return None
