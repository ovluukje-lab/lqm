# Render deploy – minimale checklist (±5 min)

De code is klaar. Alleen deze stappen moet jij nog doen (ik heb geen toegang tot je accounts).

---

## Deel 1: GitHub (eenmalig)

1. Ga naar **https://github.com/new**
2. Repository name: `lqm-advertentie-agent` → **Create repository**
3. Open **PowerShell** of **Command Prompt** in de map `lqm-advertentie-agent` (rechtermuisklik in de map → "Open in Terminal" of "Open PowerShell window here").
4. Plak en voer uit (vervang `JOUW-GEBRUIKERSNAAM` door je echte GitHub-gebruikersnaam):

```
git init
git add .
git commit -m "LQM Advertentie Agent"
git branch -M main
git remote add origin https://github.com/JOUW-GEBRUIKERSNAAM/lqm-advertentie-agent.git
git push -u origin main
```

5. Log in als Git daarom vraagt (of gebruik een Personal Access Token).

---

## Deel 2: Render (eenmalig)

1. Ga naar **https://render.com** → **Get Started** → **Sign up with GitHub** (autoriseer Render).
2. Klik **New +** → **Web Service**.
3. Klik bij je repo **lqm-advertentie-agent** op **Connect**.
4. Vul alleen dit in (de rest mag blijven staan):
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn --bind 0.0.0.0:$PORT app:app`
   - **Instance Type:** Free
5. Klik **Create Web Service**.
6. Wacht tot de status **Live** is (een paar minuten).
7. Klik op de URL bovenin (bijv. `https://lqm-advertentie-agent.onrender.com`) – klaar.

---

Daarna: wijzigingen lokaal doen → in de map `git add .` → `git commit -m "..."` → `git push` → Render bouwt automatisch opnieuw.
