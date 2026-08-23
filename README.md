# Research: marketing eCommerce România

Research pe marketingul celor mai mari jucători din comerțul online — românesc și
internațional — și playbook-ul organic derivat din el, pentru un magazin la început de drum.

## Fișiere

| Fișier | Ce conține |
|---|---|
| `Contraofensiva-Organica-raport.pdf` | Raportul complet, 28 de pagini, gata de citit sau printat |
| `raport-marketing-ecommerce-ro.html` | Aceeași versiune, ca pagină web |

## Structură

| # | Secțiune |
|---|---|
| 00 | Sinteză — opt concluzii |
| 01 | Terenul de joc — cifrele pieței RO în 2026 |
| 02 | Cum fac marketing cei mari — 13 companii decodate |
| 03 | Cele 7 tipare comune |
| 04 | Asimetria ta — ce nu poți copia, ce ai tu în plus |
| 05 | Alegerea produsului — 7 filtre cu praguri |
| 06 | Playbook 0→12 luni — patru faze |
| 07 | Motorul de conținut — formate, cadență, deschideri |
| 08 | SEO în epoca AI — AEO și GEO |
| 09 | Retenție — cele 6 fluxuri obligatorii |
| 10 | Canale gratuite specifice României |
| 11 | Măsurare |
| 12 | Capcane |
| 13 | Planul de 90 de zile |

## Companii analizate

**România:** eMAG, Dedeman, Altex, Notino, Answear, Freshful, Sezamo, Temu/Shein/Trendyol.
**Internațional:** Gymshark, Duolingo, Glossier, Liquid Death, Oatly, Warby Parker.

## Surse

Peste 40 de surse, verificate în august 2026 — între altele MerchantPro eCommerce Insights 2026,
DataReportal Digital 2026 Romania, Brand Finance, Sameday, Klaviyo, ARMO și studiul ASE privind
platformele non-UE. Lista completă e la finalul raportului.

## Cum a fost generat PDF-ul

```
chromium --headless --print-to-pdf --no-pdf-header-footer print.html
```

unde `print.html` e raportul cu fonturile incluse ca data URI și o foaie de stil suplimentară
pentru print (A4, fără rail-ul de navigare, fără întreruperi în tabele și carduri).
