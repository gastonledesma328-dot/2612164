import requests
import json
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

OUTPUT_FILE = "agenda_espn.json"

ESPN_SCOREBOARD_URLS = [
    "https://site.api.espn.com/apis/site/v2/sports/soccer/{league}/scoreboard",
    "https://site.web.api.espn.com/apis/site/v2/sports/soccer/{league}/scoreboard",
]

ESPN_SUMMARY_URLS = [
    "https://site.api.espn.com/apis/site/v2/sports/soccer/{league}/summary",
    "https://site.web.api.espn.com/apis/site/v2/sports/soccer/{league}/summary",
]

FETCH_SCORERS = True

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json,text/plain,*/*",
    "Referer": "https://www.espn.com.ar/futbol/calendario",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}

# ============================================================
# LIGAS / COMPETICIONES ESPN
# ============================================================

LEAGUES = {
    # ARGENTINA
    "arg.1": "Liga Profesional Argentina",
    "arg.2": "Primera Nacional Argentina",
    "arg.copa": "Copa Argentina",
    "arg.supercopa": "Supercopa Argentina",

    # CONMEBOL / SUDAMÉRICA
    "conmebol.libertadores": "CONMEBOL Libertadores",
    "conmebol.sudamericana": "CONMEBOL Sudamericana",
    "conmebol.recopa": "CONMEBOL Recopa",
    "conmebol.america": "Copa América",
    "fifa.worldq.conmebol": "Eliminatorias CONMEBOL",

    "bra.1": "Brasileirão Serie A",
    "bra.2": "Brasileirão Serie B",
    "bra.copa_do_brazil": "Copa do Brasil",

    "uru.1": "Primera División Uruguay",
    "chi.1": "Primera División Chile",
    "col.1": "Primera A Colombia",
    "ecu.1": "LigaPro Ecuador",
    "per.1": "Liga 1 Perú",
    "par.1": "Primera División Paraguay",
    "bol.1": "Primera División Bolivia",
    "ven.1": "Primera División Venezuela",

    # EUROPA - PRINCIPALES
    "eng.1": "Premier League",
    "eng.2": "Championship",
    "eng.3": "League One",
    "eng.4": "League Two",
    "eng.5": "National League",
    "eng.fa": "FA Cup",
    "eng.league_cup": "Carabao Cup",
    "eng.community": "Community Shield",

    "esp.1": "LaLiga",
    "esp.2": "LaLiga 2",
    "esp.copa_del_rey": "Copa del Rey",
    "esp.super_cup": "Supercopa de España",

    "ita.1": "Serie A",
    "ita.2": "Serie B",
    "ita.coppa_italia": "Coppa Italia",
    "ita.super_cup": "Supercoppa Italiana",

    "ger.1": "Bundesliga",
    "ger.2": "2. Bundesliga",
    "ger.3": "3. Liga",
    "ger.dfb_pokal": "DFB Pokal",
    "ger.super_cup": "Supercopa Alemania",

    "fra.1": "Ligue 1",
    "fra.2": "Ligue 2",
    "fra.coupe_de_france": "Coupe de France",
    "fra.coupe_de_la_ligue": "Coupe de la Ligue",

    "ned.1": "Eredivisie",
    "ned.2": "Eerste Divisie",
    "ned.knvb_beker": "KNVB Beker",

    "por.1": "Primeira Liga",
    "por.2": "Liga Portugal 2",
    "por.taca_de_portugal": "Taça de Portugal",

    # UEFA / INTERNACIONALES EUROPA
    "uefa.champions": "UEFA Champions League",
    "uefa.europa": "UEFA Europa League",
    "uefa.europa.conf": "UEFA Conference League",
    "uefa.super_cup": "UEFA Super Cup",
    "uefa.nations": "UEFA Nations League",
    "uefa.euro": "Eurocopa",
    "fifa.worldq.uefa": "Eliminatorias UEFA",

    # MÁS EUROPA
    "sco.1": "Scottish Premiership",
    "sco.2": "Scottish Championship",
    "bel.1": "Belgian Pro League",
    "aut.1": "Austrian Bundesliga",
    "sui.1": "Swiss Super League",
    "tur.1": "Super Lig Turquía",
    "gre.1": "Super League Grecia",
    "den.1": "Superliga Dinamarca",
    "nor.1": "Eliteserien Noruega",
    "swe.1": "Allsvenskan Suecia",
    "pol.1": "Ekstraklasa Polonia",
    "cze.1": "Czech First League",
    "cro.1": "HNL Croacia",
    "ser.1": "SuperLiga Serbia",
    "rom.1": "Liga I Rumania",
    "ukr.1": "Premier League Ucrania",
    "rus.1": "Premier League Rusia",
    "irl.1": "Premier Division Irlanda",

    # NORTE / CENTROAMÉRICA
    "usa.1": "MLS",
    "usa.2": "USL Championship",
    "usa.open": "US Open Cup",

    "mex.1": "Liga MX",
    "mex.2": "Liga de Expansión MX",
    "mex.copa": "Copa MX",

    "concacaf.champions": "CONCACAF Champions Cup",
    "concacaf.gold": "Copa Oro",
    "concacaf.nations": "CONCACAF Nations League",
    "fifa.worldq.concacaf": "Eliminatorias CONCACAF",

    # ASIA
    "afc.champions": "AFC Champions League",
    "afc.cup": "AFC Cup",
    "afc.asian.cup": "AFC Asian Cup",
    "fifa.worldq.afc": "Eliminatorias Asia",

    "chn.1": "Superliga China",
    "jpn.1": "J1 League Japón",
    "jpn.2": "J2 League Japón",
    "kor.1": "K League 1 Corea",
    "aus.1": "A-League Australia",
    "ind.1": "Indian Super League",
    "ksa.1": "Saudi Pro League",
    "uae.1": "UAE Pro League",
    "qat.1": "Qatar Stars League",

    # ÁFRICA
    "caf.champions": "CAF Champions League",
    "caf.confed": "CAF Confederation Cup",
    "caf.nations": "Copa Africana de Naciones",
    "fifa.worldq.caf": "Eliminatorias África",

    "rsa.1": "Premier Soccer League Sudáfrica",
    "egy.1": "Premier League Egipto",
    "mar.1": "Botola Marruecos",

    # OCEANÍA / FIFA
    "fifa.world": "Mundial FIFA",
    "fifa.worldq.ofc": "Eliminatorias Oceanía",
    "fifa.confederations": "Copa Confederaciones",

    # MUNDIALES / TORNEOS FIFA
    "fifa.cwc": "Mundial de Clubes FIFA",
    "fifa.intercontinental": "Copa Intercontinental FIFA",

    # FEMENINO
    "fifa.wwc": "Mundial Femenino FIFA",
    "uefa.wchampions": "UEFA Women's Champions League",
    "uefa.weuro": "Eurocopa Femenina",
    "eng.w.1": "Women's Super League Inglaterra",
    "usa.nwsl": "NWSL Estados Unidos",
}

# ============================================================
# PRIORIDAD DE ORDEN
# Menor número = aparece más arriba
# ============================================================

LEAGUE_PRIORITY = {
    # COPA DEL MUNDO / FIFA
    "fifa.world": 1,
    "fifa.cwc": 2,
    "fifa.intercontinental": 3,

    "fifa.worldq.conmebol": 4,
    "fifa.worldq.uefa": 5,
    "fifa.worldq.concacaf": 6,
    "fifa.worldq.afc": 7,
    "fifa.worldq.caf": 8,
    "fifa.worldq.ofc": 9,

    # EUROPA PRINCIPAL
    "uefa.champions": 10,
    "uefa.europa": 11,
    "uefa.europa.conf": 12,
    "uefa.super_cup": 13,
    "uefa.nations": 14,
    "uefa.euro": 15,

    "eng.1": 20,
    "esp.1": 21,
    "ita.1": 22,
    "ger.1": 23,
    "fra.1": 24,

    "eng.fa": 30,
    "eng.league_cup": 31,
    "eng.community": 32,
    "eng.2": 33,

    "esp.copa_del_rey": 34,
    "esp.super_cup": 35,
    "esp.2": 36,

    "ita.coppa_italia": 37,
    "ita.super_cup": 38,
    "ita.2": 39,

    "ger.dfb_pokal": 40,
    "ger.super_cup": 41,
    "ger.2": 42,

    "fra.coupe_de_france": 43,
    "fra.2": 44,

    "por.1": 50,
    "ned.1": 51,
    "bel.1": 52,
    "tur.1": 53,
    "sco.1": 54,
    "aut.1": 55,
    "sui.1": 56,

    # SUDAMÉRICA PRINCIPAL
    "conmebol.libertadores": 100,
    "conmebol.sudamericana": 101,
    "conmebol.recopa": 102,
    "conmebol.america": 103,

    "bra.1": 110,
    "bra.copa_do_brazil": 111,
    "bra.2": 112,

    "arg.1": 120,
    "arg.copa": 121,
    "arg.supercopa": 122,
    "arg.2": 123,

    "uru.1": 130,
    "chi.1": 131,
    "col.1": 132,
    "ecu.1": 133,
    "per.1": 134,
    "par.1": 135,
    "bol.1": 136,
    "ven.1": 137,

    # NORTE / CENTROAMÉRICA
    "mex.1": 200,
    "usa.1": 201,
    "concacaf.champions": 202,
    "concacaf.gold": 203,
    "concacaf.nations": 204,
    "mex.2": 205,
    "usa.2": 206,
    "usa.open": 207,

    # ASIA / ÁFRICA / OTROS
    "afc.champions": 300,
    "afc.cup": 301,
    "afc.asian.cup": 302,
    "ksa.1": 310,
    "jpn.1": 311,
    "kor.1": 312,
    "aus.1": 313,
    "chn.1": 314,

    "caf.champions": 400,
    "caf.confed": 401,
    "caf.nations": 402,

    # FEMENINO
    "fifa.wwc": 500,
    "uefa.wchampions": 501,
    "uefa.weuro": 502,
    "eng.w.1": 503,
    "usa.nwsl": 504,
}


def fecha_argentina():
    return datetime.now(timezone(timedelta(hours=-3)))


def fecha_api_argentina(fecha=None):
    if fecha is None:
        fecha = fecha_argentina()

    return fecha.strftime("%Y%m%d")


def normalizar_score(score):
    if score is None:
        return None

    if isinstance(score, dict):
        score = (
            score.get("value")
            or score.get("displayValue")
            or score.get("score")
        )

    if score is None:
        return None

    try:
        return str(int(float(score)))
    except Exception:
        return str(score)


def score_numero(score):
    score = normalizar_score(score)

    try:
        return int(score or 0)
    except Exception:
        return 0


def obtener_eventos_liga(league_slug, league_name, fecha=None):
    params = {
        "region": "ar",
        "lang": "es",
        "contentorigin": "espn",
        "dates": fecha_api_argentina(fecha),
        "limit": 300,
        "_": int(datetime.now().timestamp()),
    }

    ultimo_error = None

    for base_url in ESPN_SCOREBOARD_URLS:
        url = base_url.format(league=league_slug)

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
            ultimo_error = str(e)

    return {
        "league_slug": league_slug,
        "league_name": league_name,
        "events": [],
        "ok": False,
        "error": ultimo_error,
    }


def obtener_detalle_evento(league_slug, event_id):
    """
    Consulta summary de ESPN para datos más actualizados:
    marcador, estado, minuto y goleadores.
    Usa dos endpoints y se queda con el dato más vivo.
    """
    if not event_id:
        return {}

    params = {
        "region": "ar",
        "lang": "es",
        "contentorigin": "espn",
        "event": event_id,
        "_": int(datetime.now().timestamp()),
    }

    mejor_detalle = {}

    for base_url in ESPN_SUMMARY_URLS:
        url = base_url.format(league=league_slug)

        try:
            r = requests.get(url, headers=HEADERS, params=params, timeout=15)
            r.raise_for_status()

            data = r.json()

            if not mejor_detalle:
                mejor_detalle = data
                continue

            comp_actual = obtener_competencia_desde_detalle(mejor_detalle)
            comp_nueva = obtener_competencia_desde_detalle(data)

            if puntuar_competencia(comp_nueva) > puntuar_competencia(comp_actual):
                mejor_detalle = data

        except Exception:
            continue

    return mejor_detalle


def obtener_logo(equipo):
    logos = equipo.get("logos") or []

    if logos:
        for logo in logos:
            href = logo.get("href")
            if href and ".png" in href.lower():
                return href

        for logo in logos:
            href = logo.get("href")
            if href:
                return href

    logo_directo = equipo.get("logo")
    if logo_directo:
        return logo_directo

    equipo_id = equipo.get("id")
    if equipo_id:
        return f"https://a.espncdn.com/i/teamlogos/soccer/500/{equipo_id}.png"

    return None


def obtener_competencia_desde_detalle(detalle):
    header = detalle.get("header") or {}
    competencias_header = header.get("competitions") or []

    if competencias_header:
        return competencias_header[0]

    return {}


def obtener_competencia_desde_evento(evento):
    competencias_evento = evento.get("competitions") or []

    if competencias_evento:
        return competencias_evento[0]

    return {}


def puntuar_competencia(competencia):
    """
    Sirve para elegir la competencia más actualizada.
    Mayor puntaje = dato más confiable.
    """
    if not competencia:
        return -1

    status = competencia.get("status") or {}
    estado = status.get("type") or {}

    nombre = estado.get("name")
    completado = bool(estado.get("completed"))
    clock = status.get("displayClock")
    estado_corto = estado.get("shortDetail") or ""

    competidores = competencia.get("competitors") or []

    total_goles = 0
    for c in competidores:
        total_goles += score_numero(c.get("score"))

    puntaje = 0

    if completado:
        puntaje += 1000

    if nombre in [
        "STATUS_IN_PROGRESS",
        "STATUS_HALFTIME",
        "STATUS_END_PERIOD",
        "STATUS_FINAL",
        "STATUS_FULL_TIME",
    ]:
        puntaje += 800

    if clock:
        puntaje += 500

    if "'" in str(estado_corto) or "+" in str(estado_corto):
        puntaje += 300

    puntaje += total_goles * 50

    return puntaje


def elegir_mejor_competencia(evento, detalle):
    """
    Compara scoreboard vs summary y elige el dato más actualizado.
    """
    competencias = []

    comp_evento = obtener_competencia_desde_evento(evento)
    if comp_evento:
        competencias.append(comp_evento)

    comp_detalle = obtener_competencia_desde_detalle(detalle)
    if comp_detalle:
        competencias.append(comp_detalle)

    if not competencias:
        return {}

    return max(competencias, key=puntuar_competencia)


def extraer_estado(competencia):
    status = competencia.get("status") or {}
    estado = status.get("type") or {}

    clock = status.get("displayClock")
    periodo = status.get("period")

    estado_nombre = estado.get("name")
    estado_desc = estado.get("description")
    estado_corto = estado.get("shortDetail")

    completado = bool(estado.get("completed"))

    if estado_nombre in ["STATUS_FINAL", "STATUS_FULL_TIME"]:
        completado = True

    if completado:
        mostrar_tiempo = "Fin"
    elif clock:
        mostrar_tiempo = clock
    else:
        mostrar_tiempo = estado_corto or estado_desc

    return {
        "estado": estado_desc,
        "estado_corto": estado_corto,
        "estado_nombre": estado_nombre,
        "completado": completado,
        "minuto": clock,
        "periodo": periodo,
        "mostrar_tiempo": mostrar_tiempo,
    }


def extraer_equipos_y_marcador(competencia):
    competidores = competencia.get("competitors") or []

    datos = {
        "local": None,
        "visitante": None,
        "local_logo": None,
        "visitante_logo": None,
        "local_id": None,
        "visitante_id": None,
        "marcador_local": None,
        "marcador_visitante": None,
    }

    for c in competidores:
        equipo = c.get("team") or {}

        nombre = (
            equipo.get("displayName")
            or equipo.get("shortDisplayName")
            or equipo.get("name")
        )

        equipo_id = equipo.get("id")
        logo = obtener_logo(equipo)
        score = normalizar_score(c.get("score"))

        if c.get("homeAway") == "home":
            datos["local"] = nombre
            datos["local_logo"] = logo
            datos["local_id"] = equipo_id
            datos["marcador_local"] = score

        elif c.get("homeAway") == "away":
            datos["visitante"] = nombre
            datos["visitante_logo"] = logo
            datos["visitante_id"] = equipo_id
            datos["marcador_visitante"] = score

    return datos


def extraer_goleadores(detalle):
    """
    ESPN suele mandar los goles en scoringPlays.
    No todos los partidos/ligas lo traen.
    """
    goleadores = []

    scoring_plays = detalle.get("scoringPlays") or []

    for play in scoring_plays:
        atleta = play.get("athlete") or {}
        equipo = play.get("team") or {}
        clock = play.get("clock")
        tipo = play.get("type") or {}

        jugador = (
            atleta.get("displayName")
            or atleta.get("fullName")
            or atleta.get("shortName")
            or atleta.get("name")
        )

        equipo_nombre = (
            equipo.get("displayName")
            or equipo.get("shortDisplayName")
            or equipo.get("name")
            or equipo.get("abbreviation")
        )

        minuto = None

        if isinstance(clock, dict):
            minuto = clock.get("displayValue")
        elif isinstance(clock, str):
            minuto = clock

        descripcion = (
            play.get("text")
            or play.get("displayValue")
            or tipo.get("text")
            or tipo.get("description")
        )

        score = play.get("score") or {}

        if not jugador and not descripcion:
            continue

        goleadores.append({
            "jugador": jugador,
            "equipo": equipo_nombre,
            "minuto": minuto,
            "descripcion": descripcion,
            "score": score,
        })

    return goleadores


def partido_empezo_o_termino(estado_data, marcador_local=None, marcador_visitante=None):
    estado_nombre = estado_data.get("estado_nombre")
    estado_corto = estado_data.get("estado_corto")
    estado = estado_data.get("estado")
    completado = estado_data.get("completado")
    minuto = estado_data.get("minuto")
    mostrar_tiempo = estado_data.get("mostrar_tiempo")

    estados_activos = [
        "STATUS_IN_PROGRESS",
        "STATUS_HALFTIME",
        "STATUS_END_PERIOD",
        "STATUS_FINAL",
        "STATUS_FULL_TIME",
    ]

    if completado:
        return True

    if estado_nombre in estados_activos:
        return True

    if minuto:
        return True

    textos = [
        str(estado_corto or ""),
        str(estado or ""),
        str(mostrar_tiempo or ""),
    ]

    for texto in textos:
        texto_lower = texto.lower()

        if "'" in texto or "+" in texto:
            return True

        if texto_lower in ["fin", "final", "descanso", "entretiempo"]:
            return True

        if "half" in texto_lower or "final" in texto_lower:
            return True

    try:
        goles_local = int(marcador_local or 0)
        goles_visitante = int(marcador_visitante or 0)

        if goles_local > 0 or goles_visitante > 0:
            return True
    except Exception:
        pass

    return False


def calcular_resultado(marcador_local, marcador_visitante, estado_data):
    if not partido_empezo_o_termino(estado_data, marcador_local, marcador_visitante):
        return None

    if marcador_local is None or marcador_visitante is None:
        return None

    return f"{marcador_local}-{marcador_visitante}"


def normalizar_mostrar_tiempo(estado_data, hora_inicio):
    completado = estado_data.get("completado")
    minuto = estado_data.get("minuto")
    estado_corto = estado_data.get("estado_corto")
    mostrar_tiempo = estado_data.get("mostrar_tiempo")

    if completado:
        return "Fin"

    if minuto:
        return minuto

    if estado_corto and ("'" in str(estado_corto) or "+" in str(estado_corto)):
        return estado_corto

    if mostrar_tiempo and mostrar_tiempo not in ["Prox", "Programado", "Previa"]:
        return mostrar_tiempo

    return hora_inicio


def limpiar_evento(evento, league_slug, league_name):
    detalle = {}

    if FETCH_SCORERS and evento.get("id"):
        detalle = obtener_detalle_evento(league_slug, evento.get("id"))

    competencia = elegir_mejor_competencia(evento, detalle)

    equipos = extraer_equipos_y_marcador(competencia)
    estado_data = extraer_estado(competencia)

    local = equipos["local"]
    visitante = equipos["visitante"]
    marcador_local = equipos["marcador_local"]
    marcador_visitante = equipos["marcador_visitante"]

    mostrar_marcador = partido_empezo_o_termino(
        estado_data,
        marcador_local,
        marcador_visitante
    )

    resultado = calcular_resultado(
        marcador_local,
        marcador_visitante,
        estado_data
    )

    fecha_utc = evento.get("date")

    comp_detalle = obtener_competencia_desde_detalle(detalle)
    if comp_detalle:
        fecha_utc = comp_detalle.get("date") or fecha_utc

    fecha_arg = None
    hora_inicio = None

    if fecha_utc:
        dt = datetime.fromisoformat(fecha_utc.replace("Z", "+00:00"))
        dt_arg = dt.astimezone(timezone(timedelta(hours=-3)))
        fecha_arg = dt_arg.strftime("%Y-%m-%d")
        hora_inicio = dt_arg.strftime("%H:%M")

    hora_mostrar = normalizar_mostrar_tiempo(estado_data, hora_inicio)

    links = evento.get("links") or []
    url_espn = links[0].get("href") if links else None

    prioridad = LEAGUE_PRIORITY.get(league_slug, 9999)

    goleadores = extraer_goleadores(detalle) if detalle and mostrar_marcador else []

    return {
        "id": evento.get("id"),

        "partido": f"{local} vs {visitante}" if local and visitante else evento.get("name"),

        "local": local,
        "visitante": visitante,
        "local_id": equipos["local_id"],
        "visitante_id": equipos["visitante_id"],
        "local_logo": equipos["local_logo"],
        "visitante_logo": equipos["visitante_logo"],

        "liga": league_name,
        "liga_corta": league_name,
        "liga_slug": league_slug,
        "prioridad_liga": prioridad,

        "competicion": {
            "nombre": league_name,
            "nombre_corto": league_name,
            "slug": league_slug,
            "prioridad": prioridad,
        },

        "fecha": fecha_arg,

        # Hora real de inicio
        "hora_inicio": hora_inicio,

        # Campo listo para mostrar en la app:
        # - Partido próximo: 15:00
        # - Partido en vivo: 71'
        # - Partido terminado: Fin
        "hora": hora_mostrar,
        "mostrar_tiempo": hora_mostrar,

        "estado": estado_data["estado"],
        "estado_corto": estado_data["estado_corto"],
        "estado_nombre": estado_data["estado_nombre"],
        "completado": estado_data["completado"],
        "minuto": estado_data["minuto"],
        "periodo": estado_data["periodo"],

        "marcador_local": marcador_local if mostrar_marcador else None,
        "marcador_visitante": marcador_visitante if mostrar_marcador else None,
        "resultado": resultado,
        "mostrar_marcador": mostrar_marcador,
        "goleadores": goleadores,

        "fecha_espn": fecha_utc,
        "url_espn": url_espn,
    }


def scrapear_partidos(fecha=None):
    resultados = []
    errores = []
    ids_vistos = set()

    print("Consultando competiciones de ESPN...")

    with ThreadPoolExecutor(max_workers=12) as executor:
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
                clave = evento_id or f"{league_slug}-{evento.get('name')}-{evento.get('date')}"

                if clave in ids_vistos:
                    continue

                item = limpiar_evento(evento, league_slug, league_name)

                if item["local"] and item["visitante"]:
                    resultados.append(item)
                    ids_vistos.add(clave)

    resultados.sort(
        key=lambda x: (
            x.get("prioridad_liga", 9999),
            x.get("fecha") or "",
            x.get("hora_inicio") or "",
            x.get("partido") or "",
        )
    )

    return resultados, errores


def agrupar_por_liga(partidos):
    ligas = {}

    for partido in partidos:
        liga = partido.get("liga") or "Sin competición"
        prioridad = partido.get("prioridad_liga", 9999)

        if liga not in ligas:
            ligas[liga] = {
                "liga": liga,
                "liga_slug": partido.get("liga_slug"),
                "prioridad": prioridad,
                "partidos": []
            }

        ligas[liga]["partidos"].append(partido)

    agrupado = []

    for liga_data in ligas.values():
        liga_data["partidos"].sort(
            key=lambda x: (
                x.get("fecha") or "",
                x.get("hora_inicio") or "",
                x.get("partido") or "",
            )
        )

        agrupado.append({
            "liga": liga_data["liga"],
            "liga_slug": liga_data["liga_slug"],
            "prioridad": liga_data["prioridad"],
            "total": len(liga_data["partidos"]),
            "partidos": liga_data["partidos"],
        })

    agrupado.sort(
        key=lambda x: (
            x.get("prioridad", 9999),
            x.get("liga") or "",
        )
    )

    return agrupado


def guardar_json(partidos, errores):
    salida = {
        "fuente": "ESPN Argentina",
        "metodo": "scoreboard + summary doble endpoint",
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
