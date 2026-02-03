# LQM (Listing Quality Model) Scorer - 50 attributen, 8 categorieën
# Alle bonus/malus regels volgens specificatie

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
import re

try:
    from config import POSTCODE_PATTERNS, COVID_KEYWORDS, POSTCODE_MIN_LEN, POSTCODE_MAX_LEN
except ImportError:
    POSTCODE_PATTERNS = {}
    COVID_KEYWORDS = ["corona", "covid", "pandemie"]
    POSTCODE_MIN_LEN = 4
    POSTCODE_MAX_LEN = 10


@dataclass
class LQMScoreItem:
    """Eén score-attribuut met naam, punten en toelichting. Voor Description (advisory): passed + recommendation."""
    attribute: str
    category: str
    score: int
    type_: str  # "bonus" | "malus" | "advisory"
    reason: str
    not_applicable: bool = False  # True als niet beoordeelbaar vanaf URL
    passed: Optional[bool] = None  # Voor advisory: True = voldoet, False = aanbeveling geven
    recommendation: Optional[str] = None  # Aanbeveling wanneer passed=False


@dataclass
class ExtractedData:
    """Data geëxtraheerd van een advertentiepagina (of uit API). Ontbrekende velden = None."""
    # Description
    general_description: Optional[str] = None
    nature_description: Optional[str] = None
    days_since_last_update: Optional[int] = None  # dagen
    # Impact
    sustainability_impact_level_leaves: Optional[int] = None  # 0, 1, 2, 3, ...
    # Location
    postcode: Optional[str] = None
    place: Optional[str] = None
    country: Optional[str] = None  # NL, BE, DE, FR, ...
    # Availability
    allow_instant_booking: Optional[int] = None  # 0/1
    channel_manager_type: Optional[str] = None  # e.g. OPENGDS, Smoobu
    nr_icals_error: Optional[int] = None
    nr_icals_total: Optional[int] = None
    fully_blocked: Optional[int] = None
    fully_nonbookable: Optional[int] = None
    fully_available: Optional[int] = None
    only_weeks_possible: Optional[bool] = None
    only_other_stays_possible: Optional[bool] = None
    has_short_stay_types: Optional[bool] = None
    years_platform: Optional[float] = None
    months_updated_priceplan: Optional[int] = None
    months_last_update_blocks: Optional[int] = None
    months_updated: Optional[int] = None
    # Photos
    photo_count: Optional[int] = None
    ctr: Optional[float] = None
    cover_photo_suggests_nature: Optional[bool] = None  # True/False uit eerste foto alt-tekst
    first_photo_house_not_interior: Optional[bool] = None  # True=huisje/exterior, False=interieur, None=niet te bepalen
    first_photo_width: Optional[int] = None  # breedte eerste foto (uit HTML) voor resolutie-check
    first_photo_height: Optional[int] = None
    # AI-vision (OpenAI): alleen gezet als OPENAI_API_KEY is gezet en analyse lukt
    first_photo_ai_exterior: Optional[bool] = None  # True=exterior, False=interieur
    first_photo_ai_watermark: Optional[bool] = None  # True=watermerk/tekst zichtbaar
    first_photo_ai_collage: Optional[bool] = None   # True=collage
    # Guest opinion
    click_to_add_to_cart: Optional[float] = None
    nr_reviews: Optional[int] = None
    nr_reviews_past6months: Optional[int] = None
    average_rating: Optional[float] = None   # gemiddelde beoordeling (schaal 5 of 10)
    rating_scale_max: Optional[int] = None  # 5 of 10
    # Filters
    max_babies: Optional[int] = None
    baby_facilities_count: Optional[int] = None
    max_animals: Optional[int] = None
    has_pet_related_features: Optional[bool] = None
    total_house_attributes: Optional[int] = None
    accommodation_type_string: Optional[str] = None  # e.g. "villa, bungalow"
    allow_fireworks: Optional[bool] = None
    allow_groups: Optional[bool] = None
    allow_smoking: Optional[bool] = None
    allow_parties: Optional[bool] = None
    number_of_bedrooms: Optional[int] = None
    max_persons: Optional[int] = None
    nr_house_themes: Optional[int] = None
    province_or_region: Optional[str] = None
    theme_coastal: Optional[bool] = None
    region_inland: Optional[bool] = None
    # Time settings
    arrival_departure_times: Optional[list] = None  # e.g. ["14:00:00", "10:00:00"]
    silence_start: Optional[str] = None
    silence_end: Optional[str] = None


def _len(s: Optional[str]) -> int:
    return len(s.strip()) if s and s.strip() else 0


def _is_opengds(data: ExtractedData) -> bool:
    return (data.channel_manager_type or "").upper() == "OPENGDS"


def _is_smoobu(data: ExtractedData) -> bool:
    return (data.channel_manager_type or "").upper() == "SMOOBU"


def _not_opengds(data: ExtractedData) -> bool:
    return not _is_opengds(data)


