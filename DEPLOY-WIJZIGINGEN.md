# Nieuwe wijzigingen deployen (na aanpassingen in de code)

Render haalt de code uit je **Git-repo** (GitHub of GitLab). De wijzigingen staan nu alleen op je computer. Zo komt de nieuwe versie online.

---

## Stap 1: Wijzigingen naar Git pushen

Render kan alleen bouwen wat **in de repo staat**. Eerst dus pushen.

1. Open een **terminal** in de map van het project:  
   `C:\Users\vanoe\lqm-advertentie-agent`
2. Voer uit (één voor één, Enter na elke regel):

```
git add .
```
```
git commit -m "LQM verbeteringen: impact-tag, instant booking, foto's ideaal 11-49, coverfoto natuur"
```
```
git push
```

3. Als Git om inloggen vraagt: gebruik je GitHub/GitLab-gebruikersnaam en (bij GitHub) een **Personal Access Token** in plaats van je wachtwoord.

Daarna staat de nieuwe code in je repo.

---

## Stap 2: Deploy in Render

**Optie A – Automatisch (meestal zo ingesteld)**  
Na `git push` start Render vaak **vanzelf** een nieuwe deploy. Wacht een paar minuten en kijk in het Render-dashboard of er een deploy loopt of net klaar is.

**Optie B – Handmatig**  
1. Ga naar [dashboard.render.com](https://dashboard.render.com).  
2. Klik op je service **lqm-advertentie-agent** (of de naam die je hebt gekozen).  
3. Bovenin: klik op **Manual Deploy** → **Deploy latest commit**.  
4. Render bouwt nu de **laatste code uit de repo** (dus wat je net hebt gepusht).  
5. Wacht tot de status **Live** (groen) is.

---

**Samenvatting:** Eerst `git add .` → `git commit -m "..."` → `git push`, daarna in Render gewoon **Manual Deploy** doen (of wachten tot de automatische deploy klaar is). Zonder push heeft Render geen nieuwe code om te deployen.
