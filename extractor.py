# Page extractor: haalt content van een advertentie-URL en vult ExtractedData

from __future__ import annotations
import json
import re
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup

from lqm_scorer import ExtractedData


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
TIMEOUT = 15


def fetch_page(url: str) -> tuple[str | None, str | None]:
    """Haalt HTML op van de URL. Retourneert (html, error_message)."""
    try:
        resp = requests.get(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=TIMEOUT,
            allow_redirects=True,
        )
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding or "utf-8"
        return resp.text, None
    except requests.RequestException as e:
        return None, str(e)


def _get_text(soup: BeautifulSoup, selectors: list[str], join: str = " ") -> str:
    """Zoekt eerste match voor een van de selectors en retourneert getrimde tekst."""
    for sel in selectors:
        el = soup.select_one(sel)
        if el:
            return " ".join(el.get_text(separator=" ", strip=True).split())
    return ""


def _get_all_text(soup: BeautifulSoup, selectors: list[str], join: str = " ") -> str:
    """Verzamelt tekst van alle elementen die matchen met een van de selectors."""
    parts = []
    for sel in selectors:
        for el in soup.select(sel):
            t = el.get_text(separator=" ", strip=True)
            if t:
                parts.append(" ".join(t.split()))
    return join.join(parts) if parts else ""


def _count_images(soup: BeautifulSoup, url: str) -> int:
    """Telt afbeeldingen die waarschijnlijk bij de listing horen (niet logo's/icons)."""
    imgs = soup.find_all("img", src=True)
    base_domain = urlparse(url).netloc
    count = 0
    skip = {"logo", "icon", "avatar", "sprite", "pixel", "tracking", "1x1", "placeholder"}
    for img in imgs:
        src = (img.get("src") or "").lower()
        alt = (img.get("alt") or "").lower()
        if any(s in src or s in alt for s in skip):
            continue
        if "data:image" in src:
            count += 1
            continue
        if src.startswith("http") or src.startswith("//"):
            count += 1
        elif src.startswith("/"):
            count += 1
    return count


def _find_json_ld(soup: BeautifulSoup) -> list[dict]:
    """Haalt JSON-LD scripts op (o.a. voor Accommodation)."""
    result = []
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "{}")
            if isinstance(data, list):
                result.extend(data)
            elif isinstance(data, dict):
                result.append(data)
        except Exception:
            pass
    return result


def _extract_from_json_ld(blocks: list[dict]) -> dict:
    """Haalt velden uit JSON-LD die relevant zijn voor LQM."""
    out = {}
    for b in blocks:
        if b.get("@type") in ("Accommodation", "LodgingBusiness", "Product"):
            # Adres
            addr = b.get("address") or {}
            if isinstance(addr, dict):
                out["addressRegion"] = addr.get("addressRegion")
                out["addressLocality"] = addr.get("addressLocality")
                out["postalCode"] = addr.get("postalCode")
            # Recensies
            agg = b.get("aggregateRating") or {}
            if isinstance(agg, dict):
                out["reviewCount"] = agg.get("reviewCount")
            # Foto's
            img = b.get("image") or []
            if isinstance(img, list):
                out["imageCount"] = len(img)
            elif isinstance(img, str):
                out["imageCount"] = 1
    return out


def extract_from_html(html: str, url: str) -> ExtractedData:
    """
    Parsed de HTML van een advertentiepagina en vult zoveel mogelijk
    velden van ExtractedData. Velden die niet op de pagina staan blijven None.
    """
    soup = BeautifulSoup(html, "lxml")
    data = ExtractedData()

    # --- Description: zoek naar hoofdtekst / beschrijvingen ---
    # Eerste grote tekstblokken als "general", evt. sectie met "natuur" als "nature"
    general_selectors = [
        "[data-testid='description']",
        ".description",
        ".listing-description",
        ".property-description",
        "[class*='description']",
        "article p",
        ".content p",
        "main p",
    ]
    data.general_description = _get_all_text(soup, general_selectors, "\n\n")
    if not data.general_description:
        data.general_description = _get_all_text(soup, ["p"], "\n\n")[:5000]

    # Aparte "natuur" beschrijving zoeken
    nature_selectors = [
        "[class*='nature']",
        "[id*='nature']",
        "[data-section='nature']",
        ".nature-description",
    ]
    data.nature_description = _get_all_text(soup, nature_selectors, "\n\n")
    if not data.nature_description and data.general_description:
        # Geen aparte natuur-sectie: gebruik tweede helft van algemene tekst als proxy
        parts = (data.general_description or "").split("\n\n")
        if len(parts) >= 2:
            data.nature_description = "\n\n".join(parts[1:])

    # Place / locatie uit tekst of meta
    place_selectors = [
        "[itemprop='addressLocality']",
        ".address-locality",
        "[class*='location']",
        "[class*='place']",
        "[data-testid='location']",
    ]
    data.place = _get_text(soup, place_selectors)
    if not data.place:
        meta_geo = soup.find("meta", attrs={"name": re.compile(r"geo|place|location", re.I)})
        if meta_geo and meta_geo.get("content"):
            data.place = meta_geo["content"].strip()

    # Postcode uit tekst of JSON-LD
    json_ld_blocks = _find_json_ld(soup)
    json_data = _extract_from_json_ld(json_ld_blocks)
    if json_data.get("postalCode"):
        data.postcode = str(json_data["postalCode"]).strip()
    if json_data.get("addressLocality") and not data.place:
        data.place = str(json_data["addressLocality"]).strip()

    # Place: malus voor ( ), * , 
    if data.place and ("(" in data.place or "*" in data.place or "," in data.place):
        pass  # Scorer handelt malus_place_chars

    # Foto's: tel img op de pagina
    data.photo_count = _count_images(soup, url)

    # Reviews uit JSON-LD of tekst
    if json_data.get("reviewCount") is not None:
        try:
            data.nr_reviews = int(json_data["reviewCount"])
        except (TypeError, ValueError):
            pass
    if data.nr_reviews is None:
        # Zoek naar "X reviews" of "X beoordelingen"
        text = soup.get_text()
        for pat in [r"(\d+)\s*(?:reviews?|beoordelingen?)", r"(?:reviews?|beoordelingen?)\s*[:\s]*(\d+)"]:
            m = re.search(pat, text, re.I)
            if m:
                try:
                    data.nr_reviews = int(m.group(1))
                    break
                except (IndexError, ValueError):
                    pass

    # Sustainability / leaves: zoek naar "blad" of "leaf" of "duurzaam"
    text_lower = (soup.get_text() or "").lower()
    if "duurzaam" in text_lower or "sustainability" in text_lower or "eco" in text_lower:
        # Heuristiek: als er iets over duurzaamheid staat, neem 1 leaf
        data.sustainability_impact_level_leaves = 1
    # Exact aantal leaves is zonder API meestal niet te bepalen

    # Overige velden (allow_instant_booking, channel_manager, iCals, etc.) zijn
    # typisch niet zichtbaar op de publieke pagina → blijven None; scorer geeft N/A.

    return data


def extract_from_url(url: str) -> tuple[ExtractedData | None, str | None]:
    """
    Haalt de pagina op en extraheert data. Retourneert (ExtractedData, None) bij succes,
    of (None, error_message) bij fout.
    """
    if not url or not url.strip():
        return None, "Geen URL opgegeven."
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    html, err = fetch_page(url)
    if err:
        return None, f"Pagina ophalen mislukt: {err}"

    data = extract_from_html(html, url)
    return data, None