# ---------- Category: Description (advisory: aanbeveling + groene check) ----------
# Geen punten; check of voldoet en geef aanbeveling om aan voorwaarden te voldoen.
MIN_GEN_LEN = 275   # algemene beschrijving minimaal lang genoeg
MIN_NAT_LEN = 200   # natuur beschrijving minimaal lang genoeg


def score_description(data: ExtractedData) -> list[LQMScoreItem]:
    """Description als aanbeveling: check lengte, verschillend, geen capslock. Groene check als alles voldoet."""
    items = []
    gen = data.general_description
    nat = data.nature_description
    len_gen = _len(gen)
    len_nat = _len(nat)
    combined = (gen or "") + " " + (nat or "")

    # 1. Algemene beschrijving lang genoeg (min 275, bij voorkeur 550+)
    if gen is None or not gen.strip():
        items.append(LQMScoreItem(
            "algemene_beschrijving", "Description", 0, "advisory",
            "Algemene beschrijving ontbreekt.",
            passed=False,
            recommendation="Voeg een algemene beschrijving toe van minimaal 275 tekens (bij voorkeur meer dan 550). Beschrijf het huisje, de omgeving en wat gasten kunnen verwachten."
        ))
    elif len_gen < MIN_GEN_LEN:
        items.append(LQMScoreItem(
            "algemene_beschrijving", "Description", 0, "advisory",
            f"Algemene beschrijving is {len_gen} tekens (minimaal {MIN_GEN_LEN}).",
            passed=False,
            recommendation=f"Maak de algemene beschrijving langer: minimaal {MIN_GEN_LEN} tekens (bij voorkeur meer dan 550). Nu: {len_gen} tekens."
        ))
    else:
        items.append(LQMScoreItem(
            "algemene_beschrijving", "Description", 0, "advisory",
            f"Algemene beschrijving is lang genoeg ({len_gen} tekens).",
            passed=True
        ))

    # 2. Natuur beschrijving lang genoeg (min 200, bij voorkeur 550+)
    if nat is None or not nat.strip():
        items.append(LQMScoreItem(
            "natuur_beschrijving", "Description", 0, "advisory",
            "Natuur beschrijving ontbreekt.",
            passed=False,
            recommendation="Voeg een aparte natuur beschrijving toe van minimaal 200 tekens (bij voorkeur meer dan 550). Beschrijf de natuur, het landschap en de omgeving rond het huisje."
        ))
    elif len_nat < MIN_NAT_LEN:
        items.append(LQMScoreItem(
            "natuur_beschrijving", "Description", 0, "advisory",
            f"Natuur beschrijving is {len_nat} tekens (minimaal {MIN_NAT_LEN}).",
            passed=False,
            recommendation=f"Maak de natuur beschrijving langer: minimaal {MIN_NAT_LEN} tekens (bij voorkeur meer dan 550). Nu: {len_nat} tekens."
        ))
    else:
        items.append(LQMScoreItem(
            "natuur_beschrijving", "Description", 0, "advisory",
            f"Natuur beschrijving is lang genoeg ({len_nat} tekens).",
            passed=True
        ))

    # 3. Algemene en natuur beschrijving verschillend van elkaar
    if gen is not None and nat is not None and len_gen > 75 and gen.strip() == nat.strip():
        items.append(LQMScoreItem(
            "beschrijvingen_verschillend", "Description", 0, "advisory",
            "Algemene en natuur beschrijving zijn identiek.",
            passed=False,
            recommendation="Schrijf een aparte tekst voor de natuur beschrijving in plaats van dezelfde tekst te kopiëren. De natuur beschrijving moet gaan over het landschap, de omgeving en de natuur; de algemene beschrijving over het huisje en de voorzieningen."
        ))
    else:
        items.append(LQMScoreItem(
            "beschrijvingen_verschillend", "Description", 0, "advisory",
            "Algemene en natuur beschrijving zijn verschillend.",
            passed=True
        ))

    # 4. Geen teksten in capslock (geen lange woorden in HOOFDLETTERS)
    if combined:
        words = re.findall(r"[A-Za-z]{8,}", combined)
        caps_count = sum(1 for w in words if w == w.upper() and len(w) >= 8)
        if caps_count >= 2:
            items.append(LQMScoreItem(
                "geen_capslock", "Description", 0, "advisory",
                f"Er staan {caps_count} lange woorden in HOOFDLETTERS.",
                passed=False,
                recommendation="Vermijd lange woorden in HOOFDLETTERS (capslock); dat oogt onrustig en onprofessioneel. Gebruik normale hoofdletters (alleen eerste letter van een zin of eigennaam)."
            ))
        else:
            items.append(LQMScoreItem(
                "geen_capslock", "Description", 0, "advisory",
                "Geen overmatig gebruik van hoofdletters.",
                passed=True
            ))
    else:
        items.append(LQMScoreItem(
            "geen_capslock", "Description", 0, "advisory",
            "Geen tekst om te controleren.",
            not_applicable=True
        ))

    return items


