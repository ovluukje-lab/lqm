# Git installeren op Windows

Als je de melding krijgt: **'git' is not recognized** – dan moet Git nog geïnstalleerd worden.

---

## Stap 1: Git downloaden

1. Ga naar: **https://git-scm.com/download/win**
2. De download start automatisch (64-bit voor de meeste Windows-pc’s).
3. Als er geen download start: klik op **Click here to download**.

---

## Stap 2: Git installeren

1. Open het gedownloade bestand (bijv. **Git-2.43.0-64-bit.exe**).
2. Klik een paar keer op **Next** (standaardinstellingen zijn prima).
3. Bij **"Adjusting your PATH environment"** laat je **Git from the command line and also from 3rd-party software** staan → **Next**.
4. Verder **Next** tot **Install** → **Install**.
5. Klik **Finish**.

---

## Stap 3: Nieuwe terminal openen

**Belangrijk:** Sluit het zwarte CMD-venster en open een **nieuwe** terminal. Anders herkent Windows Git nog niet.

- Open Verkenner → ga naar **C:\Users\vanoe\lqm-advertentie-agent** → klik in de adresbalk → typ **cmd** → Enter.

Of: start CMD opnieuw via Windows-toets + R → typ **cmd** → Enter, en typ dan:

```
cd C:\Users\vanoe\lqm-advertentie-agent
```

---

## Stap 4: Controleren of Git werkt

Typ in de terminal:

```
git --version
```

Druk op Enter. Als je iets ziet als **git version 2.43.0** (of een ander versienummer), dan werkt Git.

Daarna kun je de commando’s uit **DEPLOY-MINIMAAL.md** of **COMMANDOS-UITVOEREN.md** gewoon uitvoeren.
