import requests
import unicodedata
from flask import Flask, jsonify
from datetime import datetime

app = Flask(__name__)

STREAMTP10_JSON = "https://streamtp10.com/eventos.json"
CANALES_URL = "https://raw.githubusercontent.com/gastonledesma328-dot/agendascrap/main/canales%20(8).json"


def normalizar(texto):
    if not texto:
        return ""
    texto = texto.lower()
    texto = unicodedata.normalize("NFD", texto)
    return texto.encode("ascii", "ignore").decode("utf-8")


def cargar_json(url):
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    return r.json()


@app.route("/agenda")
def agenda():
    eventos = cargar_json(STREAMTP10_JSON)
    canales = cargar_json(CANALES_URL)

    resultado = {}

    for ev in eventos.get("eventos", []):
        titulo = ev.get("event-name") or ev.get("titulo") or ""
        hora = ev.get("hora", "")
        canal = ev.get("canal", "")
        link_evento = ev.get("iframe") or ev.get("link") or ""

        link_final = link_evento

        for c in canales:
            if normalizar(c["name"]) in normalizar(canal):
                link_final = c["streamUrl"]
                break

        liga = ev.get("liga", "Eventos")

        partido = {
            "partido": titulo,
            "hora": hora,
            "canal": canal,
            "link": link_final
        }

        resultado.setdefault(liga, []).append(partido)

    return jsonify(resultado)


@app.route("/")
def home():
    return "Agenda Tole API activa"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
