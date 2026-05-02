import requests
from bs4 import BeautifulSoup
import base64

AGENDA_URL = "https://pelotalibrestv.org/agenda.html"


def obtener_html():
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(AGENDA_URL, headers=headers, timeout=15)
    r.raise_for_status()
    return r.text


def decodificar_base64(href):
    if not href or "r=" not in href:
        return None

    encoded = href.split("r=")[1]
    return base64.b64decode(encoded).decode("utf-8")


def scrapear_partidos():
    html = obtener_html()
    soup = BeautifulSoup(html, "html.parser")

    resultados = []
    enlaces = soup.find_all("a")

    for i in range(len(enlaces) - 1):

        texto = enlaces[i].get_text(strip=True)

        if "vs" in texto.lower():

            hora_tag = enlaces[i].find("span", class_="t")
            hora = hora_tag.text if hora_tag else None

            siguiente = enlaces[i + 1]
            canal = siguiente.get_text(strip=True)
            href = siguiente.get("href")

            url_evento = decodificar_base64(href)

            resultados.append({
                "partido": texto.strip(),
                "hora": hora,
                "canal": canal.strip(),
                "url_evento": url_evento
            })

    return resultados
