#!/usr/bin/env python3
"""Recensământ: câte firme dintr-o verticală au site și câte nu.

Cifra asta nu e publicată nicăieri — statisticile oficiale se opresc la nivelul
„IMM-urile din România" agregat. Singurul mod de a o afla e s-o numeri, firmă cu firmă.

Instrumentul folosește Google Places API (New), Text Search. Nu face scraping pe
HTML-ul Google Maps: încalcă termenii de utilizare, iar datele sunt oricum murdare.

  export GOOGLE_MAPS_API_KEY=...
  python3 scripts/recensamant.py --dry-run              # planul, fără apeluri
  python3 scripts/recensamant.py --verticala service-auto --oras cluj
  python3 scripts/recensamant.py                        # tot: 4 verticale x 7 orașe

Problema centrală de acoperire
------------------------------
Text Search întoarce maximum 60 de rezultate per interogare (3 pagini x 20). În
București sunt mult mai multe service-uri auto decât atât, deci o singură interogare
ar returna un eșantion arbitrar și ar subestima piața fără să ne dăm seama.

Soluția e subdiviziunea adaptivă: pornim cu un dreptunghi peste tot orașul și, ori de
câte ori o zonă întoarce numărul maxim de rezultate (semn că e saturată și mai sunt
firme pe care nu le vedem), o împărțim în patru și reluăm. Zonele rare nu se
subdivid, deci nu plătim apeluri degeaba.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from config import VERTICALE, ORASE, VERTICALE_DUPA_SLUG, ORASE_DUPA_SLUG, Oras, Verticala

ENDPOINT = "https://places.googleapis.com/v1/places:searchText"

CAMPURI = (
    "places.id,"
    "places.displayName,"
    "places.formattedAddress,"
    "places.websiteUri,"
    "places.nationalPhoneNumber,"
    "places.rating,"
    "places.userRatingCount,"
    "places.businessStatus,"
    "places.location,"
    "places.primaryType,"
    "nextPageToken"
)

# Text Search întoarce cel mult 20 de rezultate pe pagină și 3 pagini.
MAX_PAGINI = 3
REZULTATE_PER_PAGINA = 20
PRAG_SATURARE = MAX_PAGINI * REZULTATE_PER_PAGINA

# Adâncimea maximă de subdiviziune. 3 înseamnă că un oraș se poate împărți în
# până la 4^3 = 64 de zone — suficient chiar și pentru București.
ADANCIME_MAX = 3

# Costul estimat per 1000 de apeluri. `websiteUri`, `rating` și `userRatingCount`
# sunt câmpuri din tierul Enterprise, deci apelul se facturează la tariful Enterprise.
# ATENȚIE: Google a schimbat structura de SKU-uri și prețuri în 2025 și există o cotă
# lunară gratuită. Verifică tariful curent înainte de a te baza pe estimare.
USD_PER_1000_APELURI = 35.0

METRI_PER_GRAD_LAT = 111_320.0


@dataclass
class Firma:
    verticala: str
    oras: str
    place_id: str
    nume: str
    adresa: str
    telefon: str
    website: str
    are_site: int
    rating: str
    nr_recenzii: str
    status: str
    lat: str
    lng: str
    tip_principal: str
    interogare: str


@dataclass
class Dreptunghi:
    """Zonă geografică, în formatul cerut de `locationRestriction`."""

    sud: float
    vest: float
    nord: float
    est: float

    def ca_json(self) -> dict:
        return {
            "rectangle": {
                "low": {"latitude": self.sud, "longitude": self.vest},
                "high": {"latitude": self.nord, "longitude": self.est},
            }
        }

    def imparte_in_patru(self) -> list["Dreptunghi"]:
        lat_mij = (self.sud + self.nord) / 2
        lng_mij = (self.vest + self.est) / 2
        return [
            Dreptunghi(self.sud, self.vest, lat_mij, lng_mij),
            Dreptunghi(self.sud, lng_mij, lat_mij, self.est),
            Dreptunghi(lat_mij, self.vest, self.nord, lng_mij),
            Dreptunghi(lat_mij, lng_mij, self.nord, self.est),
        ]

    def latura_km(self) -> float:
        return (self.nord - self.sud) * METRI_PER_GRAD_LAT / 1000


def dreptunghi_pentru_oras(oras: Oras) -> Dreptunghi:
    """Cutia care încadrează cercul de rază `raza_m` în jurul centrului orașului."""
    d_lat = oras.raza_m / METRI_PER_GRAD_LAT
    d_lng = oras.raza_m / (METRI_PER_GRAD_LAT * math.cos(math.radians(oras.lat)))
    return Dreptunghi(oras.lat - d_lat, oras.lng - d_lng, oras.lat + d_lat, oras.lng + d_lng)


class Client:
    """Client minimal peste Places API, cu reîncercări și contorizare de apeluri."""

    def __init__(self, cheie: str, pauza_s: float = 0.12, verbose: bool = True):
        self.cheie = cheie
        self.pauza_s = pauza_s
        self.verbose = verbose
        self.apeluri = 0

    def cauta(self, interogare: str, zona: Dreptunghi, page_token: str | None = None) -> dict:
        corp = {
            "textQuery": interogare,
            "locationRestriction": zona.ca_json(),
            "pageSize": REZULTATE_PER_PAGINA,
            "languageCode": "ro",
            "regionCode": "RO",
        }
        if page_token:
            corp["pageToken"] = page_token

        cerere = urllib.request.Request(
            ENDPOINT,
            data=json.dumps(corp).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "X-Goog-Api-Key": self.cheie,
                "X-Goog-FieldMask": CAMPURI,
            },
            method="POST",
        )

        for incercare in range(5):
            try:
                self.apeluri += 1
                with urllib.request.urlopen(cerere, timeout=30) as raspuns:
                    time.sleep(self.pauza_s)
                    return json.loads(raspuns.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                corp_eroare = e.read().decode("utf-8", "replace")[:500]
                # 429 = throttling, 5xx = eroare temporară. Restul sunt erori reale
                # (cheie greșită, API neactivat, field mask invalid) și nu au rost reîncercate.
                if e.code in (429, 500, 502, 503, 504) and incercare < 4:
                    asteptare = 2 ** incercare
                    if self.verbose:
                        print(f"    HTTP {e.code}, reîncerc în {asteptare}s", file=sys.stderr)
                    time.sleep(asteptare)
                    continue
                raise RuntimeError(f"Places API a răspuns HTTP {e.code}: {corp_eroare}") from e
            except urllib.error.URLError as e:
                if incercare < 4:
                    time.sleep(2 ** incercare)
                    continue
                raise RuntimeError(f"Nu am putut contacta Places API: {e.reason}") from e

        raise RuntimeError("Reîncercări epuizate")

    def cauta_tot(self, interogare: str, zona: Dreptunghi) -> list[dict]:
        """Toate paginile pentru o interogare într-o zonă (maximum 60 de rezultate)."""
        rezultate: list[dict] = []
        token: str | None = None
        for _ in range(MAX_PAGINI):
            raspuns = self.cauta(interogare, zona, token)
            rezultate.extend(raspuns.get("places", []))
            token = raspuns.get("nextPageToken")
            if not token:
                break
        return rezultate


def cauta_adaptiv(
    client: Client, interogare: str, zona: Dreptunghi, adancime: int = 0, verbose: bool = True
) -> dict[str, dict]:
    """Caută într-o zonă, subdivizând-o dacă rezultatele se saturează.

    Întoarce un dicționar place_id -> loc, deci deduplicarea între zone și între
    pagini se face automat (o firmă la granița dintre două zone apare o singură dată).
    """
    locuri = client.cauta_tot(interogare, zona)
    gasite = {loc["id"]: loc for loc in locuri if "id" in loc}

    saturat = len(locuri) >= PRAG_SATURARE
    if saturat and adancime < ADANCIME_MAX:
        if verbose:
            print(
                f"    {'  ' * adancime}zonă saturată ({len(locuri)} rezultate, "
                f"~{zona.latura_km():.1f} km) — o împart în patru",
                file=sys.stderr,
            )
        for sub in zona.imparte_in_patru():
            gasite.update(cauta_adaptiv(client, interogare, sub, adancime + 1, verbose))

    return gasite


def normalizeaza(loc: dict, verticala: str, oras: str, interogare: str) -> Firma:
    website = loc.get("websiteUri", "") or ""
    pozitie = loc.get("location", {}) or {}
    return Firma(
        verticala=verticala,
        oras=oras,
        place_id=loc.get("id", ""),
        nume=(loc.get("displayName") or {}).get("text", ""),
        adresa=loc.get("formattedAddress", "") or "",
        telefon=loc.get("nationalPhoneNumber", "") or "",
        website=website,
        are_site=1 if website else 0,
        rating=str(loc.get("rating", "")),
        nr_recenzii=str(loc.get("userRatingCount", "")),
        status=loc.get("businessStatus", "") or "",
        lat=str(pozitie.get("latitude", "")),
        lng=str(pozitie.get("longitude", "")),
        tip_principal=loc.get("primaryType", "") or "",
        interogare=interogare,
    )


def cheie_deduplicare(f: Firma) -> str:
    """A doua rundă de deduplicare, după place_id.

    Aceeași firmă apare uneori de două ori în Google, cu place_id-uri diferite, dacă
    are punct de lucru înregistrat separat. Telefonul e cel mai bun discriminator;
    unde lipsește, cădem pe nume plus primii 30 de caracteri din adresă.
    """
    telefon = "".join(c for c in f.telefon if c.isdigit())
    if len(telefon) >= 9:
        return f"tel:{telefon[-9:]}"
    return f"nume:{f.nume.strip().lower()}|{f.adresa.strip().lower()[:30]}"


def recenseaza_celula(
    client: Client, verticala: Verticala, oras: Oras, verbose: bool = True
) -> list[Firma]:
    """O celulă = o verticală într-un oraș, pe toate interogările verticalei."""
    zona = dreptunghi_pentru_oras(oras)
    brute: dict[str, Firma] = {}

    for interogare in verticala.interogari:
        if verbose:
            print(f'  „{interogare}”', file=sys.stderr)
        gasite = cauta_adaptiv(client, interogare, zona, verbose=verbose)
        for place_id, loc in gasite.items():
            # Prima interogare care găsește o firmă o și revendică — păstrăm
            # formularea care a găsit-o, e utilă la depanare.
            if place_id not in brute:
                brute[place_id] = normalizeaza(loc, verticala.slug, oras.slug, interogare)

    # Firmele închise definitiv nu sunt clienți. Le scoatem, altfel umflă numitorul.
    active = [f for f in brute.values() if f.status != "CLOSED_PERMANENTLY"]

    unice: dict[str, Firma] = {}
    for f in active:
        unice.setdefault(cheie_deduplicare(f), f)

    if verbose:
        dubluri = len(active) - len(unice)
        print(
            f"  → {len(unice)} firme unice "
            f"({len(brute)} brute, {len(brute) - len(active)} închise, {dubluri} dubluri)",
            file=sys.stderr,
        )
    return list(unice.values())


def scrie_csv(firme: list[Firma], cale: Path) -> None:
    cale.parent.mkdir(parents=True, exist_ok=True)
    with cale.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(asdict(firme[0]).keys()) if firme else
                                [c for c in Firma.__dataclass_fields__])
        writer.writeheader()
        for firma in firme:
            writer.writerow(asdict(firma))


def plan_dry_run(verticale: list[Verticala], orase: list[Oras]) -> None:
    """Ce s-ar întâmpla, fără să apelăm nimic."""
    print("Plan de recensământ\n")
    total_min = 0
    for oras in orase:
        zona = dreptunghi_pentru_oras(oras)
        print(f"{oras.nume} — zonă de {zona.latura_km():.1f} x {zona.latura_km():.1f} km")
        for v in verticale:
            # Minimul: o interogare = până la 3 apeluri, fără subdiviziune.
            minim = len(v.interogari) * MAX_PAGINI
            total_min += minim
            print(f"    {v.nume:<38} ≥ {minim:>4} apeluri")
    maxim = total_min * (1 + 4 + 16)  # dacă fiecare zonă s-ar satura până la adâncimea 2
    print(f"\nApeluri: minimum ~{total_min}, maximum ~{maxim} dacă totul se saturează.")
    print(f"Cost estimat: {total_min / 1000 * USD_PER_1000_APELURI:.2f} – "
          f"{maxim / 1000 * USD_PER_1000_APELURI:.2f} USD "
          f"(la {USD_PER_1000_APELURI} USD/1000, tier Enterprise)")
    print("\nVerifică tariful curent și cota gratuită lunară înainte de rulare —")
    print("Google a schimbat SKU-urile în 2025 și e posibil ca rularea să fie gratuită.")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--verticala", action="append", help="slug de verticală (implicit: toate)")
    p.add_argument("--oras", action="append", help="slug de oraș (implicit: toate)")
    p.add_argument("--iesire", default="date/recensamant.csv", help="fișierul CSV de ieșire")
    p.add_argument("--dry-run", action="store_true", help="arată planul, nu apela API-ul")
    p.add_argument("--liniste", action="store_true", help="fără progres pe stderr")
    args = p.parse_args()

    try:
        verticale = ([VERTICALE_DUPA_SLUG[s] for s in args.verticala]
                     if args.verticala else list(VERTICALE))
        orase = ([ORASE_DUPA_SLUG[s] for s in args.oras] if args.oras else list(ORASE))
    except KeyError as e:
        print(f"Slug necunoscut: {e}. Verticale: "
              f"{', '.join(VERTICALE_DUPA_SLUG)}. Orașe: {', '.join(ORASE_DUPA_SLUG)}",
              file=sys.stderr)
        return 2

    if args.dry_run:
        plan_dry_run(verticale, orase)
        return 0

    cheie = os.environ.get("GOOGLE_MAPS_API_KEY")
    if not cheie:
        print("Lipsește GOOGLE_MAPS_API_KEY.\n\n"
              "  export GOOGLE_MAPS_API_KEY=...\n\n"
              "Cheia are nevoie de Places API (New) activat. Rulează întâi cu --dry-run\n"
              "ca să vezi câte apeluri ar însemna.", file=sys.stderr)
        return 2

    verbose = not args.liniste
    client = Client(cheie, verbose=verbose)
    toate: list[Firma] = []

    for oras in orase:
        for v in verticale:
            if verbose:
                print(f"\n{v.nume} — {oras.nume}", file=sys.stderr)
            toate.extend(recenseaza_celula(client, v, oras, verbose))

    cale = Path(args.iesire)
    scrie_csv(toate, cale)

    fara_site = sum(1 for f in toate if not f.are_site)
    print(f"\n{len(toate)} firme scrise în {cale}", file=sys.stderr)
    if toate:
        print(f"{fara_site} fără site ({fara_site / len(toate) * 100:.1f}%)", file=sys.stderr)
    print(f"{client.apeluri} apeluri API "
          f"(~{client.apeluri / 1000 * USD_PER_1000_APELURI:.2f} USD)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
