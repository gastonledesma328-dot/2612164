import requests
import json
import re
from datetime import datetime, timedelta, timezone

OUTPUT_FILE = "agenda_espn.json"

ESPN_API = "https://site.api.espn.com/apis/site/v2/sports/soccer/all/scoreboard"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json,text/plain,*/*",
    "Referer": "https://www.espn.com.ar/futbol/calendario",
}


def fecha_argentina():
    return datetime.now(timezone(timedelta(hours=-3)))


def obtener_eventos(fecha=None):
    if fecha is None:
        fecha = fecha_argentina()

    params = {
        "region": "ar",
        "lang": "es",
        "dates": fecha.strftime("%Y%m%d"),
        "limit": 500,
    }

    r = requests.get(ESPN_API, headers=HEADERS, params=params, timeout=25)
    r.raise_for_status()
    return r.json()


def limpiar_slug_competicion(slug):
    if not slug:
        return None

    texto = slug.lower()

    # Borra años tipo:
    # 2025-
    # 2025-26-
    # 2026-
    texto = re.sub(r"^\d{4}(-\d{2})?-", "", texto)

    reemplazos = {
        "english-premier-league": "Premier League",
        "spanish-laliga": "LaLiga",
        "italian-serie-a": "Serie A",
        "german-bundesliga": "Bundesliga",
        "french-ligue-1": "Ligue 1",
        "uefa-champions-league": "UEFA Champions League",
        "uefa-europa-league": "UEFA Europa League",
        "uefa-europa-conference-league": "UEFA Conference League",
        "conmebol-libertadores": "CONMEBOL Libertadores",
        "conmebol-sudamericana": "CONMEBOL Sudamericana",
        "argentine-liga-profesional": "Liga Profesional Argentina",
        "argentine-primera-nacional": "Primera Nacional Argentina",
        "brazilian-serie-a": "Brasileirão",
        "mls": "MLS",
        "fifa-world-cup": "Mundial FIFA",
        "fifa-world-cup-qualifying-conmebol": "Eliminatorias CONMEBOL",
        "fifa-world-cup-qualifying-uefa": "Eliminatorias UEFA",
        "fifa-world-cup-qualifying-concacaf": "Eliminatorias CONCACAF",
    }

    if texto in reemplazos:
        return reemplazos[texto]

    return texto.replace("-", " ").title()


def obtener_liga(evento, competencia):
    temporada = evento.get("season") or {}

    posibles_ligas = [
        competencia.get("league") or {},
        evento.get("league") or {},
    ]

    for liga in posibles_ligas:
        nombre = (
            liga.get("displayName")
            or liga.get("name")
            or liga.get("shortName")
            or liga.get("abbreviation")
        )

        if nombre and nombre.lower() not in ["soccer", "fútbol", "all"]:
            return {
                "liga": nombre,
                "liga_corta": liga.get("shortName") or liga.get("abbreviation") or nombre,
                "liga_id": liga.get("id"),
                "liga_slug": liga.get("slug"),
                "temporada": temporada.get("year"),
                "temporada_slug": temporada.get("slug"),
            }

    # Fallback importante para ESPN soccer/all
    temporada_slug = temporada.get("slug")
    nombre_desde_slug = limpiar_slug_competicion(temporada_slug)

    if nombre_desde_slug:
        return {
            "liga": nombre_desde_slug,
            "liga_corta": nombre_desde_slug,
            "liga_id": None,
            "liga_slug": None,
            "temporada": temporada.get("year"),
            "temporada_slug": temporada_slug,
        }

    return {
        "liga": "Sin competición",
        "liga_corta": "Sin competición",
        "liga_id": None,
        "liga_slug": None,
        "temporada": temporada.get("year"),
        "temporada_slug": temporada.get("slug"),
    }


def limpiar_evento(evento):
    competencia = (evento.get("competitions") or [{}])[0]
    competidores = competencia.get("competitors") or []

    local = None
    visitante = None
    local_logo = None
    visitante_logo = None

    for c in competidores:
        equipo = c.get("team") or {}

        nombre = (
            equipo.get("displayName")
            or equipo.get("shortDisplayName")
            or equipo.get("name")
        )

        logos = equipo.get("logos") or []
        logo = logos[0].get("href") if logos else None

        if c.get("homeAway") == "home":
            local = nombre
            local_logo = logo
        elif c.get("homeAway") == "away":
            visitante = nombre
            visitante_logo = logo

    fecha_utc = evento.get("date")
    fecha_arg = None
    hora_arg = None

    if fecha_utc:
        dt = datetime.fromisoformat(fecha_utc.replace("Z", "+00:00"))
        dt_arg = dt.astimezone(timezone(timedelta(hours=-3)))
        fecha_arg = dt_arg.strftime("%Y-%m-%d")
        hora_arg = dt_arg.strftime("%H:%M")

    estado = (competencia.get("status") or {}).get("type") or {}
    liga_data = obtener_liga(evento, competencia)

    links = evento.get("links") or []
    url_espn = links[0].get("href") if links else None

    return {
        "id": evento.get("id"),
        "partido": f"{local} vs {visitante}" if local and visitante else evento.get("name"),

        "local": local,
        "visitante": visitante,
        "local_logo": local_logo,
        "visitante_logo": visitante_logo,

        "liga": liga_data["liga"],
        "liga_corta": liga_data["liga_corta"],
        "liga_id": liga_data["liga_id"],
        "liga_slug": liga_data["liga_slug"],

        "competicion": {
            "nombre": liga_data["liga"],
            "nombre_corto": liga_data["liga_corta"],
            "id": liga_data["liga_id"],
            "slug": liga_data["liga_slug"],
            "temporada": liga_data["temporada"],
            "temporada_slug": liga_data["temporada_slug"],
        },

        "fecha": fecha_arg,
        "hora": hora_arg,
        "estado": estado.get("description"),
        "estado_corto": estado.get("shortDetail"),

        "fecha_espn": fecha_utc,
        "url_espn": url_espn,
    }


def scrapear_partidos():
    data = obtener_eventos()
    eventos = data.get("events") or []

    resultados = []

    for evento in eventos:
        item = limpiar_evento(evento)

        if item["local"] and item["visitante"]:
            resultados.append(item)

    resultados.sort(
        key=lambda x: (
            x["fecha"] or "",
            x["hora"] or "",
            x["liga"] or "",
            x["partido"] or "",
        )
    )

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
