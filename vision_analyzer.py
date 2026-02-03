# AI-analyse van de eerste foto (OpenAI Vision) voor LQM Photos-advisory
# Optioneel: alleen actief als OPENAI_API_KEY is gezet

from __future__ import annotations
import base64
import json
import os
import re
from typing import Optional
import requests

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
IMAGE_TIMEOUT = 15
IMAGE_MAX_BYTES = 4 * 1024 * 1024  # 4 MB
OPENAI_TIMEOUT = 30


def _resolve_image_url(src: str, page_url: str) -> str:
    """Maak van een relatief of protocol-relatief img src een absolute URL."""
    src = (src or "").strip()
    if not src:
        return ""
    if src.startswith("//"):
        return "https:" + src
    if src.startswith("http://") or src.startswith("https://"):
        return src
    if src.startswith("/"):
        from urllib.parse import urlparse
        parsed = urlparse(page_url)
        return f"{parsed.scheme or 'https'}://{parsed.netloc}{src}"
    # relatief t.o.v. pagina
    from urllib.parse import urljoin
    return urljoin(page_url, src)


def _fetch_image_as_base64(url: str) -> Optional[str]:
    """Haal afbeelding op en retourneer als base64-string, of None bij fout."""
    try:
        resp = requests.get(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=IMAGE_TIMEOUT,
            stream=True,
        )
        resp.raise_for_status()
        content_type = (resp.headers.get("content-type") or "").lower()
        if "image/" not in content_type and not content_type.startswith("image"):
            return None
        data = b""
        for chunk in resp.iter_content(chunk_size=8192):
            data += chunk
            if len(data) > IMAGE_MAX_BYTES:
                break
        if not data:
            return None
        return base64.standard_b64encode(data).decode("ascii")
    except Exception:
        return None


def analyze_first_photo(image_url: str, page_url: str) -> dict[str, Optional[bool]]:
    """
    Analyseer de eerste/coverfoto met OpenAI Vision.
    Retourneert dict met:
      - is_exterior: True = huis/exterior, False = interieur, None = onbekend/fout
      - has_watermark: True = tekst/watermerk zichtbaar, False = geen, None = onbekend
      - is_collage: True = collage van meerdere foto's, False = enkele foto, None = onbekend
    Zonder OPENAI_API_KEY of bij fout: lege dict of partial.
    """
    out: dict[str, Optional[bool]] = {}
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        return out

    if not image_url or not page_url:
        return out

    resolved = _resolve_image_url(image_url, page_url)
    if not resolved:
        return out

    b64 = _fetch_image_as_base64(resolved)
    if not b64:
        return out

    try:
        try:
            from openai import OpenAI
        except ImportError:
            return out
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=300,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Je analyseert één foto van een vakantie-accommodatie voor een kwaliteitscheck. "
                        "Antwoord uitsluitend met een JSON-object, geen andere tekst. Gebruik alleen de keys: is_exterior, has_watermark, is_collage. "
                        "Waarden: true of false."
                    ),
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
                        },
                        {
                            "type": "text",
                            "text": (
                                "Beantwoord voor deze foto:\n"
                                "1. is_exterior: Toont de foto de buitenkant van een huis/gebouw (exterior, voorgevel, huisje in omgeving)? "
                                "Antwoord false als het een interieur is (woonkamer, keuken, slaapkamer, badkamer).\n"
                                "2. has_watermark: Is er zichtbare tekst, een watermerk, logo of naam op de foto?\n"
                                "3. is_collage: Is dit een collage (meerdere kleine foto's in één afbeelding geplakt)?\n"
                                "Geef alleen een JSON-object, bijvoorbeeld: {\"is_exterior\": true, \"has_watermark\": false, \"is_collage\": false}"
                            ),
                        },
                    ],
                },
            ],
        )
        choice = response.choices[0] if response.choices else None
        if not choice or not choice.message or not choice.message.content:
            return out
        text = choice.message.content.strip()
        # Haal JSON uit eventuele markdown code block
        m = re.search(r"\{[^{}]*\}", text, re.DOTALL)
        if m:
            text = m.group(0)
        obj = json.loads(text)
        out["is_exterior"] = bool(obj.get("is_exterior")) if "is_exterior" in obj else None
        out["has_watermark"] = bool(obj.get("has_watermark")) if "has_watermark" in obj else None
        out["is_collage"] = bool(obj.get("is_collage")) if "is_collage" in obj else None
    except Exception:
        pass
    return out
