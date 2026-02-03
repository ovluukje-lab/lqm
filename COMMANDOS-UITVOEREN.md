# Hoe voer ik die commando's uit?

Je moet ze in een **terminal** (opdrachtprompt) typen. Zo doe je dat op Windows.

---

## Stap 1: Terminal openen in de juiste map

### Optie A – Via Verkenner (makkelijkst)

1. Open **Verkenner** (Windows-toets + E).
2. Ga naar de map waar de app staat:  
   `C:\Users\vanoe\lqm-advertentie-agent`
3. Klik **eenmaal** in het adresbalk (bovenin, waar het pad staat).
4. Typ: `cmd` en druk op **Enter**.  
   Er opent een zwart venster; je zit dan al in die map.

### Optie B – Via Cursor / VS Code

1. Open de map `lqm-advertentie-agent` in Cursor (of VS Code).
2. Druk op **Ctrl + `** (backtick, links naast de 1) of menu **Terminal** → **New Terminal**.
3. Onderaan opent een terminal; die staat meestal al in je projectmap.

### Optie C – Handmatig naar de map gaan

1. Druk op **Windows-toets + R**, typ `cmd`, druk op **Enter**.
2. In het zwarte venster typ je:
   ```
   cd C:\Users\vanoe\lqm-advertentie-agent
   ```
   en druk op **Enter**.

---

## Stap 2: Eén voor één de commando's plakken

1. Ga naar **DEPLOY-MINIMAAL.md** (of hieronder) en kopieer het **eerste** commando, bijvoorbeeld:
   ```
   git init
   ```
2. Klik **in het zwarte terminalvenster** (zodat de cursor daar knippert).
3. **Rechtermuisklik** om te plakken (of Ctrl + V).
4. Druk op **Enter**.
5. Herhaal voor elk volgend commando: kopiëren → in terminal plakken → Enter.

**Let op:** Vervang `JOUW-GEBRUIKERSNAAM` door je echte GitHub-gebruikersnaam in het commando met `git remote add origin ...`.

---

## Alle commando's op een rij (na “Deel 1: GitHub”)

Voer ze **één voor één** uit (na elke regel Enter):

```
git init
```
```
git add .
```
```
git commit -m "LQM Advertentie Agent"
```
```
git branch -M main
```
```
git remote add origin https://github.com/JOUW-GEBRUIKERSNAAM/lqm-advertentie-agent.git
```
*(vervang JOUW-GEBRUIKERSNAAM door je GitHub-gebruikersnaam)*

```
git push -u origin main
```

---

## Als er iets misgaat

- **"git is niet herkend"**  
  Git is dan nog niet geïnstalleerd. Download: https://git-scm.com/download/win en installeer. Daarna terminal opnieuw openen.

- **Vraagt om inloggen**  
  Bij `git push` kan Git om je GitHub-gebruikersnaam en wachtwoord vragen. Gebruik als wachtwoord een **Personal Access Token**: GitHub → Settings → Developer settings → Personal access tokens → Generate new token. Kopieer de token en plak die waar om een wachtwoord wordt gevraagd.

- **"remote origin already exists"**  
  De koppeling met GitHub bestaat al. Sla `git remote add origin ...` over en voer alleen uit: `git push -u origin main`. Als de URL toch verkeerd is (andere gebruikersnaam), voer dan eerst uit: `git remote remove origin` en daarna opnieuw `git remote add origin https://github.com/JOUW-GEBRUIKERSNAAM/lqm-advertentie-agent.git`, en dan `git push -u origin main`.
