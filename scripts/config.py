"""Configurația recensământului: ce verticale căutăm și în ce orașe.

Verticalele sunt definite prin interogări în limbaj natural, nu prin tipuri Google.
Motivul: tipurile Google (`car_repair`, `dentist`) sunt prea largi sau prea înguste
față de cum se numesc firmele în România, iar Text Search se descurcă mai bine cu
formularea pe care ar folosi-o un client real.

Fiecare verticală are mai multe interogări, pentru că o singură formulare ratează
sistematic o parte din piață — „service auto" nu prinde vulcanizările, „dentist" nu
prinde clinicile care se numesc „centru de implantologie".
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Verticala:
    slug: str
    nume: str
    interogari: tuple[str, ...]
    coduri_caen: tuple[str, ...]
    nota: str = ""


@dataclass(frozen=True)
class Oras:
    slug: str
    nume: str
    lat: float
    lng: float
    # Raza în metri a zonei acoperite. Orașele mari se împart în dale (vezi tiling.py),
    # pentru că Text Search întoarce maximum 60 de rezultate per interogare.
    raza_m: int
    populatie: int
    mic: bool = False


VERTICALE: tuple[Verticala, ...] = (
    Verticala(
        slug="service-auto",
        nume="Service auto",
        interogari=(
            "service auto",
            "reparatii auto",
            "vulcanizare",
            "service auto electric",
            "tinichigerie auto",
        ),
        coduri_caen=("4520",),
        nota="Nevoie recurentă (revizii, ITP), număr foarte mare de firme.",
    ),
    Verticala(
        slug="stomatologie",
        nume="Stomatologie / clinici dentare",
        interogari=(
            "cabinet stomatologic",
            "clinica dentara",
            "dentist",
            "implantologie dentara",
        ),
        coduri_caen=("8623",),
        nota="Valoare mare pe pacient, dar breaslă închisă și agenții specializate deja prezente.",
    ),
    Verticala(
        slug="constructii-amenajari",
        nume="Construcții / amenajări interioare",
        interogari=(
            "firma constructii",
            "amenajari interioare",
            "renovari apartamente",
            "constructii case la rosu",
        ),
        coduri_caen=("4120", "4332", "4333", "4339"),
        nota="Bon mediu mare, maturitate digitală mică, ciclu de vânzare lung.",
    ),
    Verticala(
        slug="instalatori-electricieni",
        nume="Instalatori / electricieni (urgențe)",
        interogari=(
            "instalator sanitar",
            "electrician",
            "instalator urgente",
            "desfundare canalizare",
            "reparatii centrale termice",
        ),
        coduri_caen=("4321", "4322"),
        nota="Nevoie urgentă — cea mai bună verticală pentru pay-per-lead.",
    ),
)


ORASE: tuple[Oras, ...] = (
    Oras("bucuresti", "București", 44.4268, 26.1025, 12000, 1716961),
    Oras("cluj", "Cluj-Napoca", 46.7712, 23.6236, 7000, 286598),
    Oras("timisoara", "Timișoara", 45.7489, 21.2087, 7000, 250849),
    Oras("iasi", "Iași", 47.1585, 27.6014, 7000, 271692),
    Oras("brasov", "Brașov", 45.6427, 25.5887, 6000, 237589),
    Oras("craiova", "Craiova", 44.3302, 23.7949, 6000, 234140),
    # Orașul mic e obligatoriu în eșantion: penetrarea site-urilor e alta acolo și
    # e foarte posibil să răstoarne clasamentul verticalelor.
    Oras("alba-iulia", "Alba Iulia", 46.0733, 23.5805, 4500, 63536, mic=True),
)


VERTICALE_DUPA_SLUG = {v.slug: v for v in VERTICALE}
ORASE_DUPA_SLUG = {o.slug: o for o in ORASE}
