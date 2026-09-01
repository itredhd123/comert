# Rapoarte de research

Două rapoarte independente. Nu au legătură între ele — au fost făcute la momente și pe subiecte
diferite.

---

## 1. Model AI pe Fanvue — sustenabilitate și potențial financiar

*Septembrie 2026*

Cât de sustenabil e businessul cu o persona AI monetizată pe Fanvue, câți bani se pot face realist
ca operator solo din România, și de ce aproape tot ce circulă online pe tema asta e material de
marketing pentru cursuri.

| Fișier | Ce conține |
|---|---|
| `Model-AI-Fanvue-raport.pdf` | Raportul complet, 30 de pagini |
| `raport-model-ai-fanvue.html` | Aceeași versiune, ca pagină web |

**Scenariul analizat:** conținut explicit, operator singur care face personal chatul cu abonații.

| # | Secțiune |
|---|---|
| 00 | Verdict în opt puncte |
| 01 | Cum citești cifrele — grila A/B/C de încredere a surselor |
| 02 | Terenul de joc: Fanvue |
| 03 | De unde vin banii de fapt |
| 04 | Oameni care chiar fac asta — cazuri documentate |
| 05 | Distribuția reală a câștigurilor |
| 06 | Trei scenarii pe 12 luni |
| 07 | Costul real: timpul |
| 08 | Banii în mână: aritmetica ANAF |
| 09 | Cele 7 amenințări |
| 10 | Conformitate: ce te scoate din joc |
| 11 | Traficul după 31 august 2026 |
| 12 | Praguri de decizie |

**Metodologia care contează:** nișa e dominată de site-uri care vând cursuri, unelte și servicii de
agenție, iar cifrele lor spectaculoase sunt reclamă, nu date. Fiecare cifră din raport poartă o
etichetă de încredere — **A** verificabil (presă independentă, documente oficiale, legislație),
**B** raportat dar neconfirmat, **C** marketing, citat doar ca dovadă a ce se promite în piață.

---

## 2. Marketing eCommerce România

*August 2026*

Research pe marketingul celor mai mari jucători din comerțul online — românesc și internațional —
și playbook-ul organic derivat din el, pentru un magazin la început de drum.

| Fișier | Ce conține |
|---|---|
| `Contraofensiva-Organica-raport.pdf` | Raportul complet, 28 de pagini |
| `raport-marketing-ecommerce-ro.html` | Aceeași versiune, ca pagină web |

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

**Companii analizate.** România: eMAG, Dedeman, Altex, Notino, Answear, Freshful, Sezamo,
Temu/Shein/Trendyol. Internațional: Gymshark, Duolingo, Glossier, Liquid Death, Oatly, Warby Parker.

---

## Cum au fost generate PDF-urile

```
chromium --headless --print-to-pdf --no-pdf-header-footer print.html
```

unde `print.html` e raportul cu fonturile incluse ca data URI și o foaie de stil suplimentară
pentru print (A4, fără rail-ul de navigare, fără întreruperi în tabele și carduri).
