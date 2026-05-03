import requests
import json
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

OUTPUT_FILE = "agenda_espn.json"

ESPN_API_BASE = "https://site.api.espn.com/apis/site/v2/sports/soccer/{league}/scoreboard"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json,text/plain,*/*",
    "Referer": "https://www.espn.com.ar/futbol/calendario",
}

# Agregá o quitá competiciones acá.
# La clave es el slug de ESPN.
LEAGUES = {
    # Argentina
    "arg.1": "Liga Profesional Argentina",
    "arg.2": "Primera Nacional Argentina",
    "arg.copa": "Copa Argentina",

    # CONMEBOL
    "conmebol.libertadores": "CONMEBOL Libertadores",
    "conmebol.sudamericana": "CONMEBOL Sudamericana",
    "conmebol.recopa": "CONMEBOL Recopa",
    "fifa.worldq.conmebol": "Eliminatorias CONMEBOL",

    # Europa principales
    "eng.1": "Premier League",
    "esp.1": "LaLiga",
    "ita.1": "Serie A",
    "ger.1": "Bundesliga",
    "fra.1": "Ligue 1",
    "ned.1": "Eredivisie",
    "por.1": "Primeira Liga",

    # Copas europeas
    "uefa.champions": "UEFA Champions League",
    "uefa.europa": "UEFA Europa League",
    "uefa.europa.conf": "UEFA Conference League",
    "uefa.super_cup": "UEFA Super Cup",

    # Selecciones / FIFA
    "fifa.world": "Mundial FIFA",
    "fifa.worldq.uefa": "Eliminatorias UEFA",
    "fifa.worldq.concacaf": "Eliminatorias CONCACAF",
    "fifa.worldq.caf": "Eliminatorias África",
    "fifa.worldq.afc": "Eliminatorias Asia",
    "fifa.worldq.ofc": "Eliminatorias Oceanía",
    "uefa.euro": "Eurocopa",
    "conmebol.america": "Copa América",

    # Norteamérica
    "usa.1": "MLS",
    "mex.1": "Liga MX",
    "concacaf.champions": "CONCACAF Champions Cup",

    # Brasil / Sudamérica
    "bra.1": "Brasileirão",
    "bra.copa_do_brazil": "Copa do Brasil",
    "uru.1": "Primera División Uruguay",
    "chi.1": "Primera División Chile",
    "col.1": "Primera A Colombia",
    "ecu.1": "LigaPro Ecuador",
    "per.1": "Liga 1 Perú",

    # Inglaterra copas
    "eng.fa": "FA Cup",
    "eng.league_cup": "Carabao Cup",
    "eng.2": "Championship",

    # España copas
    "esp.copa_del_rey": "Copa del Rey",
    "esp.super_cup": "Supercopa de España",

    # Italia copas
    "ita.coppa_italia": "Coppa Italia",
    "ita.super_cup": "Supercoppa Italiana",

    # Alemania copas
    "ger.dfb_pokal": "DFB Pokal",
    "ger.super_cup": "Supercopa Alemania",

    # Francia copas
    "fra.coupe_de_france": "Coupe de France",
}


def fecha_argentina():
    return datetime.now(timezone(timedelta(hours=-3)))


def fecha_api_argentina(fecha=None):
    if fecha is None:
        fecha = fecha_argentina()
    return fecha.strftime("%Y%m%d")


def obtener_eventos_liga(league_slug, league_name, fecha=None):
    url = ESPN_API_BASE.format(league=league_slug)

    params = {
        "region": "ar",
        "lang": "es",
        "dates": fecha_api_argentina(fecha),
        "limit": 300,
    }

    try:
        r = requests.get(url, headers=HEADERS, params=params, timeout=20)
        r.raise_for_status()
        data = r.json()

        eventos = data.get("events") or []

        return {
            "league_slug": league_slug,
            "league_name": league_name,
            "events": eventos,
            "ok": True,
            "error": None,
        }

    except Exception as e:
        return {
            "league_slug": league_slug,
            "league_name": league_name,
            "events": [],
            "ok": False,
            "error": str(e),
        }


def obtener_logo(equipo):
    logos = equipo.get("logos") or []
    if logos:
        return logos[0].get("href")
    return equipo.get("logo")


def limpiar_evento(evento, league_slug, league_name):
    competencia = (evento.get("competitions") or [{}])[0]
    competidores = competencia.get("competitors") or []

    local = None
    visitante = None
    local_logo = None
    visitante_logo = None
    local_id = None
    visitante_id = None

    for c in competidores:
        equipo = c.get("team") or {}

        nombre = (
            equipo.get("displayName")
            or equipo.get("shortDisplayName")
            or equipo.get("name")
        )

        equipo_id = equipo.get("id")
        logo = obtener_logo(equipo)

        if c.get("homeAway") == "home":
            local = nombre
            local_logo = logo
            local_id = equipo_id
        elif c.get("homeAway") == "away":
            visitante = nombre
            visitante_logo = logo
            visitante_id = equipo_id

    fecha_utc = evento.get("date")
    fecha_arg = None
    hora_arg = None

    if fecha_utc:
        dt = datetime.fromisoformat(fecha_utc.replace("Z", "+00:00"))
        dt_arg = dt.astimezone(timezone(timedelta(hours=-3)))
        fecha_arg = dt_arg.strftime("%Y-%m-%d")
        hora_arg = dt_arg.strftime("%H:%M")

    status = competencia.get("status") or {}
    estado = status.get("type") or {}

    links = evento.get("links") or []
    url_espn = links[0].get("href") if links else None

    marcador_local = None
    marcador_visitante = None

    for c in competidores:
        if c.get("homeAway") == "home":
            marcador_local = c.get("score")
        elif c.get("homeAway") == "away":
            marcador_visitante = c.get("score")

    return {
        "id": evento.get("id"),

        "partido": f"{local} vs {visitante}" if local and visitante else evento.get("name"),

        "local": local,
        "visitante": visitante,
        "local_id": local_id,
        "visitante_id": visitante_id,
        "local_logo": local_logo,
        "visitante_logo": visitante_logo,

        # ESTA ES LA COMPETICIÓN REAL
        "liga": league_name,
        "liga_corta": league_name,
        "liga_slug": league_slug,

        "competicion": {
            "nombre": league_name,
            "nombre_corto": league_name,
            "slug": league_slug,
        },

        "fecha": fecha_arg,
        "hora": hora_arg,

        "estado": estado.get("description"),
        "estado_corto": estado.get("shortDetail"),
        "estado_nombre": estado.get("name"),
        "completado": estado.get("completed"),

        "marcador_local": marcador_local,
        "marcador_visitante": marcador_visitante,

        "fecha_espn": fecha_utc,
        "url_espn": url_espn,
    }


def scrapear_partidos(fecha=None):
    resultados = []
    errores = []
    ids_vistos = set()

    print("Consultando competiciones de ESPN...")

    with ThreadPoolExecutor(max_workers=8) as executor:
        tareas = []

        for league_slug, league_name in LEAGUES.items():
            tareas.append(
                executor.submit(
                    obtener_eventos_liga,
                    league_slug,
                    league_name,
                    fecha
                )
            )

        for tarea in as_completed(tareas):
            respuesta = tarea.result()

            league_slug = respuesta["league_slug"]
            league_name = respuesta["league_name"]

            if not respuesta["ok"]:
                errores.append({
                    "liga": league_name,
                    "slug": league_slug,
                    "error": respuesta["error"],
                })
                continue

            eventos = respuesta["events"]

            for evento in eventos:
                evento_id = evento.get("id")

                # Evita duplicados si ESPN muestra el mismo partido en más de una competición.
                clave = evento_id or f"{league_slug}-{evento.get('name')}-{evento.get('date')}"

                if clave in ids_vistos:
                    continue

                item = limpiar_evento(evento, league_slug, league_name)

                if item["local"] and item["visitante"]:
                    resultados.append(item)
                    ids_vistos.add(clave)

    resultados.sort(
        key=lambda x: (
            x["fecha"] or "",
            x["hora"] or "",
            x["liga"] or "",
            x["partido"] or "",
        )
    )

    return resultados, errores


def agrupar_por_liga(partidos):
    ligas = {}

    for partido in partidos:
        liga = partido.get("liga") or "Sin competición"

        if liga not in ligas:
            ligas[liga] = []

        ligas[liga].append(partido)

    return [
        {
            "liga": liga,
            "total": len(items),
            "partidos": items,
        }
        for liga, items in ligas.items()
    ]


def guardar_json(partidos, errores):
    salida = {
        "fuente": "ESPN Argentina",
        "metodo": "scoreboard por competición",
        "fecha_scrapeo": fecha_argentina().isoformat(),
        "total": len(partidos),
        "total_ligas_consultadas": len(LEAGUES),
        "partidos": partidos,
        "agrupado_por_liga": agrupar_por_liga(partidos),
        "errores": errores,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(salida, f, ensure_ascii=False, indent=2)


def main():
    print("Obteniendo agenda desde ESPN por competición...")

    partidos, errores = scrapear_partidos()
    guardar_json(partidos, errores)

    print(f"OK: {len(partidos)} partidos guardados en {OUTPUT_FILE}")
    print(f"Ligas consultadas: {len(LEAGUES)}")
    print(f"Errores: {len(errores)}")


if __name__ == "__main__":
    main()
