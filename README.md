# LQM Advertentie Beoordelaar

Een agent die advertenties (listings) beoordeelt volgens het **LQM (Listing Quality Model)**. Je voert een URL in; de agent haalt de pagina op en analyseert de advertentie op 50 scoring-attributen in 8 categorieën.

## Categorieën

| Categorie | Beschrijving |
|-----------|--------------|
| **Description** | Lengte en recency van algemene en natuur-beschrijving, caps, COVID-verwijzingen |
| **Impact** | Duurzaamheid (sustainability leaves) |
| **Location** | Postcode, plaatsnaam |
| **Availability** | Direct boeken, channel manager, iCals, verblijftypes, geblokkeerd |
| **Photos** | Aantal foto's, CTR |
| **Guest Opinion** | Click-to-cart, reviews |
| **Filters** | Huisattributen, beleid (huisdieren, baby's, groepen, etc.), consistentie |
| **Time Settings** | Aankomst/vertrek, stilte-uren |

## Lokaal starten

```bash
cd lqm-advertentie-agent
pip install -r requirements.txt
python app.py
```

Open in de browser: **http://localhost:5000**

Voer een advertentie-URL in en klik op **Analyseren**. Het rapport toont de totaal LQM-score en per categorie alle bonus- en maluspunten.

---

## Online zetten

De app kan eenvoudig online gezet worden op o.a. **Render** of **Railway** (beide hebben een gratis tier).

### Optie 1: Render (gratis)

**Stap-voor-stap:** zie **[RENDER-STAPPEN.md](RENDER-STAPPEN.md)**.

Kort: project op GitHub zetten → [render.com](https://render.com) → **New** → **Web Service** → repo koppelen → **Build Command:** `pip install -r requirements.txt` → **Start Command:** `gunicorn --bind 0.0.0.0:$PORT app:app` → **Instance type:** Free → **Create Web Service**. Na het builden krijg je een URL zoals `https://lqm-advertentie-agent.onrender.com`.

**Let op:** Op de gratis tier valt de service na ~15 min inactiviteit in slaap; het eerste verzoek kan dan even duren.

### Optie 2: Railway (gratis credits)

1. Zet het project op **GitHub**.
2. Ga naar [railway.app](https://railway.app) en log in.
3. **New Project** → **Deploy from GitHub repo** → kies je repo (en evt. de map met `app.py`).
4. Railway herkent Python en gebruikt `requirements.txt` en `Procfile`. Als er geen Procfile wordt gebruikt, stel dan het startcommando in: `gunicorn --bind 0.0.0.0:$PORT app:app`.
5. Na deploy: **Settings** → **Generate Domain** om een publieke URL te krijgen.

### Optie 3: Eigen webhosting

Als je **al een website met webhosting** hebt, kun je de app daar zetten of de frontend daar en de API elders. Zie **[DEPLOY-WEBHOSTING.md](DEPLOY-WEBHOSTING.md)** voor:

- Hosting **met Python/SSH**: upload, venv, gunicorn of Passenger (`passenger_wsgi.py`), (sub)domein koppelen.
- Hosting **alleen PHP/statisch**: subdomein laten wijzen naar Render **of** alleen de HTML op je site met de API op Render (configureer `LQM_API_BASE` in `index.html`).

### Optie 4: Docker (eigen server of cloud)

```bash
cd lqm-advertentie-agent
docker build -t lqm-agent .
docker run -p 8080:8080 lqm-agent
```

De app is bereikbaar op **http://localhost:8080**. Je kunt dezelfde image op een VPS of cloud (bijv. Google Cloud Run, Fly.io) deployen.

## Beperking bij alleen URL

Veel LQM-attributen gebruiken **backend-data** (bijv. `allow_instant_booking`, `channel_manager_type`, iCal-fouten, CTR, click-to-cart). Die zijn niet zichtbaar op de publieke pagina. Voor die velden geeft de agent **"niet beoordeelbaar vanaf URL"** en 0 punten. Voor een volledige score is een API of database met listing-data nodig; deze agent gebruikt alleen wat van de HTML te halen is (tekst, afbeeldingen, JSON-LD, meta).

## Projectstructuur

- `app.py` – Flask-app met route `/` (formulier) en `/api/analyze` (POST met `{"url": "..."}`)
- `lqm_scorer.py` – Alle 50 LQM-attributen en 8 categorieën
- `extractor.py` – Ophalen en parsen van de pagina op de opgegeven URL
- `config.py` – Postcode-regex (NL, BE, DE, FR), COVID-zoekwoorden
- `static/index.html` – Web-UI met invoer en rapport