# ---------- Category: Impact ----------
def score_impact(data: ExtractedData) -> list[LQMScoreItem]:
    items = []
    leaves = data.sustainability_impact_level_leaves

    # bonus_impact_score_leaves 0–3 (0 leaves=1, else 3; NULL=0)
    if leaves is not None:
        items.append(LQMScoreItem(
            "bonus_impact_score_leaves", "Impact",
            1 if leaves == 0 else 3, "bonus",
            f"Sustainability leaves: {leaves} (bonus 1 bij 0, 3 bij ≥1)."
        ))
    else:
        items.append(LQMScoreItem("bonus_impact_score_leaves", "Impact", 0, "bonus", "Impact score niet beschikbaar.", not_applicable=True))

    # malus_impact_score_leaves -5 bij NULL
    items.append(LQMScoreItem(
        "malus_impact_score_leaves", "Impact",
        -5 if leaves is None else 0, "malus",
        "Impact/duurzaamheidsscore ontbreekt." if leaves is None else "Impact score aanwezig."
    ))
    return items


# ---------- Category: Location ----------
def _validate_postcode(postcode: Optional[str], country: Optional[str]) -> bool:
    if not postcode or not postcode.strip():
        return False
    pc = postcode.strip().replace(" ", "")
    country = (country or "").upper()[:2]
    if country in POSTCODE_PATTERNS:
        return bool(POSTCODE_PATTERNS[country].match(pc))
    return POSTCODE_MIN_LEN <= len(pc) <= POSTCODE_MAX_LEN


def score_location(data: ExtractedData) -> list[LQMScoreItem]:
    items = []
    pc = data.postcode
    place = data.place or ""
    country = data.country

    # malus_not_a_valid_postcode
    if pc is not None or (data.place and any(c.isdigit() for c in (data.place or ""))):
        # Als we alleen place hebben, kunnen we geen postcode valideren
        valid = _validate_postcode(pc, country) if pc else False
        items.append(LQMScoreItem(
            "malus_not_a_valid_postcode", "Location",
            -2 if not valid and pc else 0, "malus",
            "Ongeldige of ontbrekende postcode." if (pc and not valid) else "Postcode OK of niet gecontroleerd."
        ))
    else:
        items.append(LQMScoreItem("malus_not_a_valid_postcode", "Location", 0, "malus", "Postcode niet beschikbaar vanaf URL.", not_applicable=True))

    # malus_place_chars ( ), * , in place
    has_bad = "(" in place or "*" in place or "," in place
    items.append(LQMScoreItem(
        "malus_place_chars", "Location",
        -2 if has_bad else 0, "malus",
        "Plaatsnaam bevat marketing/onduidelijke tekens." if has_bad else "Plaatsnaam OK."
    ))
    return items


