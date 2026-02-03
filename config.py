# LQM Advertentie Agent - configuratie
import re

# Postcode regex per land (NL, BE, DE, FR)
POSTCODE_PATTERNS = {
    "NL": re.compile(r"^\d{4}\s*[A-Za-z]{2}$"),   # 1234 AB
    "BE": re.compile(r"^\d{4}$"),                  # 1000
    "DE": re.compile(r"^\d{5}$"),                   # 10115
    "FR": re.compile(r"^\d{5}$"),                   # 75001
}

# COVID-gerelateerde zoekwoorden
COVID_KEYWORDS = ["corona", "covid", "pandemie", "lockdown", "1,5 meter", "anderhalve meter"]

# Min. lengte postcode (fallback andere landen)
POSTCODE_MIN_LEN = 4
POSTCODE_MAX_LEN = 10
