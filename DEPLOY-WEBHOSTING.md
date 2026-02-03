# LQM Advertentie Agent op eigen webhosting

Je hebt al een website met webhosting. Er zijn grofweg twee situaties.

---

## 1. Je hosting ondersteunt Python (SSH of “Python-app”)

Sommige hosts bieden **SSH** of een **“Python-app”** / **“Web app”** in het panel. Dan kun je de Flask-app direct op je hosting draaien.

### Wat je nodig hebt

- Toegang tot **SSH** of een **Python/Web-app** in het controlepaneel
- Python 3.8+ op de server

### Stappen (via SSH)

1. **Bestanden uploaden**  
   Upload de hele map `lqm-advertentie-agent` (of alleen de bestanden) naar je hosting, bijvoorbeeld in een submap zoals `lqm` of `advertentie-agent`. Via FTP/SFTP of Git.

2. **Virtuele omgeving en dependencies** (op de server):
   ```bash
   cd /pad/naar/lqm-advertentie-agent
   python3 -m venv venv
   source venv/bin/activate   # Linux/macOS
   # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **App starten**  
   Hoe dat moet hangt af van je host:

   - **Eigen VPS / host met systemd**  
     Maak een service die `gunicorn` start (zie hieronder “Gunicorn + systemd”).

   - **Passenger**  
     Zorg dat de app in de juiste map staat en dat `passenger_wsgi.py` aanwezig is. Soms moet je in het panel “Python-app” of “Passenger” inschakelen en de map kiezen waar `passenger_wsgi.py` staat.

   - **cPanel / “Setup Python App”**  
     Vaak kies je de map, Python-versie en het startcommando, bijvoorbeeld:
     ```text
     gunicorn --bind 0.0.0.0:$PORT app:app
     ```
     of (als er een venv is):
     ```text
     /pad/naar/venv/bin/gunicorn --bind 0.0.0.0:$PORT app:app
     ```

4. **Submap of subdomein**  
   In je panel wijs je een (sub)domein toe aan de map of app, bijv. `lqm.jouwdomein.nl` of `jouwdomein.nl/lqm`. Hoe dat precies gaat (subdomain, submap, reverse proxy) staat in de documentatie van je host.

### Voorbeeld: Gunicorn + systemd (VPS)

Op een VPS kun je de app als service laten draaien:

```bash
# In de app-map, met venv geactiveerd:
gunicorn --bind 127.0.0.1:5000 app:app
```

Maak een systemd-service (bijv. `/etc/systemd/system/lqm-agent.service`):

```ini
[Unit]
Description=LQM Advertentie Agent
After=network.target

[Service]
User=www-data
WorkingDirectory=/pad/naar/lqm-advertentie-agent
ExecStart=/pad/naar/lqm-advertentie-agent/venv/bin/gunicorn --bind 127.0.0.1:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Daarna:

```bash
sudo systemctl daemon-reload
sudo systemctl enable lqm-agent
sudo systemctl start lqm-agent
```

En in Nginx (of Apache) een virtual host die naar `127.0.0.1:5000` proxyt voor het gewenste (sub)domein.

---

## 2. Je hosting is alleen voor PHP / statische bestanden

Veel “standaard” webhosting draait alleen **PHP** en **statische bestanden**. Er is dan geen mogelijkheid om een Python/Flask-app op diezelfde host te starten.

Je hebt twee bruikbare opties.

### Optie A: Subdomein wijst naar een gratis cloud

1. Deploy de app op **Render** of **Railway** (zie README). Je krijgt een URL zoals `https://lqm-advertentie-agent.onrender.com`.
2. Bij je **domeinregistrar/hosting** maak je een **subdomein** aan (bijv. `lqm.jouwdomein.nl`) en zet je een **CNAME-record** naar die Render/Railway-URL (zoals in hun instructies).
3. Bezoekers gaan naar `https://lqm.jouwdomein.nl` en gebruiken daar de app; de app draait op Render/Railway, maar het adres is jouw domein.

### Optie B: Frontend op jouw site, API op Render

Je zet **alleen de webpagina** op je eigen hosting; de **API** draait op Render (of een andere host).

1. **API deployen**  
   Deploy de volledige app op Render (zoals in de README). Noteer de URL, bijv. `https://lqm-advertentie-agent.onrender.com`.

2. **Frontend op je eigen site**  
   - Upload de inhoud van de map `static/` naar je hosting (bijv. in `lqm/` of `advertentie-agent/`), zodat `index.html` bereikbaar is op bijv. `https://jouwdomein.nl/lqm/`.
   - Open `index.html` in een teksteditor en zet bovenaan in de `<script>` de API-URL:
   ```html
   <script>
     window.LQM_API_BASE = 'https://lqm-advertentie-agent.onrender.com';
   </script>
   ```
   (Vervang door jouw echte Render-URL.)  
   Sla het bestand op en upload het opnieuw.

3. **CORS**  
   De Flask-app staat al toe dat andere domeinen de API aanroepen (Flask stuurt de juiste headers). Als je later een eigen API-host gebruikt, moet daar ook CORS toegestaan zijn voor jouwdomein.nl.

Dan: bezoekers gaan naar `https://jouwdomein.nl/lqm/` (of jouw pad), de pagina laadt vanaf jouw hosting en de analyse gaat via de API op Render.

---

## Samenvatting

| Situatie | Aanpak |
|----------|--------|
| Hosting met Python/SSH of “Python-app” | App (incl. `passenger_wsgi.py` bij Passenger) uploaden, venv + `pip install`, gunicorn of Passenger starten, (sub)domein koppelen. |
| Alleen PHP/statisch | Subdomein CNAME naar Render/Railway **of** alleen frontend op je site met `LQM_API_BASE` naar de API op Render. |

Welke hosting gebruik je (naam/type)? Dan kunnen we de stappen nog specifieker maken (bijv. cPanel, Plesk, alleen FTP, etc.).