# ---------- Category: Availability ----------
def score_availability(data: ExtractedData) -> list[LQMScoreItem]:
    items = []
    opengds = _is_opengds(data)
    smoobu = _is_smoobu(data)
    not_og = _not_opengds(data)

    # bonus_allow_instant_booking 15
    if data.allow_instant_booking is not None:
        items.append(LQMScoreItem(
            "bonus_allow_instant_booking", "Availability",
            15 if data.allow_instant_booking == 1 else 0, "bonus",
            "Direct boeken mogelijk." if data.allow_instant_booking == 1 else "Geen direct boeken."
        ))
    else:
        items.append(LQMScoreItem("bonus_allow_instant_booking", "Availability", 0, "bonus", "Niet zichtbaar op pagina.", not_applicable=True))

    # bonus_has_channel_manager 10
    items.append(LQMScoreItem(
        "bonus_has_channel_manager", "Availability",
        10 if data.channel_manager_type else 0, "bonus",
        "Channel manager aanwezig." if data.channel_manager_type else "Geen channel manager."
    ))

    # bonus_has_opengds 10
    items.append(LQMScoreItem(
        "bonus_has_opengds", "Availability",
        10 if opengds else 0, "bonus",
        "OpenGDS integratie." if opengds else "Geen OpenGDS."
    ))

    # bonus_icals_working (vereenvoudigd: geen errors = bonus)
    if data.nr_icals_error is not None and data.nr_icals_total is not None:
        if data.nr_icals_error == 0 and data.nr_icals_total > 0:
            weight = {1: 4, 2: 3}.get(data.nr_icals_total, 2)
            bonus = min(8, data.nr_icals_total * weight)
            items.append(LQMScoreItem("bonus_icals_working", "Availability", bonus, "bonus", f"iCals werken ({data.nr_icals_total} feeds)."))
        else:
            items.append(LQMScoreItem("bonus_icals_working", "Availability", 0, "bonus", "Geen werkende iCals of errors."))
    else:
        items.append(LQMScoreItem("bonus_icals_working", "Availability", 0, "bonus", "Niet zichtbaar op pagina.", not_applicable=True))

    # bonus_short_stay (niet OPENGDS: weekend/midweek/long weekend * 4, max 12)
    if data.has_short_stay_types is not None and not_og:
        items.append(LQMScoreItem(
            "bonus_short_stay", "Availability",
            12 if data.has_short_stay_types else 0, "bonus",
            "Korte verblijven mogelijk." if data.has_short_stay_types else "Geen korte verblijven."
        ))
    else:
        items.append(LQMScoreItem("bonus_short_stay", "Availability", 0, "bonus", "Niet zichtbaar op pagina.", not_applicable=True))

    # bonus_priceplan_updated6months_or_recent
    if data.years_platform is not None and data.months_updated_priceplan is not None:
        items.append(LQMScoreItem(
            "bonus_priceplan_updated6months_or_recent", "Availability",
            3 if data.years_platform > 0 and data.months_updated_priceplan <= 6 else 0, "bonus",
            "Prijsplan recent bijgewerkt." if (data.years_platform and data.months_updated_priceplan is not None and data.months_updated_priceplan <= 6) else "Niet recent."
        ))
    else:
        items.append(LQMScoreItem("bonus_priceplan_updated6months_or_recent", "Availability", 0, "bonus", "Niet zichtbaar.", not_applicable=True))

    # bonus_recent_agenda_block_updated
    if data.months_last_update_blocks is not None:
        items.append(LQMScoreItem(
            "bonus_recent_agenda_block_updated", "Availability",
            3 if data.months_last_update_blocks <= 6 else 0, "bonus",
            "Agenda recent bijgewerkt." if data.months_last_update_blocks <= 6 else "Niet recent."
        ))
    else:
        items.append(LQMScoreItem("bonus_recent_agenda_block_updated", "Availability", 0, "bonus", "Niet zichtbaar.", not_applicable=True))

    # malus_available_only_weeks
    if data.only_weeks_possible is not None and not_og:
        items.append(LQMScoreItem(
            "malus_available_only_weeks", "Availability",
            -5 if data.only_weeks_possible else 0, "malus",
            "Alleen weken boekbaar." if data.only_weeks_possible else "Meerdere verblijftypes."
        ))
    else:
        items.append(LQMScoreItem("malus_available_only_weeks", "Availability", 0, "malus", "Niet van toepassing.", not_applicable=True))

    # malus_available_only_otherstays
    if data.only_other_stays_possible is not None and not_og:
        items.append(LQMScoreItem(
            "malus_available_only_otherstays", "Availability",
            -10 if data.only_other_stays_possible else 0, "malus",
            "Alleen 'overige' verblijven." if data.only_other_stays_possible else "Standaard verblijven mogelijk."
        ))
    else:
        items.append(LQMScoreItem("malus_available_only_otherstays", "Availability", 0, "malus", "Niet van toepassing.", not_applicable=True))

    # malus_icals_not_working (nr_icals_error * -10, tenzij OPENGDS/Smoobu)
    if data.nr_icals_error is not None and not opengds and not smoobu:
        malus = min(0, data.nr_icals_error * -10)
        items.append(LQMScoreItem(
            "malus_icals_not_working", "Availability",
            malus, "malus",
            f"Aantal iCal-fouten: {data.nr_icals_error}."
        ))
    else:
        items.append(LQMScoreItem("malus_icals_not_working", "Availability", 0, "malus", "Niet van toepassing of OpenGDS/Smoobu.", not_applicable=True))

    # malus_fully_blocked
    if data.fully_blocked is not None and not_og:
        items.append(LQMScoreItem(
            "malus_fully_blocked", "Availability",
            -30 if data.fully_blocked == 1 else 0, "malus",
            "Volledig geblokkeerd." if data.fully_blocked == 1 else "Niet volledig geblokkeerd."
        ))
    else:
        items.append(LQMScoreItem("malus_fully_blocked", "Availability", 0, "malus", "Niet zichtbaar.", not_applicable=True))

    # malus_fully_nonbookable
    if data.fully_nonbookable is not None and not_og:
        items.append(LQMScoreItem(
            "malus_fully_nonbookable", "Availability",
            -30 if data.fully_nonbookable == 1 else 0, "malus",
            "Volledig niet boekbaar." if data.fully_nonbookable == 1 else "Boekbaar."
        ))
    else:
        items.append(LQMScoreItem("malus_fully_nonbookable", "Availability", 0, "malus", "Niet zichtbaar.", not_applicable=True))

    # malus_fully_available
    if data.fully_available is not None and not_og:
        items.append(LQMScoreItem(
            "malus_fully_available", "Availability",
            -5 if data.fully_available == 1 else 0, "malus",
            "Volledig beschikbaar (geen agenda?)." if data.fully_available == 1 else "Agenda geconfigureerd."
        ))
    else:
        items.append(LQMScoreItem("malus_fully_available", "Availability", 0, "malus", "Niet zichtbaar.", not_applicable=True))

    # malus_months_updated (>12)
    if data.months_updated is not None:
        items.append(LQMScoreItem(
            "malus_months_updated", "Availability",
            -3 if data.months_updated > 12 else 0, "malus",
            f"Laatste update {data.months_updated} maanden geleden."
        ))
    else:
        items.append(LQMScoreItem("malus_months_updated", "Availability", 0, "malus", "Niet zichtbaar.", not_applicable=True))

    return items


