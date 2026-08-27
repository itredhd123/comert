# Research: marketing eCommerce România

Research pe marketingul celor mai mari jucători din comerțul online — românesc și
internațional — și playbook-ul organic derivat din el, pentru un magazin la început de drum.
Plus documentul de decizie care aplică filtrele pe un profil concret de fondator, și scanarea
de produse care testează ipoteza „ce merge în afară și n-a ajuns încă la noi”.

## Fișiere

| Fișier | Ce conține |
|---|---|
| `Contraofensiva-Organica-raport.pdf` | Raportul de research, 28 de pagini, gata de citit sau printat |
| `raport-marketing-ecommerce-ro.html` | Aceeași versiune, ca pagină web |
| `Pariul-pe-pisici-raport.pdf` | Documentul de decizie, 18 pagini |
| `decizia-de-business.html` | Aceeași versiune, ca pagină web |
| `Fereastra-de-doi-ani-raport.pdf` | Scanarea de produse, 16 pagini |
| `vanatoarea-de-produse.html` | Aceeași versiune, ca pagină web |

## Raportul de research — structură

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

### Companii analizate

**România:** eMAG, Dedeman, Altex, Notino, Answear, Freshful, Sezamo, Temu/Shein/Trendyol.
**Internațional:** Gymshark, Duolingo, Glossier, Liquid Death, Oatly, Warby Parker.

## Documentul de decizie — structură

Aplică cele 7 filtre din raport pe un profil dat: 15.000 lei capital, ~17 ore pe săptămână
în paralel cu un job, fără avantaj de start, produs fizic vândut online.

| # | Secțiune |
|---|---|
| 00 | Verdictul |
| 01 | Ce exclude profilul — restricțiile ca filtru |
| 02 | Nouă candidate, punctate pe cele 7 filtre |
| 03 | Nișa, exact — public, problemă, produs de start |
| 04 | De ce ține — patru mecanisme, cu cifre |
| 05 | Cum intri cu 15.000 lei — distribuție, apoi etichetă proprie |
| 06 | Economia unitară — pe comandă, în ambele faze |
| 07 | Bugetul de start, linie cu linie |
| 08 | Bugetul de timp — 17 ore, pe blocuri |
| 09 | Primele 90 de zile, cu praguri |
| 10 | Alternativele, dacă subiectul nu te atrage |
| 11 | Ce să nu faci |
| 12 | Riscurile reale, cu contramăsuri |
| 13 | Când te oprești — pragurile de abandon |

## Scanarea de produse — structură

Testează ipoteza „adu un produs care merge în afară și nu există încă în România”: unsprezece
produse cu creștere documentată extern, verificate unul câte unul pentru disponibilitatea locală.

| # | Secțiune |
|---|---|
| 00 | Ce am găsit — 6 din 11 erau deja aici |
| 01 | Exemplele tale, disecate |
| 02 | Cele trei stadii de sosire în România |
| 03 | Scanarea — 11 produse, cu dovada pentru fiecare |
| 04 | Ce te protejează de fapt — cele 4 ziduri |
| 05 | Metoda, pas cu pas — 90 de minute pe săptămână |
| 06 | Filtrul de siguranță — trendurile care se prăbușesc |
| 07 | Cine a rămas în picioare — 4 candidați punctați |
| 08 | Recomandarea |
| 09 | Economia |
| 10 | Primele 30 de zile |
| 11 | Comparația cu recomandarea precedentă |
| 12 | Capcanele acestui joc |

## Surse

Raportul de research: peste 40 de surse, verificate în august 2026 — între altele MerchantPro
eCommerce Insights 2026, DataReportal Digital 2026 Romania, Brand Finance, Sameday, Klaviyo,
ARMO și studiul ASE privind platformele non-UE.

Documentul de decizie adaugă surse pe piața de pet food din România (RetailZoom, Euromonitor,
Progresiv) și pe cadrul de înregistrare sanitar-veterinară (ANSVSA, DSVSA).

Scanarea de produse adaugă rapoarte de piață pentru fiecare categorie testată, două surse
medicale care elimină un candidat (recenzia sistematică PLOS One din 2025 privind lipirea gurii
în somn) și verificările de disponibilitate în România, cu link către listarea găsită. Listele
complete sunt la finalul fiecărui document.

## Cum au fost generate PDF-urile

```
chromium --headless --print-to-pdf --no-pdf-header-footer print.html
```

unde `print.html` e raportul cu fonturile incluse ca data URI și o foaie de stil suplimentară
pentru print (A4, fără rail-ul de navigare, fără întreruperi în tabele și carduri).
