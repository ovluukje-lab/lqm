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
    # Guest opinion
    click_to_add_to_cart: Optional[float] = None
    nr_reviews: Optional[int] = None
    nr_reviews_past6months: Optional[int] = None
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


# ---------- Category: Photos ----------
# Ideaal: meer dan 10 en minder dan 50 foto's. Onder 10 = malus, boven 50 = malus.
def score_photos(data: ExtractedData) -> list[LQMScoreItem]:
    items = []
    n = data.photo_count
    ctr = data.ctr

    # bonus_ctr
    if ctr is not None:
        items.append(LQMScoreItem(
            "bonus_ctr", "Photos",
            10 if ctr > 0.02 else 0, "bonus",
            f"CTR: {ctr:.4f} (bonus bij >0.02)."
        ))
    else:
        items.append(LQMScoreItem("bonus_ctr", "Photos", 0, "bonus", "CTR niet beschikbaar (tracking).", not_applicable=True))

    # bonus_photo_count_ideal: 11–49 foto's is ideale positie
    if n is not None:
        if 11 <= n <= 49:
            items.append(LQMScoreItem("bonus_photo_count_ideal", "Photos", 5, "bonus", f"Ideaal aantal foto's: {n} (11–49)."))
        else:
            items.append(LQMScoreItem("bonus_photo_count_ideal", "Photos", 0, "bonus", f"Aantal foto's: {n} (ideaal 11–49)."))
    else:
        items.append(LQMScoreItem("bonus_photo_count_ideal", "Photos", 0, "bonus", "Aantal foto's niet bepaald.", not_applicable=True))

    # malus_photo_count_low: onder 10 = aftrek
    if n is not None:
        if n == 0:
            items.append(LQMScoreItem("malus_photo_count_low", "Photos", -50, "malus", "Geen foto's."))
        elif n < 2:
            items.append(LQMScoreItem("malus_photo_count_low", "Photos", -20, "malus", "Minder dan 2 foto's."))
        elif n < 5:
            items.append(LQMScoreItem("malus_photo_count_low", "Photos", -10, "malus", "Minder dan 5 foto's."))
        elif n < 10:
            items.append(LQMScoreItem("malus_photo_count_low", "Photos", -5, "malus", "Minder dan 10 foto's."))
        else:
            items.append(LQMScoreItem("malus_photo_count_low", "Photos", 0, "malus", f"Foto's: {n}."))
    else:
        items.append(LQMScoreItem("malus_photo_count_low", "Photos", 0, "malus", "Aantal foto's niet bepaald.", not_applicable=True))

    # malus_photo_count_high: boven 50 = aftrek
    if n is not None:
        if n > 60:
            items.append(LQMScoreItem("malus_photo_count_high", "Photos", -5, "malus", "Meer dan 60 foto's."))
        elif n >= 50:
            items.append(LQMScoreItem("malus_photo_count_high", "Photos", -3, "malus", "50 of meer foto's (ideaal <50)."))
        else:
            items.append(LQMScoreItem("malus_photo_count_high", "Photos", 0, "malus", "Aantal OK."))
    else:
        items.append(LQMScoreItem("malus_photo_count_high", "Photos", 0, "malus", "Niet bepaald.", not_applicable=True))

    # Coverfoto: eerste foto moet huisje in de natuur zijn (uit alt-tekst)
    cov = data.cover_photo_suggests_nature
    if cov is True:
        items.append(LQMScoreItem("bonus_cover_photo_nature", "Photos", 5, "bonus", "Coverfoto suggereert huisje in de natuur (uit alt-tekst)."))
    elif cov is False:
        items.append(LQMScoreItem("malus_cover_photo_not_nature", "Photos", -3, "malus", "Coverfoto lijkt geen huisje in de natuur (uit alt-tekst)."))
    else:
        items.append(LQMScoreItem("bonus_cover_photo_nature", "Photos", 0, "bonus", "Coverfoto niet beoordeelbaar (geen/weinig alt-tekst).", not_applicable=True))

    # malus_ctr_poor
    if ctr is not None:
        items.append(LQMScoreItem(
            "malus_ctr_poor", "Photos",
            -5 if 0.0001 < ctr <= 0.003 else 0, "malus",
            f"CTR laag: {ctr:.4f}."
        ))
    else:
        items.append(LQMScoreItem("malus_ctr_poor", "Photos", 0, "malus", "Niet beschikbaar.", not_applicable=True))

    return items


# ---------- Category: Guest Opinion ----------
def score_guest_opinion(data: ExtractedData) -> list[LQMScoreItem]:
    items = []

    if data.click_to_add_to_cart is not None:
        items.append(LQMScoreItem(
            "bonus_click_to_cart_high", "Guest Opinion",
            5 if data.click_to_add_to_cart > 0.07 else 0, "bonus",
            f"Click-to-cart: {data.click_to_add_to_cart:.4f}."
        ))
    else:
        items.append(LQMScoreItem("bonus_click_to_cart_high", "Guest Opinion", 0, "bonus", "Niet beschikbaar (tracking).", not_applicable=True))

    if data.nr_reviews is not None:
        items.append(LQMScoreItem(
            "bonus_review_any", "Guest Opinion",
            3 if data.nr_reviews > 0 else 0, "bonus",
            f"Aantal reviews: {data.nr_reviews}."
        ))
    else:
        items.append(LQMScoreItem("bonus_review_any", "Guest Opinion", 0, "bonus", "Niet zichtbaar op pagina.", not_applicable=True))

    if data.nr_reviews_past6months is not None:
        items.append(LQMScoreItem(
            "bonus_review_6months_or_recent", "Guest Opinion",
            5 if data.nr_reviews_past6months > 0 else 0, "bonus",
            f"Reviews afgelopen 6 maanden: {data.nr_reviews_past6months}."
        ))
    else:
        items.append(LQMScoreItem("bonus_review_6months_or_recent", "Guest Opinion", 0, "bonus", "Niet zichtbaar.", not_applicable=True))

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
    """Totaal LQM-score; Description telt niet mee (advisory)."""
    return sum(i.score for i in items if i.category != "Description")


def summary_by_category(items: list[LQMScoreItem]) -> dict:
    by_cat = {}
    for i in items:
        by_cat.setdefault(i.category, {"bonus": 0, "malus": 0, "items": [], "advisory": False, "all_passed": None})
        by_cat[i.category]["items"].append(i)
        if i.category == "Description":
            by_cat[i.category]["advisory"] = True
        elif i.type_ == "bonus":
            by_cat[i.category]["bonus"] += i.score
        else:
            by_cat[i.category]["malus"] += i.score
    # Description: overall groene check als alle checks voldaan
    if "Description" in by_cat:
        desc_items = by_cat["Description"]["items"]
        applicable = [i for i in desc_items if not i.not_applicable and i.passed is not None]
        by_cat["Description"]["all_passed"] = all(i.passed for i in applicable) if applicable else None
    return by_cat