# ---------- Category: Photos (advisory: aanbeveling + groene check) ----------
# Geen punten; check aantal (11–50), eerste foto huisje/geen interieur, geen namen/collage, resolutie.
MIN_PHOTOS = 11
MAX_PHOTOS = 50
MIN_PHOTO_WIDTH = 600
MIN_PHOTO_HEIGHT = 400


def score_photos(data: ExtractedData) -> list[LQMScoreItem]:
    """Photos als aanbeveling: aantal 11–50, eerste foto huisje (geen interieur), geen namen/collage, resolutie. Groene check als alles voldoet."""
    items = []
    n = data.photo_count

    # 1. Aantal foto's: minimaal 11, maximaal 50
    if n is None:
        items.append(LQMScoreItem(
            "aantal_fotos", "Photos", 0, "advisory",
            "Aantal foto's niet bepaald.",
            not_applicable=True,
            recommendation="Zorg voor minimaal 11 en maximaal 50 foto's van de accommodatie."
        ))
    elif MIN_PHOTOS <= n <= MAX_PHOTOS:
        items.append(LQMScoreItem(
            "aantal_fotos", "Photos", 0, "advisory",
            f"Aantal foto's is goed: {n} (tussen {MIN_PHOTOS} en {MAX_PHOTOS}).",
            passed=True
        ))
    elif n < MIN_PHOTOS:
        items.append(LQMScoreItem(
            "aantal_fotos", "Photos", 0, "advisory",
            f"Te weinig foto's: {n} (minimaal {MIN_PHOTOS}).",
            passed=False,
            recommendation=f"Voeg meer foto's toe. Een goede advertentie heeft minimaal {MIN_PHOTOS} en maximaal {MAX_PHOTOS} foto's. Nu: {n}."
        ))
    else:
        items.append(LQMScoreItem(
            "aantal_fotos", "Photos", 0, "advisory",
            f"Te veel foto's: {n} (maximaal {MAX_PHOTOS}).",
            passed=False,
            recommendation=f"Gebruik maximaal {MAX_PHOTOS} foto's. Te veel foto's kan overweldigend zijn. Nu: {n}. Kies de beste en meest representatieve foto's."
        ))

    # 2. Eerste foto: huisje (exterior), geen interieur — AI of alt-tekst
    first_house = data.first_photo_ai_exterior if data.first_photo_ai_exterior is not None else data.first_photo_house_not_interior
    ai_source = data.first_photo_ai_exterior is not None
    if first_house is True:
        items.append(LQMScoreItem(
            "eerste_foto_huisje", "Photos", 0, "advisory",
            "De eerste (cover)foto toont een huisje/exterior, geen interieur." + (" (AI-analyse)" if ai_source else ""),
            passed=True
        ))
    elif first_house is False:
        items.append(LQMScoreItem(
            "eerste_foto_huisje", "Photos", 0, "advisory",
            "De eerste foto toont een interieur, geen huisje van buiten." + (" (AI-analyse)" if ai_source else " (uit alt-tekst/bestandsnaam)."),
            passed=False,
            recommendation="Zet een foto van het huisje zelf (exterior, bijvoorbeeld de voorgevel of het huisje in de omgeving) als eerste/coverfoto. Geen interieur (woonkamer, keuken, slaapkamer) als eerste foto; dat kan later in de galerij."
        ))
    else:
        items.append(LQMScoreItem(
            "eerste_foto_huisje", "Photos", 0, "advisory",
            "Niet te bepalen of de eerste foto een huisje of interieur is (geen/weinig alt-tekst). Stel OPENAI_API_KEY in voor AI-analyse.",
            not_applicable=True,
            recommendation="Zorg dat de eerste foto het huisje van buiten toont (geen interieur als coverfoto). Voeg bij voorkeur een duidelijke alt-tekst toe aan de foto's."
        ))

    # 3. Geen namen op foto's — AI of handmatige aanbeveling
    wm = data.first_photo_ai_watermark
    if wm is not None:
        if wm:
            items.append(LQMScoreItem(
                "geen_namen_op_fotos", "Photos", 0, "advisory",
                "Op de eerste foto is tekst, een watermerk of logo zichtbaar (AI-analyse).",
                passed=False,
                recommendation="Verwijder watermerken, namen of logo's van de foto's. Foto's moeten professioneel en neutraal ogen."
            ))
        else:
            items.append(LQMScoreItem(
                "geen_namen_op_fotos", "Photos", 0, "advisory",
                "Geen watermerk of tekst zichtbaar op de eerste foto (AI-analyse).",
                passed=True
            ))
    else:
        items.append(LQMScoreItem(
            "geen_namen_op_fotos", "Photos", 0, "advisory",
            "Niet automatisch te controleren. Stel OPENAI_API_KEY in voor AI-analyse van de foto.",
            not_applicable=True,
            recommendation="Controleer handmatig dat er geen namen, watermerken of logo's op de foto's staan. Foto's moeten professioneel en neutraal ogen."
        ))

    # 4. Geen collage — AI of handmatige aanbeveling
    coll = data.first_photo_ai_collage
    if coll is not None:
        if coll:
            items.append(LQMScoreItem(
                "geen_collage", "Photos", 0, "advisory",
                "De eerste foto is een collage van meerdere afbeeldingen (AI-analyse).",
                passed=False,
                recommendation="Gebruik losse foto's, geen collages. Elke foto moet één duidelijke afbeelding tonen."
            ))
        else:
            items.append(LQMScoreItem(
                "geen_collage", "Photos", 0, "advisory",
                "De eerste foto is geen collage (AI-analyse).",
                passed=True
            ))
    else:
        items.append(LQMScoreItem(
            "geen_collage", "Photos", 0, "advisory",
            "Niet automatisch te controleren. Stel OPENAI_API_KEY in voor AI-analyse van de foto.",
            not_applicable=True,
            recommendation="Gebruik losse foto's, geen collages. Elke foto moet één duidelijke afbeelding tonen."
        ))

    # 5. Voldoende resolutie
    w, h = data.first_photo_width, data.first_photo_height
    if w is not None and h is not None:
        if w >= MIN_PHOTO_WIDTH and h >= MIN_PHOTO_HEIGHT:
            items.append(LQMScoreItem(
                "voldoende_resolutie", "Photos", 0, "advisory",
                f"Resolutie eerste foto is voldoende ({w}×{h} px).",
                passed=True
            ))
        else:
            items.append(LQMScoreItem(
                "voldoende_resolutie", "Photos", 0, "advisory",
                f"Resolutie eerste foto is laag: {w}×{h} px (aanbevolen min. {MIN_PHOTO_WIDTH}×{MIN_PHOTO_HEIGHT}).",
                passed=False,
                recommendation=f"Upload foto's met voldoende resolutie (minimaal {MIN_PHOTO_WIDTH}×{MIN_PHOTO_HEIGHT} pixels aanbevolen). Kleine of wazige foto's ogen onprofessioneel."
            ))
    else:
        items.append(LQMScoreItem(
            "voldoende_resolutie", "Photos", 0, "advisory",
            "Resolutie niet uit HTML te bepalen.",
            not_applicable=True,
            recommendation=f"Zorg dat alle foto's voldoende resolutie hebben (minimaal {MIN_PHOTO_WIDTH}×{MIN_PHOTO_HEIGHT} pixels aanbevolen). Geen kleine of wazige afbeeldingen."
        ))

    return items


