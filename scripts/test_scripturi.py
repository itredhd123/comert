#!/usr/bin/env python3
"""Teste offline pentru instrumentele de recensământ.

Nu ating rețeaua. Scopul lor e să garanteze că algoritmul de acoperire e corect
ÎNAINTE să cheltuim apeluri plătite pe el — o subdiviziune greșită nu dă eroare, dă
pur și simplu cifre mai mici decât realitatea, iar asta n-ai cum s-o observi din CSV.

  python3 scripts/test_scripturi.py
"""

from __future__ import annotations

import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from recensamant import (
    Client, Dreptunghi, Firma, PRAG_SATURARE, cauta_adaptiv, cheie_deduplicare,
    dreptunghi_pentru_oras, normalizeaza, recenseaza_celula,
)
from config import ORASE_DUPA_SLUG, VERTICALE_DUPA_SLUG
from verifica_site import clasifica

esecuri: list[str] = []


def verifica(conditie: bool, descriere: str) -> None:
    if conditie:
        print(f"  ok    {descriere}")
    else:
        print(f"  EȘEC  {descriere}")
        esecuri.append(descriere)


class ClientFals(Client):
    """Un Google Maps de jucărie, cu o lume de firme cunoscută dinainte.

    Respectă limita reală a API-ului: maximum 60 de rezultate per interogare, oricâte
    firme ar fi în zonă. Fără limita asta testul n-ar demonstra nimic.
    """

    def __init__(self, lume: list[dict]):
        super().__init__(cheie="fals", pauza_s=0, verbose=False)
        self.lume = lume
        self.apeluri = 0

    def cauta_tot(self, interogare: str, zona: Dreptunghi) -> list[dict]:
        self.apeluri += 1
        induntru = [
            loc for loc in self.lume
            if zona.sud <= loc["location"]["latitude"] <= zona.nord
            and zona.vest <= loc["location"]["longitude"] <= zona.est
        ]
        return induntru[:PRAG_SATURARE]


def firma_falsa(i: int, lat: float, lng: float, site: bool, status: str = "OPERATIONAL") -> dict:
    loc = {
        "id": f"place_{i}",
        "displayName": {"text": f"Firma {i}"},
        "formattedAddress": f"Strada {i}, Cluj-Napoca",
        "nationalPhoneNumber": f"07{i:08d}",
        "location": {"latitude": lat, "longitude": lng},
        "businessStatus": status,
        "userRatingCount": i % 50,
    }
    if site:
        loc["websiteUri"] = f"https://firma{i}.ro"
    return loc


def test_subdiviziunea_depaseste_plafonul_de_60():
    """Testul care contează: fără subdiviziune am vedea 60 de firme din 400."""
    rng = random.Random(42)
    oras = ORASE_DUPA_SLUG["cluj"]
    zona = dreptunghi_pentru_oras(oras)
    lume = [
        firma_falsa(i, rng.uniform(zona.sud, zona.nord), rng.uniform(zona.vest, zona.est),
                    site=i % 3 == 0)
        for i in range(400)
    ]

    client = ClientFals(lume)
    fara_subdiviziune = client.cauta_tot("service auto", zona)
    gasite = cauta_adaptiv(client, "service auto", zona, verbose=False)

    verifica(len(fara_subdiviziune) == PRAG_SATURARE,
             f"o singură interogare se blochează la {PRAG_SATURARE} rezultate")
    verifica(len(gasite) > 300,
             f"subdiviziunea adaptivă găsește {len(gasite)}/400 firme (fără ea: 60)")
    verifica(len(gasite) == len({g for g in gasite}),
             "rezultatele sunt deduplicate după place_id")


def test_zona_rara_nu_se_subdivide():
    """Subdiviziunea costă apeluri. Nu trebuie declanșată unde nu e nevoie."""
    oras = ORASE_DUPA_SLUG["alba-iulia"]
    zona = dreptunghi_pentru_oras(oras)
    lume = [firma_falsa(i, oras.lat, oras.lng, site=False) for i in range(5)]

    client = ClientFals(lume)
    gasite = cauta_adaptiv(client, "service auto", zona, verbose=False)

    verifica(len(gasite) == 5, "găsește toate cele 5 firme dintr-o zonă rară")
    verifica(client.apeluri == 1, f"nu risipește apeluri: {client.apeluri} apel, nu 5")


def test_firmele_inchise_sunt_excluse():
    oras = ORASE_DUPA_SLUG["cluj"]
    lume = [
        firma_falsa(1, oras.lat, oras.lng, site=False),
        firma_falsa(2, oras.lat, oras.lng, site=True, status="CLOSED_PERMANENTLY"),
        firma_falsa(3, oras.lat, oras.lng, site=False),
    ]
    client = ClientFals(lume)
    firme = recenseaza_celula(client, VERTICALE_DUPA_SLUG["service-auto"], oras, verbose=False)

    verifica(len(firme) == 2, "firma închisă definitiv nu intră în numitor")
    verifica(all(f.status != "CLOSED_PERMANENTLY" for f in firme),
             "nicio firmă închisă în rezultat")


