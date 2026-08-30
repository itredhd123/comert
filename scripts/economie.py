#!/usr/bin/env python3
"""Modelul de unit economics: ce formă are business-ul, la ce cifre.

Nu prezice viitorul. Face un lucru mai util: arată ce trebuie să fie adevărat ca
modelul să funcționeze, și de care variabilă atârnă de fapt totul. Răspunsul, în
aproape orice scenariu, e rata de plecare a clienților — nu prețul.

  python3 scripts/economie.py
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Ipoteze:
    abonament_lunar: float = 500.0     # lei, pachetul de prezență locală administrată
    taxa_initiala: float = 0.0         # lei, 0 = modelul „fără avans", ca la concurență
    churn_lunar: float = 0.04          # 4%/lună, tipic pentru agenții locale mici
    cost_livrare: float = 450.0        # lei, ~3h de muncă productizată
    cost_lunar_client: float = 60.0    # lei, găzduire + raport + timpul de suport
    inchideri_pe_luna: int = 8         # per om de vânzări
    cost_vanzator_lunar: float = 6000.0  # lei, salariu complet + taxe


def durata_medie_luni(churn: float) -> float:
    """Un client cu 4% șansă lunară de plecare stă în medie 1/0,04 = 25 de luni."""
    return 1 / churn if churn > 0 else float("inf")


def ltv(ip: Ipoteze) -> float:
    """Profitul brut adus de un client pe toată durata relației."""
    luni = durata_medie_luni(ip.churn_lunar)
    marja_lunara = ip.abonament_lunar - ip.cost_lunar_client
    return ip.taxa_initiala + marja_lunara * luni - ip.cost_livrare


def cac_maxim(ip: Ipoteze, raport: float = 3.0) -> float:
    """Cât îți poți permite să plătești ca să câștigi un client.

    Regula 3:1 e convenția din SaaS: sub ea, business-ul nu suportă
    nici greșeli, nici o echipă de vânzări plătită.
    """
    return ltv(ip) / raport


def proiectie(ip: Ipoteze, luni: int, vanzatori: int = 1) -> list[dict]:
    """Evoluția lună de lună. Clienții pleacă, deci creșterea nu e liniară."""
    randuri = []
    clienti = 0.0
    for luna in range(1, luni + 1):
        plecati = clienti * ip.churn_lunar
        clienti = clienti - plecati + ip.inchideri_pe_luna * vanzatori
        mrr = clienti * ip.abonament_lunar
        costuri = clienti * ip.cost_lunar_client + vanzatori * ip.cost_vanzator_lunar
        randuri.append({
            "luna": luna,
            "clienti": clienti,
            "plecati": plecati,
            "mrr": mrr,
            "profit": mrr - costuri,
        })
    return randuri


def plafon_clienti(ip: Ipoteze, vanzatori: int = 1) -> float:
    """Unde se oprește creșterea: când plecările egalează închiderile.

    Cifra asta e cea mai importantă din tot modelul. Cu 8 clienți noi pe lună și
    4% churn, business-ul se oprește singur la 200 de clienți, oricât ai insista.
    """
    return ip.inchideri_pe_luna * vanzatori / ip.churn_lunar


def lei(x: float) -> str:
    return f"{x:,.0f}".replace(",", ".") + " lei"


def main() -> None:
    ip = Ipoteze()

    print("IPOTEZE")
    print(f"  abonament               {lei(ip.abonament_lunar)}/lună")
    print(f"  churn                   {ip.churn_lunar * 100:.0f}%/lună "
          f"→ client mediu {durata_medie_luni(ip.churn_lunar):.0f} luni")
    print(f"  cost livrare            {lei(ip.cost_livrare)} o singură dată")
    print(f"  cost lunar per client   {lei(ip.cost_lunar_client)}")
    print(f"  închideri               {ip.inchideri_pe_luna}/lună/vânzător")

    print("\nVALOAREA UNUI CLIENT")
    print(f"  LTV (profit brut)       {lei(ltv(ip))}")
    print(f"  CAC maxim la 3:1        {lei(cac_maxim(ip))}")
    print("  ↑ atât îți poți permite să cheltui ca să câștigi un client.")
    print("    E mult. Concluzia: modelul nu moare din cost de achiziție,")
    print("    ci din faptul că nu reușești să închizi deloc.")

    print("\nDE CE ATÂRNĂ TOTUL — sensibilitatea la churn")
    print(f"  {'churn/lună':<12} {'durată':<10} {'LTV':<14} {'plafon clienți':<16} {'MRR la plafon'}")
    for churn in (0.02, 0.03, 0.04, 0.06, 0.08, 0.10):
        v = Ipoteze(churn_lunar=churn)
        plafon = plafon_clienti(v)
        print(f"  {churn * 100:>5.0f}%       {durata_medie_luni(churn):>5.0f} luni "
              f"{lei(ltv(v)):>14} {plafon:>12.0f}     {lei(plafon * v.abonament_lunar)}")
    print("  Diferența dintre 3% și 8% churn e diferența dintre un business")
    print("  de 1,6 milioane lei/an și unul de 600.000 lei/an. Aceeași muncă,")
    print("  aceiași clienți, aceeași ofertă — doar că unii rămân și alții pleacă.")

    print("\nPROIECȚIE — 1 vânzător, 8 închideri/lună")
    print(f"  {'luna':<7}{'clienți':>9}{'pleacă/lună':>14}{'MRR':>16}{'profit':>16}")
    p = proiectie(ip, 36)
    for r in p:
        if r["luna"] in (3, 6, 12, 18, 24, 36):
            print(f"  {r['luna']:<7}{r['clienti']:>9.0f}{r['plecati']:>14.1f}"
                  f"{lei(r['mrr']):>16}{lei(r['profit']):>16}")

    print(f"\n  Plafon teoretic: {plafon_clienti(ip):.0f} clienți "
          f"= {lei(plafon_clienti(ip) * ip.abonament_lunar)}/lună")

    print("\nCE SCHIMBĂ ORDINUL DE MĂRIME")
    scenarii = [
        ("de bază", Ipoteze(), 1),
        ("preț dublu (1.000 lei)", Ipoteze(abonament_lunar=1000), 1),
        ("churn înjumătățit (2%)", Ipoteze(churn_lunar=0.02), 1),
        ("3 vânzători", Ipoteze(), 3),
        ("3 vânzători + churn 2%", Ipoteze(churn_lunar=0.02), 3),
    ]
    print(f"  {'scenariu':<26}{'clienți la plafon':>19}{'MRR la plafon':>18}{'pe an':>18}")
    for nume, v, vanzatori in scenarii:
        plafon = plafon_clienti(v, vanzatori)
        mrr = plafon * v.abonament_lunar
        print(f"  {nume:<26}{plafon:>19.0f}{lei(mrr):>18}{lei(mrr * 12):>18}")

    print("\n  Prețul dublu dublează veniturile. Churnul înjumătățit le dublează și el,")
    print("  DAR e singurul care nu cere nimic de la client — doar ca serviciul să")
    print("  merite ținut. De asta modelul corect nu e „site”, ci ceva de care")
    print("  clientul nu se poate desprinde fără să piardă programări.")


if __name__ == "__main__":
    main()