# ---------- Category: Gastenbeoordelingen (advisory) ----------
def score_guest_opinion(data: ExtractedData) -> list[LQMScoreItem]:
    """Gastenbeoordelingen: altijd advies om beoordelingen te laten schrijven; compliment bij >3 beoordelingen met score >8."""
    items = []
    n = data.nr_reviews
    avg = data.average_rating
    scale = data.rating_scale_max or 10
    # Score "boven de 8": op schaal 10 is dat >= 8; op schaal 5 is dat >= 4
    above_8 = (avg is not None and scale == 10 and avg >= 8) or (avg is not None and scale == 5 and avg >= 4)

    # 1. Altijd advies: laat gasten beoordelingen schrijven, recente beoordelingen zijn cruciaal
    items.append(LQMScoreItem(
        "advies_gastenbeoordelingen", "Gastenbeoordelingen", 0, "advisory",
        "Gastenbeoordelingen helpen nieuwe gasten bij hun keuze. Recente beoordelingen zijn cruciaal.",
        not_applicable=True,
        recommendation=(
            "Vraag gasten na hun verblijf om een beoordeling te schrijven. "
            "Benadruk dat recente beoordelingen cruciaal zijn: ze laten zien dat je accommodatie actief en betrouwbaar is. "
            "Nieuwere beoordelingen wegen zwaarder voor potentiële gasten dan oude."
        )
    ))

    # 2. Compliment bij meer dan 3 beoordelingen met score boven de 8
    if n is not None and n > 3 and above_8:
        items.append(LQMScoreItem(
            "compliment_beoordelingen", "Gastenbeoordelingen", 0, "advisory",
            f"Compliment: je hebt {n} beoordelingen met een gemiddelde score van {avg:.1f} (boven de 8). Dat versterkt het vertrouwen van nieuwe gasten.",
            passed=True
        ))
    elif n is not None and n > 3 and avg is not None and not above_8:
        items.append(LQMScoreItem(
            "compliment_beoordelingen", "Gastenbeoordelingen", 0, "advisory",
            f"Je hebt {n} beoordelingen (gemiddeld {avg:.1f}). Nog geen score boven de 8.",
            passed=False,
            recommendation="Blijf gasten vragen om een beoordeling. Een gemiddelde score boven de 8 (op 10) geeft potentiële gasten extra vertrouwen."
        ))
    elif n is not None and n <= 3:
        items.append(LQMScoreItem(
            "compliment_beoordelingen", "Gastenbeoordelingen", 0, "advisory",
            f"Je hebt {n} beoordeling(en). Meer recente beoordelingen helpen nieuwe gasten.",
            passed=False,
            recommendation="Vraag gasten actief om een beoordeling na hun verblijf. Meer dan 3 beoordelingen met een score boven de 8 versterken je advertentie."
        ))
    else:
        items.append(LQMScoreItem(
            "compliment_beoordelingen", "Gastenbeoordelingen", 0, "advisory",
            "Aantal of gemiddelde beoordeling niet zichtbaar op de pagina.",
            not_applicable=True,
            recommendation="Laat gasten beoordelingen schrijven. Meer dan 3 beoordelingen met een score boven de 8 zijn een sterk visitekaartje."
        ))

    return items


