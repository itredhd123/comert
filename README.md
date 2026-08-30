# Research de piață — România

Două proiecte de cercetare, separate.

| Proiect | Întrebarea la care răspunde |
|---|---|
| [Validarea pieței de site-uri](#validarea-pieței-de-site-uri) | Merită să vinzi prezență online firmelor mici? Pe ce verticală? |
| [Marketing eCommerce](#marketing-ecommerce) | Cum fac marketing cei mari din comerțul online și ce se poate copia |

---

## Validarea pieței de site-uri

Ipoteza: în România sunt multe firme mici fără site, cărora li se poate vinde unul.
Întrebarea reală nu e dacă ele există — evident că da — ci **pe ce verticală și în ce
oraș** densitatea lor se suprapune peste clienți care își permit să plătească lunar.

Cifra aia nu e publicată nicăieri. Statisticile publice se opresc la nivelul agregat
„IMM-urile din România", fără defalcare pe cod CAEN și județ. Trebuie măsurată.

### Fișiere

| Fișier | Ce conține |
|---|---|
| `raport-validare-piata.html` | Raportul, etapa 1: ce s-a putut afla din surse publice |
| `raport-validare-piata.pdf` | Aceeași versiune, 12 pagini, pentru citit sau printat |
| `plan-invatare.html` / `.pdf` | Curriculumul de 12 săptămâni: ce skill-uri, în ce ordine, din ce surse |
| `scripts/config.py` | Verticalele candidate și orașele din eșantion |
| `scripts/recensamant.py` | Numărătoarea propriu-zisă, prin Google Places API |
| `scripts/verifica_site.py` | Clasificarea site-urilor găsite: mort sau funcțional |
| `scripts/economie.py` | Modelul de unit economics, cu ipotezele la vedere — impozit și comisioane incluse |
| `scripts/test_scripturi.py` | Teste offline, fără apeluri de rețea |
| `scripts/build_pdf.py` | Randarea PDF-ului, cu fonturile încorporate |

### Stadiu

Etapa 1 (surse publice) e gata. Etapa 2 (recensământul) așteaptă o cheie
**Google Maps Platform** cu Places API (New) activat:

```
export GOOGLE_MAPS_API_KEY=...
python3 scripts/recensamant.py --dry-run          # planul și costul, fără apeluri
python3 scripts/recensamant.py --verticala service-auto --oras cluj
python3 scripts/verifica_site.py --limita 50
```

`verifica_site.py` contactează site-uri arbitrare, deci are nevoie de o mașină cu acces
normal la internet — într-un mediu cu egress restricționat va raporta totul ca mort.

### Cum funcționează recensământul

Text Search întoarce maximum 60 de rezultate per interogare, mult sub numărul real de
firme dintr-un oraș mare. O interogare simplă ar returna un eșantion arbitrar și ar
subestima piața **fără niciun semnal că o face** — genul de eroare care nu dă mesaj de
eroare, doar cifre greșite.

Soluția e subdiviziunea adaptivă: pornim cu un dreptunghi peste tot orașul și, ori de
câte ori o zonă se saturează, o împărțim în patru și reluăm. Zonele rare rămân
neîmpărțite, deci nu se plătesc apeluri degeaba. Testele arată că metoda găsește 400 din
400 de firme acolo unde o interogare simplă s-ar opri la 60.

```
python3 scripts/test_scripturi.py
python3 scripts/economie.py
```

---

## Marketing eCommerce

Research pe marketingul celor mai mari jucători din comerțul online — românesc și
internațional — și playbook-ul organic derivat din el, pentru un magazin la început de drum.

### Fișiere

| Fișier | Ce conține |
|---|---|
| `Contraofensiva-Organica-raport.pdf` | Raportul complet, 28 de pagini, gata de citit sau printat |
| `raport-marketing-ecommerce-ro.html` | Aceeași versiune, ca pagină web |

### Structură

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

### Surse

Peste 40 de surse, verificate în august 2026 — între altele MerchantPro eCommerce Insights 2026,
DataReportal Digital 2026 Romania, Brand Finance, Sameday, Klaviyo, ARMO și studiul ASE privind
platformele non-UE. Lista completă e la finalul raportului.

---

## Randarea PDF-urilor

```
python3 scripts/build_pdf.py raport-validare-piata.html
```

Scriptul descarcă fonturile de la Google Fonts, le încorporează ca data URI și randează
prin Chromium headless. Fără încorporare, PDF-ul iese cu fonturi de rezervă. Adaugă și o
declarație de charset: la peste un megaoctet, din care majoritatea e base64, euristica de
detecție a codificării din Chromium ratează și toate diacriticele ies mojibake.
