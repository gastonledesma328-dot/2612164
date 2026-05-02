import requests
import json
from datetime import datetime, timedelta, timezone

OUTPUT_FILE = "agenda_espn.json"

ESPN_API = "https://site.api.espn.com/apis/site/v2/sports/soccer/all/scoreboard"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json,text/plain,*/*",
    "Referer": "https://www.espn.com.ar/futbol/calendario",
}


def fecha_argentina():
    tz_arg = timezone(timedelta(hours=-3))
    return datetime.now(tz_arg)


def obtener_eventos(fecha=None):
    if fecha is None:
        fecha = fecha_argentina()

    fecha_api = fecha.strftime("%Y%m%d")

    params = {
        "region": "ar",
        "lang": "es",
        "dates": fecha_api,
        "limit": 300,
    }

    r = requests.get(
        ESPN_API,
        headers=HEADERS,
        params=params,
        timeout=20
    )
    r.raise_for_status()
    return r.json()


def limpiar_evento(evento):
    competencia = evento.get("competitions", [{}])[0]
    competidores = competencia.get("competitors", [])

    local = None
    visitante = None

    for c in competidores:
        equipo = c.get("team", {})
        nombre = equipo.get("displayName") or equipo.get("shortDisplayName")

        if c.get("homeAway") == "home":
            local = nombre
        elif c.get("homeAway") == "away":
            visitante = nombre

    liga = evento.get("league", {})
    estado = competencia.get("status", {}).get("type", {})

    fecha_utc = evento.get("date")
    hora_arg = None

    if fecha_utc:
        dt = datetime.fromisoformat(fecha_utc.replace("Z", "+00:00"))
        dt_arg = dt.astimezone(timezone(timedelta(hours=-3)))
        hora_arg = dt_arg.strftime("%H:%M")

    return {
        "id": evento.get("id"),
        "partido": f"{local} vs {visitante}" if local and visitante else evento.get("name"),
        "local": local,
        "visitante": visitante,
        "liga": liga.get("name") or liga.get("abbreviation"),
        "hora": hora_arg,
        "estado": estado.get("description"),
        "estado_corto": estado.get("shortDetail"),
        "fecha_espn": fecha_utc,
        "url_espn": evento.get("links", [{}])[0].get("href") if evento.get("links") else None,
    }


def scrapear_partidos():
    data = obtener_eventos()
    eventos = data.get("events", [])

    resultados = []

    for evento in eventos:
        item = limpiar_evento(evento)

        if item["local"] and item["visitante"]:
            resultados.append(item)

    return resultados


def guardar_json(data):
    salida = {
        "fuente": "ESPN Argentina",
        "fecha_scrapeo": fecha_argentina().isoformat(),
        "total": len(data),
        "partidos": data,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(salida, f, ensure_ascii=False, indent=2)


def main():
    print("Obteniendo agenda desde ESPN...")
    partidos = scrapear_partidos()
    guardar_json(partidos)

    print(f"OK: {len(partidos)} partidos guardados en {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