# ---------- Category: Filters ----------
def score_filters(data: ExtractedData) -> list[LQMScoreItem]:
    items = []

    # malus_dont_allow_babies_but_many_attributes
    if data.max_babies is not None and data.baby_facilities_count is not None:
        items.append(LQMScoreItem(
            "malus_dont_allow_babies_but_many_attributes", "Filters",
            -3 if data.max_babies == 0 and data.baby_facilities_count >= 2 else 0, "malus",
            "Geen baby's toegestaan maar wel babyvoorzieningen."
        ))
    else:
        items.append(LQMScoreItem("malus_dont_allow_babies_but_many_attributes", "Filters", 0, "malus", "Niet zichtbaar.", not_applicable=True))

    # malus_mismatch_allow_pets_and_pets_attributes
    if data.max_animals is not None and data.has_pet_related_features is not None:
        items.append(LQMScoreItem(
            "malus_mismatch_allow_pets_and_pets_attributes", "Filters",
            -5 if data.max_animals == 0 and data.has_pet_related_features else 0, "malus",
            "Geen huisdieren maar wel huisdier-voorzieningen."
        ))
    else:
        items.append(LQMScoreItem("malus_mismatch_allow_pets_and_pets_attributes", "Filters", 0, "malus", "Niet zichtbaar.", not_applicable=True))

    # malus_zero_houseattributes
    if data.total_house_attributes is not None:
        items.append(LQMScoreItem(
            "malus_zero_houseattributes", "Filters",
            -5 if data.total_house_attributes == 0 else 0, "malus",
            "Geen huisattributen ingevuld." if data.total_house_attributes == 0 else "Attributen aanwezig."
        ))
    else:
        items.append(LQMScoreItem("malus_zero_houseattributes", "Filters", 0, "malus", "Niet zichtbaar.", not_applicable=True))

    # malus_accomodation_type_count (>2 types)
    if data.accommodation_type_string:
        count = len([x.strip() for x in data.accommodation_type_string.split(",") if x.strip()])
        items.append(LQMScoreItem(
            "malus_accomodation_type_count", "Filters",
            -3 if count > 2 else 0, "malus",
            f"Meerdere accommodatietypes: {count}."
        ))
    else:
        items.append(LQMScoreItem("malus_accomodation_type_count", "Filters", 0, "malus", "Niet zichtbaar.", not_applicable=True))

    # malus_allow_fireworks_missing
    items.append(LQMScoreItem(
        "malus_allow_fireworks_missing", "Filters",
        -3 if data.allow_fireworks is None else 0, "malus",
        "Vuurwerk-beleid ontbreekt." if data.allow_fireworks is None else "Ingevuld."
    ))

    # malus_allow_groups_missing
    items.append(LQMScoreItem(
        "malus_allow_groups_missing", "Filters",
        -3 if data.allow_groups is None else 0, "malus",
        "Groepen-beleid ontbreekt." if data.allow_groups is None else "Ingevuld."
    ))

    # malus_allow_smoking_parties_missing
    items.append(LQMScoreItem(
        "malus_allow_smoking_parties_missing", "Filters",
        -3 if (data.allow_smoking is None or data.allow_parties is None) else 0, "malus",
        "Roken/feesten filter ontbreekt." if (data.allow_smoking is None or data.allow_parties is None) else "Ingevuld."
    ))

    # malus_more_rooms_than_persons
    if data.number_of_bedrooms is not None and data.max_persons is not None and data.max_babies is not None:
        total = (data.max_persons or 0) + (data.max_babies or 0)
        items.append(LQMScoreItem(
            "malus_more_rooms_than_persons", "Filters",
            -7 if data.number_of_bedrooms > total else 0, "malus",
            "Meer slaapkamers dan personen+baby's."
        ))
    else:
        items.append(LQMScoreItem("malus_more_rooms_than_persons", "Filters", 0, "malus", "Niet zichtbaar.", not_applicable=True))

    # malus_nr_house_themes_overwhelming
    if data.nr_house_themes is not None:
        items.append(LQMScoreItem(
            "malus_nr_house_themes_overwhelming", "Filters",
            -5 if data.nr_house_themes >= 6 else 0, "malus",
            f"Aantal thema's: {data.nr_house_themes}."
        ))
    else:
        items.append(LQMScoreItem("malus_nr_house_themes_overwhelming", "Filters", 0, "malus", "Niet zichtbaar.", not_applicable=True))

    # malus_province_not_at_sea_coast
    if data.theme_coastal is not None and data.region_inland is not None:
        items.append(LQMScoreItem(
            "malus_province_not_at_sea_coast", "Filters",
            -7 if data.theme_coastal and data.region_inland else 0, "malus",
            "Kust-thema maar regio inland."
        ))
    else:
        items.append(LQMScoreItem("malus_province_not_at_sea_coast", "Filters", 0, "malus", "Niet zichtbaar.", not_applicable=True))

    return items


