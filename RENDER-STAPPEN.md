# Stap voor stap: LQM Advertentie Agent op Render

Volg deze stappen om de app online te zetten op Render (gratis tier).

---

## Stap 1: Project op GitHub zetten

Als je dat nog niet hebt gedaan:

1. Ga naar [github.com](https://github.com) en log in.
2. Klik rechtsboven op **+** → **New repository**.
3. Vul in:
   - **Repository name:** bijv. `lqm-advertentie-agent`
   - **Public**
   - Vink **niet** aan: "Add a README" (je hebt al bestanden)
4. Klik **Create repository**.

Daarna op je computer, in de map waar de app staat (`lqm-advertentie-agent`):

5. Open een terminal/command prompt in die map.
6. Voer uit (vervang `JOUW-GEBRUIKERSNAAM` door je GitHub-gebruikersnaam):

```bash
git init
git add .
git commit -m "Eerste versie LQM Advertentie Agent"
git branch -M main
git remote add origin https://github.com/JOUW-GEBRUIKERSNAAM/lqm-advertentie-agent.git
git push -u origin main
```

7. Als Git om een wachtwoord vraagt: gebruik een **Personal Access Token** (GitHub → Settings → Developer settings → Personal access tokens). Of log in via de browser als Git dat aanbiedt.

---

## Stap 2: Account op Render

1. Ga naar [render.com](https://render.com).
2. Klik op **Get Started** of **Sign Up**.
3. Kies **Sign up with GitHub** en autoriseer Render voor je GitHub-account.

---

## Stap 3: Nieuwe Web Service maken

1. In het Render-dashboard: klik op **New +**.
2. Kies **Web Service**.
3. Onder "Connect a repository" zie je je GitHub-repo’s. Klik bij **lqm-advertentie-agent** op **Connect** (als je de repo nog niet ziet: **Configure account** en geef Render toegang tot de juiste repo).
4. Klik **Connect** naast je repo `lqm-advertentie-agent`.

---

## Stap 4: Instellingen invullen

Render vult veel al in. Controleer en pas zo nodig aan:

| Veld | Waarde |
|------|--------|
| **Name** | `lqm-advertentie-agent` (of een andere naam; wordt deel van de URL) |
| **Region** | Kies bijv. **Frankfurt** (dichtbij NL) |
| **Branch** | `main` |
| **Root Directory** | Laat **leeg** als de app in de hoofdmap van de repo staat. Staat de app in een submap (bijv. `lqm-advertentie-agent`), vul dan die map in. |
| **Runtime** | **Python 3** |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn --bind 0.0.0.0:$PORT app:app` |
| **Instance Type** | **Free** |

Laat andere opties (Environment Variables, etc.) voor nu leeg.

---

## Stap 5: Deploy starten

1. Klik onderaan op **Create Web Service**.
2. Render gaat nu:
   - de code ophalen van GitHub
   - `pip install -r requirements.txt` uitvoeren
   - de app starten met gunicorn
3. Wacht tot de build klaar is (een paar minuten). Je ziet de log in het scherm.
4. Als de status **Live** (groen) is, is de app online.

---

## Stap 6: URL openen

1. Bovenin het scherm staat de URL van je service, bijv.:
   - `https://lqm-advertentie-agent.onrender.com`
2. Klik erop of kopieer en plak in je browser.
3. Je zou nu het formulier moeten zien: voer een advertentie-URL in en klik **Analyseren**.

---

## Problemen?

- **Build failed**  
  Controleer in de build-log of `pip install -r requirements.txt` goed is uitgevoerd. Zorg dat `requirements.txt` in de root van je repo staat (of in de Root Directory die je bij Render hebt ingevuld).

- **Application failed to respond**  
  Controleer of **Start Command** precies is:  
  `gunicorn --bind 0.0.0.0:$PORT app:app`  
  (met `$PORT`, geen spatiefout.)

- **Eerste keer traag**  
  Op de gratis tier gaat de service na ~15 min inactiviteit slapen. Het eerste verzoek na een tijdje kan 30–60 seconden duren; daarna is het weer snel.

---

## Later: wijzigingen online zetten

1. Pas de code lokaal aan.
2. In de app-map:
   ```bash
   git add .
   git commit -m "Beschrijving van de wijziging"
   git push
   ```
3. Render merkt de push op en start automatisch een nieuwe deploy. Na een paar minuten staat de nieuwe versie online.
