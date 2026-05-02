import base64
import json
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import requests
from bs4 import BeautifulSoup

AGENDA_URL = "https://pelotalibrestv.org/agenda.html"

# Este archivo queda en la RAÍZ del repo para usarlo desde GitHub Raw:
# https://raw.githubusercontent.com/gastonledesma328-dot/2612164/main/eventos.json
ROOT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_FILE = ROOT_DIR / "eventos.json"


def obtener_html():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Referer": "https://pelotalibrestv.org/",
    }
    r = requests.get(AGENDA_URL, headers=headers, timeout=20)
    r.raise_for_status()
    return r.text


def decodificar_base64(href):
    if not href:
        return None

    try:
        parsed = urlparse(href)
        params = parse_qs(parsed.query)
        encoded = params.get("r", [None])[0]

        if not encoded:
            return href

        # Completa padding si falta
        encoded += "=" * (-len(encoded) % 4)
        return base64.b64decode(encoded).decode("utf-8", errors="ignore")
    except Exception:
        return href


def scrapear_partidos():
    html = obtener_html()
    soup = BeautifulSoup(html, "html.parser")

    resultados = []
    enlaces = soup.find_all("a")

    for i in range(len(enlaces) - 1):
        texto = enlaces[i].get_text(" ", strip=True)

        if "vs" not in texto.lower():
            continue

        hora_tag = enlaces[i].find("span", class_="t")
        hora = hora_tag.get_text(strip=True) if hora_tag else None

        siguiente = enlaces[i + 1]
        canal = siguiente.get_text(" ", strip=True)
        href = siguiente.get("href")
        url_evento = decodificar_base64(href)

        resultados.append({
            "partido": texto.strip(),
            "hora": hora,
            "canal": canal.strip(),
            "url_evento": url_evento,
        })

    return resultados


def main():
    eventos = scrapear_partidos()

    salida = {
        "fuente": AGENDA_URL,
        "total": len(eventos),
        "eventos": eventos,
    }

    OUTPUT_FILE.write_text(
        json.dumps(salida, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"JSON generado: {OUTPUT_FILE}")
    print(f"Eventos encontrados: {len(eventos)}")


if __name__ == "__main__":
    main()
