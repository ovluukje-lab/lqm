# GitHub is gekoppeld aan Render – wat nu?

Je hebt GitHub aan Render gekoppeld. Volg deze stappen om de LQM-app live te zetten.

---

## Stap 1: Nieuwe Web Service maken

1. Ga naar [dashboard.render.com](https://dashboard.render.com).
2. Klik op **New +** (rechtsboven).
3. Kies **Web Service**.

---

## Stap 2: Repo kiezen

1. Je ziet nu een lijst met je GitHub-repo’s.
2. Zoek **lqm-advertentie-agent** (of de naam van je repo).
3. Klik op **Connect** naast die repo.

*(Als je de repo niet ziet: klik op **Configure account** en geef Render toegang tot de juiste GitHub-repo’s.)*

---

## Stap 3: Instellingen invullen

Render vult een deel al in. Controleer en vul aan:

| Veld | Wat je invult of kiest |
|------|-------------------------|
| **Name** | Laat staan of typ bijv. `lqm-advertentie-agent` |
| **Region** | Bijv. **Frankfurt** |
| **Branch** | `main` |
| **Root Directory** | **Leeg laten** (tenzij je code in een submap staat) |
| **Runtime** | **Python 3** |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn --bind 0.0.0.0:$PORT app:app` |
| **Instance Type** | **Free** |

Belangrijk: **Build Command** en **Start Command** moeten precies zo zijn (inclusief `$PORT` in het startcommando).

---

## Stap 4: Deploy starten

1. Scroll naar beneden.
2. Klik op **Create Web Service**.
3. Render bouwt nu je app (een paar minuten). Je ziet de build-log.
4. Wacht tot de status **Live** (groen) is.

---

## Stap 5: Je app openen

1. Bovenin het scherm staat de URL van je service, bijv.:  
   **https://lqm-advertentie-agent.onrender.com**
2. Klik erop of kopieer en plak in je browser.
3. Je zou nu het formulier van de LQM Advertentie Beoordelaar moeten zien.

Klaar.

---

**Tip:** Op de gratis tier gaat de service na ~15 min inactiviteit slapen. Het eerste verzoek daarna kan 30–60 seconden duren; daarna is het weer snel.
