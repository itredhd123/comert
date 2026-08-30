#!/usr/bin/env python3
"""Pasul 3: cât de viu e site-ul pe care firma îl are deja.

Ipoteza cea mai importantă a proiectului: „are site" nu înseamnă „n-are nevoie de site".
O firmă cu un site făcut acum șase ani, nefuncțional pe telefon, fără formular de
contact, e un client mai bun decât una fără niciun site — pentru că a acceptat deja
premisa că are nevoie de unul. Nu mai trebuie convinsă de asta, doar că al ei nu merge.

Împărțim piața în trei, nu în două:

  fara_site        — Google nu are niciun website pentru firmă
  site_mort        — există o adresă, dar nu răspunde, e parcată, e un redirect spre
                     Facebook, nu merge pe HTTPS sau nu e utilizabilă pe telefon
  site_functional  — răspunde, e sigur, e mobil și are cum să fie contactat cineva

  python3 scripts/verifica_site.py                       # citește date/recensamant.csv
  python3 scripts/verifica_site.py --limita 50           # doar primele 50, pentru probe

Notă de rulare: scriptul contactează site-uri arbitrare. Într-un mediu cu egress
restricționat (cum e containerul în care a fost scris) va raporta totul ca mort. Rulează-l
de pe o mașină cu acces normal la internet, altfel rezultatele n-au nicio valoare.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, asdict, fields
from pathlib import Path
from urllib.parse import urlparse

try:
    import requests
    from requests.exceptions import SSLError
except ImportError:
    print("Lipsește `requests`. Instalează cu: python3 -m pip install requests", file=sys.stderr)
    raise SystemExit(2)

# Cât timp îi dăm unui site să răspundă. Peste asta, un client de pe telefon
# a plecat deja oricum.
TIMEOUT_S = 12
UA = "Mozilla/5.0 (compatible; RecensamantSiteRO/1.0; cercetare de piata)"

RETELE_SOCIALE = ("facebook.com", "instagram.com", "linkedin.com", "tiktok.com", "twitter.com")

# Semne că pagina e un placeholder, nu un site. Verificate pe conținut lowercase.
SEMNE_PARCAT = (
    "domeniu de vanzare", "domeniu de vânzare", "domain for sale", "this domain is for sale",
    "under construction", "in constructie", "în construcție", "site in lucru", "site în lucru",
    "coming soon", "in curand", "în curând", "pagina in constructie",
    "welcome to nginx", "apache2 ubuntu default page", "it works!",
    "index of /", "default web site page", "future home of",
)

SEMNE_CONTACT = ("<form", "mailto:", "tel:", "whatsapp", "wa.me")
SEMNE_PROGRAMARE = (
    "programare", "programează", "programeaza", "rezerva", "rezervă",
    "cere oferta", "cere ofertă", "solicita oferta", "solicită ofertă", "booking",
)

# Sub atâția octeți de HTML nu poate exista un site real.
PRAG_CONTINUT_MINIM = 1500


@dataclass
class Verdict:
    place_id: str
    verticala: str
    oras: str
    nume: str
    website: str
    clasificare: str
    motiv: str
    cod_http: str
    https_ok: int
    mobil_ok: int
    are_contact: int
    are_programare: int
    parcat: int
    redirect_social: int
    timp_raspuns_s: str
    octeti: str


def verifica_unul(rand: dict) -> Verdict:
    url = (rand.get("website") or "").strip()
    baza = dict(
        place_id=rand.get("place_id", ""), verticala=rand.get("verticala", ""),
        oras=rand.get("oras", ""), nume=rand.get("nume", ""), website=url,
    )
    gol = dict(cod_http="", https_ok=0, mobil_ok=0, are_contact=0, are_programare=0,
               parcat=0, redirect_social=0, timp_raspuns_s="", octeti="")

    if not url:
        return Verdict(**baza, **gol, clasificare="fara_site", motiv="Google nu are website")

    gazda = (urlparse(url).netloc or "").lower()
    if any(r in gazda for r in RETELE_SOCIALE):
        return Verdict(**{**baza, **gol}, clasificare="site_mort",
                       motiv="„site-ul” e de fapt o pagină de rețea socială")

    inceput = time.monotonic()
    try:
        r = requests.get(url, timeout=TIMEOUT_S, headers={"User-Agent": UA}, allow_redirects=True)
    except SSLError:
        # Certificat invalid sau expirat. Browserele afișează un ecran roșu de avertizare,
        # deci pentru un client real site-ul e inutilizabil chiar dacă serverul răspunde.
        return Verdict(**{**baza, **gol}, clasificare="site_mort",
                       motiv="certificat HTTPS invalid sau expirat")
    except requests.RequestException as e:
        tip = type(e).__name__
        return Verdict(**{**baza, **gol}, clasificare="site_mort",
                       motiv=f"nu răspunde ({tip})")

    durata = time.monotonic() - inceput
    html = r.text or ""
    mic = html.lower()
    octeti = len(r.content or b"")

    final = (urlparse(r.url).netloc or "").lower()
    redirect_social = any(s in final for s in RETELE_SOCIALE)
    https_ok = r.url.startswith("https://")
    mobil_ok = bool(re.search(r'<meta[^>]+name=["\']?viewport', mic))
    parcat = any(s in mic for s in SEMNE_PARCAT) or octeti < PRAG_CONTINUT_MINIM
    are_contact = any(s in mic for s in SEMNE_CONTACT)
    are_programare = any(s in mic for s in SEMNE_PROGRAMARE)

    masurat = dict(
        cod_http=str(r.status_code), https_ok=int(https_ok), mobil_ok=int(mobil_ok),
        are_contact=int(are_contact), are_programare=int(are_programare),
        parcat=int(parcat), redirect_social=int(redirect_social),
        timp_raspuns_s=f"{durata:.2f}", octeti=str(octeti),
    )

    clasificare, motiv = clasifica(
        status=r.status_code, redirect_social=redirect_social, parcat=parcat,
        https_ok=https_ok, mobil_ok=mobil_ok, are_contact=are_contact, durata=durata,
    )
    return Verdict(**baza, **masurat, clasificare=clasificare, motiv=motiv)


def clasifica(*, status: int, redirect_social: bool, parcat: bool, https_ok: bool,
              mobil_ok: bool, are_contact: bool, durata: float) -> tuple[str, str]:
    """Regula de clasificare, scrisă explicit ca să poată fi contestată.

    Ordinea contează: motivele de mai sus sunt mai grave decât cele de mai jos, iar
    fiecare firmă primește un singur motiv — cel mai grav — ca să putem număra
    „câte site-uri sunt moarte și de ce" fără dublă numărare.
    """
    if status >= 400:
        return "site_mort", f"răspunde HTTP {status}"
    if redirect_social:
        return "site_mort", "redirecționează către o rețea socială"
    if parcat:
        return "site_mort", "pagină parcată sau fără conținut real"
    if not https_ok:
        return "site_mort", "fără HTTPS — browserul îl marchează nesigur"
    if not mobil_ok:
        # Peste 70% din căutările locale vin de pe telefon. Un site fără viewport
        # se afișează dezarhivat pe mobil și practic nu convertește.
        return "site_mort", "nu e adaptat pentru telefon (fără viewport)"
    if not are_contact:
        return "site_mort", "nicio cale de contact (fără formular, telefon sau email)"
    if durata > 8:
        return "site_mort", f"încarcă în {durata:.0f}s — prea lent ca să conteze"
    return "site_functional", "răspunde, e sigur, e mobil și are cale de contact"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--intrare", default="date/recensamant.csv")
    p.add_argument("--iesire", default="date/calitate_site.csv")
    p.add_argument("--limita", type=int, help="verifică doar primele N firme (pentru probe)")
    p.add_argument("--fire", type=int, default=12, help="câte verificări în paralel")
    args = p.parse_args()

    cale_in = Path(args.intrare)
    if not cale_in.exists():
        print(f"Nu găsesc {cale_in}. Rulează întâi scripts/recensamant.py", file=sys.stderr)
        return 2

    with cale_in.open(encoding="utf-8") as f:
        randuri = list(csv.DictReader(f))
    if args.limita:
        randuri = randuri[: args.limita]

    print(f"Verific {len(randuri)} firme cu {args.fire} fire...", file=sys.stderr)
    with ThreadPoolExecutor(max_workers=args.fire) as pool:
        verdicte = list(pool.map(verifica_unul, randuri))

    cale_out = Path(args.iesire)
    cale_out.parent.mkdir(parents=True, exist_ok=True)
    with cale_out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=[c.name for c in fields(Verdict)])
        w.writeheader()
        for v in verdicte:
            w.writerow(asdict(v))

    total = len(verdicte) or 1
    print(f"\n{len(verdicte)} verificate → {cale_out}\n", file=sys.stderr)
    for eticheta in ("fara_site", "site_mort", "site_functional"):
        n = sum(1 for v in verdicte if v.clasificare == eticheta)
        print(f"  {eticheta:<16} {n:>5}  ({n / total * 100:.1f}%)", file=sys.stderr)

    morti = [v for v in verdicte if v.clasificare == "site_mort"]
    if morti:
        print("\n  De ce sunt moarte:", file=sys.stderr)
        motive: dict[str, int] = {}
        for v in morti:
            motive[v.motiv] = motive.get(v.motiv, 0) + 1
        for motiv, n in sorted(motive.items(), key=lambda kv: -kv[1]):
            print(f"    {n:>5}  {motiv}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