# ---------- Category: Time Settings ----------
def score_time_settings(data: ExtractedData) -> list[LQMScoreItem]:
    items = []

    # malus_arrival_departure_00h00
    times = data.arrival_departure_times or []
    has_midnight = any(t == "00:00:00" or t == "00:00" for t in times)
    items.append(LQMScoreItem(
        "malus_arrival_departure_00h00", "Time Settings",
        -2 if has_midnight else 0, "malus",
        "Aankomst/vertrek om 00:00 (placeholder?)." if has_midnight else "Geen 00:00."
    ))

    # malus_arrival_departure_moment_no_full_15mins (vereenvoudigd: niet geïmplementeerd zonder exacte tijden)
    items.append(LQMScoreItem("malus_arrival_departure_moment_no_full_15mins", "Time Settings", 0, "malus", "Alleen te beoordelen met exacte tijden.", not_applicable=True))

    # malus_short_arrival_departure_gap_minutes (vereenvoudigd)
    items.append(LQMScoreItem("malus_short_arrival_departure_gap_minutes", "Time Settings", 0, "malus", "Niet zichtbaar op pagina.", not_applicable=True))

    # malus_silence_start_end_time_missing
    items.append(LQMScoreItem(
        "malus_silence_start_end_time_missing", "Time Settings",
        -3 if (data.silence_start is None or data.silence_end is None) else 0, "malus",
        "Stilte-uren ontbreken." if (data.silence_start is None or data.silence_end is None) else "Stilte-uren ingevuld."
    ))

    # malus_silence_start_stop_swapped (silence_end in afternoon 12:00–22:00)
    if data.silence_end:
        try:
            # verwacht formaat "HH:MM" of "HH:MM:SS"
            part = data.silence_end.split(":")[0]
            h = int(part)
            if 12 <= h <= 22:
                items.append(LQMScoreItem("malus_silence_start_stop_swapped", "Time Settings", -5, "malus", "Stilte-einde in middag/avond (logica-fout)."))
            else:
                items.append(LQMScoreItem("malus_silence_start_stop_swapped", "Time Settings", 0, "malus", "Stilte-einde OK."))
        except (ValueError, IndexError):
            items.append(LQMScoreItem("malus_silence_start_stop_swapped", "Time Settings", 0, "malus", "Tijd niet parsebaar.", not_applicable=True))
    else:
        items.append(LQMScoreItem("malus_silence_start_stop_swapped", "Time Settings", 0, "malus", "Geen stilte-einde.", not_applicable=True))

    # malus_months_updated wordt alleen in Availability meegenomen (zelfde regel, geen dubbeltelling)

    return items


def score_all(data: ExtractedData) -> list[LQMScoreItem]:
    """Berekent alle LQM-scores voor de gegeven geëxtraheerde data."""
    all_items = []
    all_items += score_description(data)
    all_items += score_impact(data)
    all_items += score_location(data)
    all_items += score_availability(data)
    all_items += score_photos(data)
    all_items += score_guest_opinion(data)
    all_items += score_filters(data)
    all_items += score_time_settings(data)
    return all_items


def total_lqm_score(items: list[LQMScoreItem]) -> int:
    """Totaal LQM-score; Description, Photos en Gastenbeoordelingen (advisory) tellen niet mee."""
    return sum(i.score for i in items if i.category not in ("Description", "Photos", "Gastenbeoordelingen"))


def _advisory_all_passed(items: list[LQMScoreItem]) -> bool | None:
    """True als alle advisory-checks voldaan, False als minstens één niet voldoet, None als alleen n.v.t."""
    applicable = [i for i in items if not i.not_applicable and i.passed is not None]
    if not applicable:
        return None
    return all(i.passed for i in applicable)


def summary_by_category(items: list[LQMScoreItem]) -> dict:
    by_cat = {}
    for i in items:
        by_cat.setdefault(i.category, {"bonus": 0, "malus": 0, "items": [], "advisory": False, "all_passed": None})
        by_cat[i.category]["items"].append(i)
        if i.category in ("Description", "Photos", "Gastenbeoordelingen"):
            by_cat[i.category]["advisory"] = True
        elif i.type_ == "bonus":
            by_cat[i.category]["bonus"] += i.score
        else:
            by_cat[i.category]["malus"] += i.score
    for cat in ("Description", "Photos", "Gastenbeoordelingen"):
        if cat in by_cat:
            by_cat[cat]["all_passed"] = _advisory_all_passed(by_cat[cat]["items"])
    return by_cat