def test_deduplicarea_dupa_telefon():
    """Aceeași firmă, două place_id-uri — se întâmplă la punctele de lucru."""
    a = normalizeaza(
        {"id": "x1", "displayName": {"text": "Service Ion"}, "nationalPhoneNumber": "0721 111 222",
         "formattedAddress": "Str. A 1", "location": {}}, "service-auto", "cluj", "q")
    b = normalizeaza(
        {"id": "x2", "displayName": {"text": "Service Ion SRL"}, "nationalPhoneNumber": "0721111222",
         "formattedAddress": "Strada A nr 1", "location": {}}, "service-auto", "cluj", "q")

    verifica(cheie_deduplicare(a) == cheie_deduplicare(b),
             "același telefon scris diferit dă aceeași cheie de deduplicare")

    c = normalizeaza(
        {"id": "x3", "displayName": {"text": "Service Ion"}, "formattedAddress": "Str. A 1",
         "location": {}}, "service-auto", "cluj", "q")
    d = normalizeaza(
        {"id": "x4", "displayName": {"text": "Service Vasile"}, "formattedAddress": "Str. B 2",
         "location": {}}, "service-auto", "cluj", "q")
    verifica(cheie_deduplicare(c) != cheie_deduplicare(d),
             "firme diferite fără telefon rămân distincte")


def test_geometria_dreptunghiului():
    oras = ORASE_DUPA_SLUG["bucuresti"]
    zona = dreptunghi_pentru_oras(oras)
    verifica(23 < zona.latura_km() < 25,
             f"București: cutie de {zona.latura_km():.1f} km pentru rază de 12 km")

    sferturi = zona.imparte_in_patru()
    verifica(len(sferturi) == 4, "împărțirea dă exact patru sferturi")
    verifica(abs(sferturi[0].latura_km() - zona.latura_km() / 2) < 0.01,
             "fiecare sfert are jumătate din latură")
    verifica(all(zona.sud <= s.sud and s.nord <= zona.nord for s in sferturi),
             "sferturile stau în interiorul zonei-părinte")


def test_clasificarea_site_urilor():
    cazuri = [
        (dict(status=200, redirect_social=False, parcat=False, https_ok=True,
              mobil_ok=True, are_contact=True, durata=1.0), "site_functional"),
        (dict(status=404, redirect_social=False, parcat=False, https_ok=True,
              mobil_ok=True, are_contact=True, durata=1.0), "site_mort"),
        (dict(status=200, redirect_social=True, parcat=False, https_ok=True,
              mobil_ok=True, are_contact=True, durata=1.0), "site_mort"),
        (dict(status=200, redirect_social=False, parcat=True, https_ok=True,
              mobil_ok=True, are_contact=True, durata=1.0), "site_mort"),
        (dict(status=200, redirect_social=False, parcat=False, https_ok=False,
              mobil_ok=True, are_contact=True, durata=1.0), "site_mort"),
        (dict(status=200, redirect_social=False, parcat=False, https_ok=True,
              mobil_ok=False, are_contact=True, durata=1.0), "site_mort"),
        (dict(status=200, redirect_social=False, parcat=False, https_ok=True,
              mobil_ok=True, are_contact=False, durata=1.0), "site_mort"),
        (dict(status=200, redirect_social=False, parcat=False, https_ok=True,
              mobil_ok=True, are_contact=True, durata=20.0), "site_mort"),
    ]
    for intrare, asteptat in cazuri:
        obtinut, motiv = clasifica(**intrare)
        verifica(obtinut == asteptat, f"clasificare {asteptat}: {motiv}")


def main() -> int:
    teste = [
        ("Subdiviziunea depășește plafonul de 60", test_subdiviziunea_depaseste_plafonul_de_60),
        ("Zonele rare nu se subdivid", test_zona_rara_nu_se_subdivide),
        ("Firmele închise sunt excluse", test_firmele_inchise_sunt_excluse),
        ("Deduplicarea după telefon", test_deduplicarea_dupa_telefon),
        ("Geometria dreptunghiurilor", test_geometria_dreptunghiului),
        ("Clasificarea site-urilor", test_clasificarea_site_urilor),
    ]
    for nume, fn in teste:
        print(f"\n{nume}")
        fn()

    print()
    if esecuri:
        print(f"{len(esecuri)} eșecuri:")
        for e in esecuri:
            print(f"  - {e}")
        return 1
    print("Toate testele trec.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
