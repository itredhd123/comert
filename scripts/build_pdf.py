#!/usr/bin/env python3
"""Transformă raportul HTML într-un PDF A4 autonom.

Raportul se bazează pe fonturi de la Google Fonts. Un PDF care le cere prin rețea
la momentul randării iese cu fonturi de rezervă — sau, dacă mediul n-are acces la
fonts.gstatic.com, iese pur și simplu urât. Așa că le descărcăm o dată și le
încorporăm ca data URI: PDF-ul rezultat nu mai depinde de nimic.

  python3 scripts/build_pdf.py raport-validare-piata.html

Produce `<nume>.pdf` lângă sursă, plus un `print.html` intermediar în scratchpad.
"""

from __future__ import annotations

import argparse
import base64
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

# Doar subseturile de care are nevoie limba română. Fără filtrul ăsta am încorpora
# și greacă, chirilică și vietnameză — de câteva ori mai mulți octeți, degeaba.
SUBSETURI = ("latin", "latin-ext")

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36"

CANDIDATI_CHROME = (
    "/opt/pw-browsers/chromium-1194/chrome-linux/chrome",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
    "/usr/bin/google-chrome",
)

# Stil suplimentar pentru hârtie: fără rail de navigare, fără bară de progres,
# fără tăieturi urâte în tabele și carduri.
CSS_PRINT = """
@page { size: A4; margin: 14mm 12mm; }
html, body { background: #fff !important; }
#progress, .rail, details.toc-m { display: none !important; }
.grid { grid-template-columns: minmax(0,1fr) !important; gap: 0 !important; }
.wrap { max-width: none !important; padding: 0 !important; }
body { font-size: 10.5pt; line-height: 1.5; }
h1 { font-size: 30pt !important; }
h2 { font-size: 18pt !important; }
h3 { font-size: 12pt !important; }
p, td, .card dd { font-size: 10.5pt; }
section { padding: 20px 0 !important; break-inside: auto; }
.sechead { break-after: avoid; }
h2, h3, h4 { break-after: avoid; }
.tablewrap, .card, .callout, .stats, .hooks, .numlist li { break-inside: avoid; }
table { min-width: 0 !important; font-size: 9.5pt; }
th, td { padding: 6px 9px; }
.stat b { font-size: 19pt !important; }
.sources { columns: 2 200px; font-size: 8.5pt; }
.sources a { color: #65737F !important; }
header.masthead { padding-top: 0 !important; }
"""


def descarca(url: str) -> bytes:
    cerere = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(cerere, timeout=60) as r:
        return r.read()


def fonturi_incorporate(url_css: str) -> str:
    """Descarcă foaia Google Fonts și înlocuiește fiecare URL cu un data URI."""
    css = descarca(url_css).decode("utf-8")

    # Foaia vine ca blocuri `/* subset */ @font-face {...}`. Le păstrăm doar pe
    # cele latine, ca să nu umflăm fișierul cu alfabete nefolosite.
    blocuri = re.split(r"/\*\s*([\w-]+)\s*\*/", css)
    pastrate: list[str] = []
    for i in range(1, len(blocuri) - 1, 2):
        if blocuri[i].strip() in SUBSETURI:
            pastrate.append(blocuri[i + 1])

    combinat = "\n".join(pastrate)
    urls = sorted(set(re.findall(r"url\((https://fonts\.gstatic\.com[^)]+)\)", combinat)))
    print(f"  {len(pastrate)} reguli @font-face, {len(urls)} fișiere de descărcat", file=sys.stderr)

    cache: dict[str, str] = {}
    total = 0
    for u in urls:
        date = descarca(u)
        total += len(date)
        cache[u] = "data:font/woff2;base64," + base64.b64encode(date).decode("ascii")
        print(f"    {len(date):>7} octeți  {u.rsplit('/', 1)[-1]}", file=sys.stderr)

    for u, data_uri in cache.items():
        combinat = combinat.replace(u, data_uri)
    print(f"  {total // 1024} KiB de fonturi încorporate", file=sys.stderr)
    return combinat


def gaseste_chrome() -> str:
    for cale in CANDIDATI_CHROME:
        if Path(cale).exists():
            return cale
    raise SystemExit("Nu găsesc Chromium. Setează calea în CANDIDATI_CHROME.")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("sursa", help="fișierul HTML al raportului")
    p.add_argument("--iesire", help="PDF-ul de ieșire (implicit: lângă sursă)")
    p.add_argument("--intermediar", default="print.html",
                   help="unde se scrie HTML-ul cu fonturi încorporate")
    args = p.parse_args()

    sursa = Path(args.sursa)
    if not sursa.exists():
        print(f"Nu găsesc {sursa}", file=sys.stderr)
        return 2
    html = sursa.read_text(encoding="utf-8")

    potrivire = re.search(r'<link rel="stylesheet" href="(https://fonts\.googleapis\.com[^"]+)">', html)
    if not potrivire:
        print("Nu găsesc link-ul către Google Fonts în sursă.", file=sys.stderr)
        return 2

    print("Încorporez fonturile...", file=sys.stderr)
    css_fonturi = fonturi_incorporate(potrivire.group(1).replace("&amp;", "&"))

    # Scoatem link-urile către rețea și punem fonturile inline, plus stilul de print.
    html = html.replace(potrivire.group(0), f"<style>{css_fonturi}</style>")
    html = re.sub(r'<link rel="preconnect"[^>]*>\s*', "", html)
    html = html.replace("</style>", "</style>\n<style>" + CSS_PRINT + "</style>", 1) \
        if "</style>" in html else html + f"<style>{CSS_PRINT}</style>"

    # Fără declarația asta, Chromium ghicește codificarea — iar cu un fișier de peste
    # un megaoctet, din care primii sute de kiloocteți sunt base64 de fonturi,
    # euristica ratează și toate diacriticele ies mojibake. Costă o linie, salvează PDF-ul.
    if "charset" not in html[:1024].lower():
        html = '<meta charset="utf-8">\n' + html

    intermediar = Path(args.intermediar)
    intermediar.write_text(html, encoding="utf-8")
    print(f"  {intermediar} ({len(html) // 1024} KiB)", file=sys.stderr)

    iesire = Path(args.iesire) if args.iesire else sursa.with_suffix(".pdf")
    print("Randez PDF-ul...", file=sys.stderr)
    rezultat = subprocess.run(
        [gaseste_chrome(), "--headless", "--disable-gpu", "--no-sandbox",
         "--no-pdf-header-footer", "--virtual-time-budget=20000",
         f"--print-to-pdf={iesire.resolve()}", intermediar.resolve().as_uri()],
        capture_output=True, text=True, timeout=300,
    )
    if not iesire.exists():
        print(rezultat.stderr[-2000:], file=sys.stderr)
        return 1

    print(f"\n{iesire} — {iesire.stat().st_size // 1024} KiB", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
