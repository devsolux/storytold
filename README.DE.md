# Storytold

**Lokale Kreativarbeit. Native App-Engines. Verifizierte Dateiübergaben.**

Ein Plugin für Claude Code und Codex für die quelloffene ArtCraft **Craft App
Suite**: Ein `craft`-Skill steuert dreizehn lokale, headless laufende
Craft-MCP-Apps (Foto, Vektor, Video, RAW, PDF, Layout, Tabellen, Dokumente,
Folien, CAD, Audio, Motion und Interface-Design) über bereitgestellte Kopien und
verifizierte Exporte.

[![CI](https://github.com/devsolux/storytold/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/devsolux/storytold/actions/workflows/ci.yml)
[![Latest release](https://img.shields.io/github/v/release/devsolux/storytold)](https://github.com/devsolux/storytold/releases/latest)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)](pyproject.toml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

[English](README.md) · **Deutsch** · [Türkçe](README.TR.md)

> **Danke, ArtCraft-Team!** Storytold baut auf der Craft App Suite auf, die das
> [ArtCraft](https://getartcraft.com/)-Team als freie, quelloffene Software
> veröffentlicht hat: dreizehn Kreativ-Apps, jede von Grund auf neu geschrieben.
> Wir sind dankbar für diese Großzügigkeit. Ohne ihre Arbeit gäbe es diese
> Integration nicht.
>
> ❤️ **ArtCraft-Team** 💚

## Inhalt

- [Überblick](#überblick)
- [Schnellstart](#schnellstart)
- [Die Craft App Suite](#die-craft-app-suite)
- [Native Apps einrichten](#native-apps-einrichten)
- [Aktualisieren und entfernen](#aktualisieren-und-entfernen)
- [Wo was liegt](#wo-was-liegt)
- [Sicher arbeiten](#sicher-arbeiten)
- [Entwicklung](#entwicklung)
- [Verifikationsstand](#verifikationsstand)
- [Repository-Übersicht](#repository-übersicht)
- [Lizenz und Zugehörigkeit](#lizenz-und-zugehörigkeit)

## Überblick

Storytold ist das lokale Integrationskit von Devsolux für die dreizehn
bestehenden Craft-CLI-MCP-Server. Ein kompakter `craft`-Skill leitet den Host
an; jede App behält ihre eigenen Schemas, ihren Bearbeitungszustand, ihr
Rendering und ihre Speichersemantik. Deterministische Helfer installieren und
pinnen die CLIs auf ausdrücklichen Befehl, stellen Dateien bereit, erzeugen
evidenzgebundene Konfiguration und prüfen Artefakte innerhalb klar benannter
Grenzen.

```text
Nutzer + Claude Code / lokaler Codex
           │  ein craft-Skill; native Tool-Erkennung und Freigaben
           ├── stdio ── PhotoCraft, VectorCraft, FilmCraft, LightCraft
           ├── stdio ── PdfCraft, EffectCraft, DesignCraft, GridCraft
           ├── stdio ── WordCraft, DeckCraft, CADCraft, SoundCraft
           └── stdio ── FigCraft
                                │
                      native Engines → dauerhafte Dateien
```

**Was es ist**

- Ein anleitender Skill, dreizehn bei Bedarf geladene App-Karten und zwei
  Workflow-Anleitungen.
- Dreizehn direkte, native stdio-MCP-Registrierungen, eine pro App und Host.
- Eine Python-CLI nur mit der Standardbibliothek (`storytold.py`), die die
  Craft-CLIs installiert, verifiziert, pinnt, prüft und registriert, aber nur,
  wenn du sie ausführst.

**Was es nicht ist**

- Kein Gateway-MCP-Server, kein Daemon, kein Router und kein zweiter KI-Agent.
- Keine mitgelieferten Binärdateien: Die Plugin-Installation fügt Anleitung,
  das geprüfte Release-Manifest und inaktive Vorlagen hinzu, niemals
  ausführbare Dateien, Berechtigungen oder laufende MCP-Prozesse.
- Kein entfernter ChatGPT-Connector. Die lokale Codex-Unterstützung ist eine
  ergänzende Paketierungs- und Konfigurationsanpassung.
- Keine OS-Sandbox. Siehe [Sicher arbeiten](#sicher-arbeiten) und
  [SECURITY.md](SECURITY.md).

## Schnellstart

**1. Plugin installieren.** Repository `devsolux/storytold`, Plugin
`storytold`, Marketplace `devsolux-storytold`. Beide Hosts erwarten
**plugin@marketplace**:

```bash
claude plugin marketplace add https://github.com/devsolux/storytold
claude plugin install storytold@devsolux-storytold

codex plugin marketplace add devsolux/storytold
codex plugin add storytold@devsolux-storytold
```

**2. Native Apps installieren.** Aus einem Klon oder aus dem installierten
Plugin-Verzeichnis (`<home>/plugins/cache/devsolux-storytold/storytold/<version>/`
unter `~/.claude` bzw. `~/.codex`) eine App oder alle dreizehn einrichten:

```bash
python3 storytold.py setup --app photocraft
```

```bash
python3 storytold.py setup --all --acknowledge-unconfined
```

**3. Eine neue Host-Sitzung starten** und den Skill nutzen: `/storytold:craft`
in Claude Code oder `storytold:craft` aus der Skill-Auswahl von Codex.

`python3 storytold.py doctor` meldet je App die gefundene Desktop-App, CLI und
Host-Registrierung und gibt für alles Fehlende den genauen `setup`-Befehl aus;
der Skill bietet denselben Befehl im Chat an, wenn ein Server nicht verbunden
ist.

## Die Craft App Suite

Der ArtCraft Launcher installiert die **Craft App Suite**: freie, quelloffene
Kreativwerkzeuge des [ArtCraft](https://getartcraft.com/)-Teams, jedes von
Grund auf in Rust geschrieben und jedes eigenständig nutzbar. Die Spalte
**Dateizugriff** zeigt, wie Storytold den MCP-Server jeder App startet.

| | App | Wofür | Dateizugriff | Code | Mehr |
|:-:|---|---|---|---|---|
| <img src="https://raw.githubusercontent.com/storytold/photocraft/main/assets/app-icon/hicolor/64x64/apps/ai.storyteller.photocraft.png" alt="" width="32" height="32"> | **PhotoCraft** | Bildbearbeitung: Ebenen, Masken, Text und echte PSD-Dateien | Lese-/Schreibwurzeln | [GitHub](https://github.com/storytold/photocraft) | [Website](https://getartcraft.com/apps/photocraft) |
| <img src="https://raw.githubusercontent.com/storytold/vectorcraft/main/assets/app-icon/hicolor/64x64/apps/ai.storyteller.vectorcraft.png" alt="" width="32" height="32"> | **VectorCraft** | Vektorillustration | Lese-/Schreibwurzeln | [GitHub](https://github.com/storytold/vectorcraft) | [Website](https://getartcraft.com/apps/vectorcraft) |
| <img src="https://raw.githubusercontent.com/storytold/filmcraft/main/assets/app-icon/hicolor/64x64/apps/ai.storyteller.filmcraft.png" alt="" width="32" height="32"> | **FilmCraft** | Videoschnitt, Farbe und Ton | Benutzerweit | [GitHub](https://github.com/storytold/filmcraft) | [Website](https://getartcraft.com/apps/filmcraft) |
| <img src="https://raw.githubusercontent.com/storytold/lightcraft/main/assets/app-icon/hicolor/64x64/apps/ai.storyteller.lightcraft.png" alt="" width="32" height="32"> | **LightCraft** | Fotobibliothek und RAW-Entwicklung | Benutzerweit | [GitHub](https://github.com/storytold/lightcraft) | [Website](https://getartcraft.com/apps/lightcraft) |
| <img src="https://raw.githubusercontent.com/storytold/pdfcraft/main/assets/app-icon/hicolor/64x64/apps/ai.storyteller.pdfcraft.png" alt="" width="32" height="32"> | **PdfCraft** | PDFs lesen, ordnen und schützen | Einzelne Wurzel | [GitHub](https://github.com/storytold/pdfcraft) | [Website](https://getartcraft.com/apps/pdfcraft) |
| <img src="https://raw.githubusercontent.com/storytold/effectcraft/main/assets/app-icon/hicolor/64x64/apps/ai.storyteller.effectcraft.png" alt="" width="32" height="32"> | **EffectCraft** | Motion Graphics und visuelle Effekte | Lese-/Schreibwurzeln | [GitHub](https://github.com/storytold/effectcraft) | [Website](https://getartcraft.com/apps/effectcraft) |
| <img src="https://raw.githubusercontent.com/storytold/designcraft/main/assets/app-icon/hicolor/64x64/apps/ai.storyteller.designcraft.png" alt="" width="32" height="32"> | **DesignCraft** | Seitenlayout und Publishing | Benutzerweit | [GitHub](https://github.com/storytold/designcraft) | [Website](https://getartcraft.com/apps/designcraft) |
| <img src="https://raw.githubusercontent.com/storytold/gridcraft/main/assets/app-icon/hicolor/64x64/apps/ai.storyteller.gridcraft.png" alt="" width="32" height="32"> | **GridCraft** | Tabellenkalkulation und Daten | Benutzerweit | [GitHub](https://github.com/storytold/gridcraft) | [Website](https://getartcraft.com/apps/gridcraft) |
| <img src="https://raw.githubusercontent.com/storytold/wordcraft/main/assets/app-icon/hicolor/64x64/apps/ai.storyteller.wordcraft.png" alt="" width="32" height="32"> | **WordCraft** | Textverarbeitung und Dokumente | Lese-/Schreibwurzeln | [GitHub](https://github.com/storytold/wordcraft) | [Website](https://getartcraft.com/apps/wordcraft) |
| <img src="https://raw.githubusercontent.com/storytold/deckcraft/main/assets/app-icon/hicolor/64x64/apps/ai.storyteller.deckcraft.png" alt="" width="32" height="32"> | **DeckCraft** | Präsentationen und Folien | Benutzerweit | [GitHub](https://github.com/storytold/deckcraft) | [Website](https://getartcraft.com/apps/deckcraft) |
| <img src="https://raw.githubusercontent.com/storytold/cadcraft/main/assets/app-icon/hicolor/64x64/apps/ai.storyteller.cadcraft.png" alt="" width="32" height="32"> | **CADCraft** | Computergestütztes Konstruieren (CAD) | Benutzerweit | [GitHub](https://github.com/storytold/cadcraft) | [Website](https://getartcraft.com/apps/cadcraft) |
| <img src="https://raw.githubusercontent.com/storytold/soundcraft/main/assets/app-icon/hicolor/64x64/apps/ai.storyteller.soundcraft.png" alt="" width="32" height="32"> | **SoundCraft** | Audioaufnahme und -bearbeitung | Lese-/Schreibwurzeln | [GitHub](https://github.com/storytold/soundcraft) | [Website](https://getartcraft.com/apps/soundcraft) |
| <img src="https://raw.githubusercontent.com/storytold/figcraft/main/assets/app-icon/hicolor/64x64/apps/ai.storyteller.figcraft.png" alt="" width="32" height="32"> | **FigCraft** | Interface-Design und Prototyping | Benutzerweit | [GitHub](https://github.com/storytold/figcraft) | [Website](https://getartcraft.com/apps/figcraft) |

- **Lese-/Schreibwurzeln** (fünf Apps): mit nativen Wurzel-Flags gestartet, die
  ihnen erlauben, den Workspace zu lesen und nur in dessen Verzeichnis
  `outputs/` zu schreiben.
- **Einzelne Wurzel** (PdfCraft): eine Wurzel, die den ganzen Workspace
  einschließlich `inputs/` umfasst; das ist keine getrennte
  Lese-/Schreibbeschränkung.
- **Benutzerweit** (sieben Apps): keine Wurzel-Flags, daher können sie alles
  lesen und schreiben, was dein OS-Benutzer darf. `setup` installiert und
  registriert sie nur mit `--acknowledge-unconfined`; nutze sie für unkritische
  Arbeit oder lass sie unter OS-Isolation laufen.

## Native Apps einrichten

Der MCP-Server jeder App ist ihre CLI, `<app>-cli`. Weder das Plugin noch die
Desktop-App stellt sie bereit oder registriert sie; bis sie eingerichtet ist,
meldet der Skill zu Recht, dass die nativen Werkzeuge der App nicht verbunden
sind. `setup` unterstützt macOS (universal), Linux x86_64 und Windows x64 und
erfordert Python 3.11+.

### Was `setup` tut

Für jede ausgewählte App durchläuft `setup` diese Schritte:

1. Herunterladen des für deine Plattform in
   [`config/releases.json`](config/releases.json) gepinnten Archivs (der
   macOS-CLI-Zip, des Linux-Tarballs oder der portablen Windows-Zip).
2. Prüfen gegen dieses Manifest **und** die `SHA256SUMS.txt` des Releases, dann
   Entnahme genau der einen `<app>-cli`.
3. Verifizieren der Herkunft (siehe [Herkunft](#herkunft)).
4. Bereitstellen des Kandidaten neben der aktiven Installation und Ausführen von
   Preflight sowie der Prüfung über das offizielle MCP-SDK: initialize,
   tools/list und ein Nur-Lese-Aufruf.
5. Erst dann Befördern nach `~/.local/opt/craft/bin` (bzw.
   `%LOCALAPPDATA%\Storytold\craft\bin` unter Windows) und Pinnen des
   Binär-Hashes in einem privaten Lock.
6. Registrieren des Servers bei jeder Host-CLI im PATH (`codex mcp add`,
   `claude mcp add --scope user`).

Ein Kandidat, der an irgendeinem Schritt scheitert, lässt die bisherige
Binärdatei, ihren Pin und die Registrierungen unberührt; ein Upgrade, das
zwischen dem Ersetzen der Datei und dem Neuschreiben des Locks unterbrochen
wurde, bringt der nächste Lauf in einen konsistenten Zustand. Ein erneutes
`setup` ist idempotent: Eine App, deren installierte Binärdatei zu ihrem Pin und
zum Manifest passt, wird übersprungen, und eine passende Registrierung bleibt
bestehen. Nichts läuft, ohne dass du es aufrufst. Starte danach eine neue
Host-Sitzung.

### Optionen

| Option | Wirkung |
|---|---|
| `--app <app>` / `--all` | Eine App auswählen (wiederholbar) oder alle dreizehn. |
| `--acknowledge-unconfined` | Auch die sieben benutzerweiten Apps installieren und registrieren. Kein Nachweis von Isolation. |
| `--host {codex,claude}` | Nur bei einem Host registrieren (Standard: jede Host-CLI im PATH). |
| `--dry-run` | Vorschau auf Downloads, Pfade und Registrierungen oder, mit `--remove`, genau auf das, was entfernt würde. Ändert nichts. |
| `--list` | Manifest-, Installations-, Pin- und Registrierungsstand sowie die verwendeten Pfade anzeigen. |
| `--upgrade` | Eine App mit geändertem Pin auf das Manifest-Release bringen. |
| `--replace` | Einen gleichnamigen Server neu registrieren, der woanders hinzeigt; der alte Eintrag wird wiederhergestellt, wenn der neue nicht hinzugefügt werden kann. |
| `--remove` | Nur die Benutzer-Registrierungen aufheben, die `setup` selbst geschrieben hat (gleicher Befehl und gleiche Argumente, App noch gepinnt), und nur eine Binärdatei löschen, deren Bytes zum Lock passen; alles andere wird gemeldet und bleibt. |
| `--skip-probe` | Registrieren, ohne die Binärdatei auszuführen, und das auch so melden. |
| `--trust-upstream-sums` | Linux/Windows: allein auf Basis von Manifest und `SHA256SUMS.txt` fortfahren, wenn kein Sigstore-Bundle oder cosign verfügbar ist; wird im Lock vermerkt. |

`python3 storytold.py setup --help` listet die übrigen Pfad- und
Timeout-Overrides. Andere Plattformen, abgeschottete Rechner und eigene Pins
nutzen die manuelle Kette in [Betrieb](docs/operations.md): herunterladen, Lock,
`preflight`, `probe`, `configure`, registrieren.

### Herkunft

Unter macOS muss die Binärdatei vom ArtCraft-Team bei Apple notarisiert sein.
Upstream signiert Linux- und Windows-Builds nicht, daher signiert der
[tägliche Workflow](.github/workflows/releases.yml) jede gepinnte CLI
schlüssellos mit [Sigstore cosign](https://docs.sigstore.dev/) unter seiner
eigenen GitHub-Identität und committet die Bundles nach
[`config/signatures.json`](config/signatures.json). Unter Linux und Windows
verifiziert `setup` dieses Bundle vor der Installation mit `cosign verify-blob`
(cosign zuerst installieren); macOS verifiziert es ebenfalls, wenn cosign
vorhanden ist. Solange ein Release kein Bundle hat oder cosign fehlt, fährt
`--trust-upstream-sums` allein auf Basis von Manifest und `SHA256SUMS.txt` fort
und vermerkt das im Lock.

### Tägliche Release-Aktualisierung

Der Workflow prüft jeden Tag das neueste Release jeder App, schreibt das
Manifest neu, signiert neue CLIs, baut das Plugin neu, führt die Checks und das
echte `setup` auf Linux-, Windows- und macOS-Runnern aus und öffnet zur Prüfung
einen Pull Request auf `bot/releases` (setze die Repository-Variable
`STORYTOLD_AUTO_MERGE=true`, um grüne Läufe automatisch zu mergen). Nutzer
erhalten die neuen Pins mit dem nächsten Plugin-Update.

## Aktualisieren und entfernen

### Aktualisieren

Die Aktualisierung hat zwei Schritte. Zuerst das Plugin aktualisieren:

```bash
claude plugin marketplace update devsolux-storytold
claude plugin update storytold@devsolux-storytold

codex plugin marketplace upgrade devsolux-storytold
codex plugin add storytold@devsolux-storytold
```

Codex kennt kein `plugin update`: `marketplace upgrade` aktualisiert den
Git-Snapshot, und ein erneutes `plugin add` installiert daraus die neuere
Version. Ein Plugin-Update bringt Skill, Doku und das aktualisierte
Release-Manifest; installierte CLIs und Host-Registrierungen bleiben unberührt,
und das Plugin-Verzeichnis trägt danach die neue Versionsnummer.

Danach die Craft-CLIs nachziehen. `--list` zeigt, welche Pins sich bewegt haben
(`manifest_commit_pinned: false`); `--all --upgrade` lädt nur diese Apps
erneut, verifiziert und prüft sie erneut und lässt die Registrierungen
unverändert:

```bash
python3 ~/.codex/plugins/cache/devsolux-storytold/storytold/<version>/storytold.py setup --list
```

```bash
python3 ~/.codex/plugins/cache/devsolux-storytold/storytold/<version>/storytold.py setup --all --upgrade --acknowledge-unconfined
```

Ändert ein Release die Startargumente einer App (WordCrafts Wurzel-Flags in
1.5.0, SoundCrafts in 1.5.2), ergänze `--replace`, damit die abweichende
Registrierung neu geschrieben wird; ohne das Flag meldet `setup` die Abweichung
nur und lässt sie stehen. SoundCraft beachtet seine Wurzeln erst ab 0.7.0,
daher wird ein älteres installiertes SoundCraft abgelehnt, bis
`setup --app soundcraft --upgrade --replace` es aktualisiert.

### Entfernen

```bash
python3 ~/.codex/plugins/cache/devsolux-storytold/storytold/<version>/storytold.py setup --remove --all
claude plugin uninstall storytold@devsolux-storytold
codex plugin remove storytold@devsolux-storytold
```

`setup --remove --all` hebt zuerst die Registrierung der dreizehn von Storytold
verwalteten CLIs auf und löscht sie samt Pins. Workspace und Ausgaben bleiben,
ebenso alles, was das Lock nicht als von Storytold installiert ausweist. Ein
bloßes Deinstallieren des Plugins ließe die Server registriert und lauffähig
zurück.

### Aus einem Quell-Checkout installieren

Die generierte Laufzeit `plugins/storytold/` ist eingecheckt, daher installieren
beide Hosts direkt aus dem öffentlichen Repository, und bei der Installation
wird nichts gebaut. Aus einem Quell-Checkout installiert stattdessen
`make install-claude-local` oder `make install-codex-local` den lokalen
Marketplace. Diese Ziele ändern den Host-Zustand; Builds und Tests führen sie
nie aus. Quellen zu Host-Paketierung und Installation sind im
[Quellenverzeichnis](docs/source-ledger.md) festgehalten.

## Wo was liegt

Das Plugin-Verzeichnis enthält nur Code, Doku und das Release-Manifest. `setup`
hält alles, was es installiert, außerhalb davon, sodass ein Plugin-Update oder
eine Deinstallation nie eine CLI löschen, zurückstufen oder austauschen kann,
und eine installierte Kopie beiden Hosts dient. `python3 storytold.py setup
--list` gibt die verwendeten Pfade aus.

| Wo (macOS/Linux) | Windows | Was | Geschrieben von |
|---|---|---|---|
| `~/.codex/plugins/cache/devsolux-storytold/storytold/<version>/`, ebenso unter `~/.claude` | ebenso unter `%USERPROFILE%` | Das Plugin: `craft`-Skill, Doku, `storytold.py`, `config/releases.json`, `config/signatures.json`. Keine Binärdateien. | `codex plugin add` / `claude plugin install` |
| `~/.local/opt/craft/bin/` | `%LOCALAPPDATA%\Storytold\craft\bin\` | Die dreizehn Craft-CLIs (`photocraft-cli` … `figcraft-cli`, je 16–192 MB). Beide Hosts starten diese, z. B. `…/cadcraft-cli mcp`. | `setup` |
| `~/.local/state/storytold/` (`$XDG_STATE_HOME/storytold` unter Linux) | `%LOCALAPPDATA%\Storytold\state\` | Privater Zustand: `installations.lock.json` (gepinnte Hashes), `evidence/` (Prüfbelege je App), `venv/` (offizielles MCP-SDK für die Prüfung), `setup.json` (gemerkte Pfade). | `setup` |
| `~/craft-work-storytold/` | `%USERPROFILE%\craft-work-storytold\` | Der Workspace: `inputs/`, `outputs/` (Exporte landen hier), `receipts/`. | `setup` legt ihn an; die Apps füllen `outputs/` |
| `~/.codex/config.toml` und `~/.claude.json` | ebenso | Eine MCP-Registrierung im Benutzerbereich je App und Host, die auf den absoluten CLI-Pfad oben zeigt. | `codex mcp add`, `claude mcp add --scope user`, ausgeführt von `setup` |

Die vollständigen Unix-Startvorlagen unter `config/` sind nur Beispiele, keine
aktive Host-Konfiguration. Die echte Konfigurationserzeugung wählt unter
nativem Windows `.exe` und gibt konkrete, geprüfte Pfade aus, statt sich darauf
zu verlassen, dass Umgebungsvariablen auf allen Hosts gleich expandiert werden.
Rechnerspezifische Konfiguration bleibt aus Paketen heraus.

## Sicher arbeiten

Jede Aufgabe folgt derselben Schleife:

**Prüfen → bereitgestellte Kopie → native Bearbeitung → Vorschau →
speichern/exportieren → erneut öffnen/verifizieren.**

- **App-Karten.** Die [dreizehn App-Karten](skills/craft/SKILL.md) beschreiben
  app-spezifische Fallstricke: headless Auswahl in VectorCraft,
  Bibliothekssperren in LightCraft, explizites Speichern in PdfCraft,
  UTF-8-Byte-Offsets in DesignCraft, typisierte Formeln in GridCraft,
  Seiteneinheiten in FigCraft, Medien-Timing und Offline-Warnungen. Das sind aus
  den Quellen abgeleitete Hinweise; die verbundene Binärdatei liefert die
  maßgebliche API.
- **App-übergreifende Arbeit.** Übergib verifizierte Dateien, niemals die
  In-Memory-IDs eines anderen Servers. PhotoCraft kann ein PNG für DesignCraft
  exportieren, DesignCraft ein PDF für PdfCraft. Scheitert eine Stufe, bleib beim
  letzten verifizierten Artefakt stehen. Es gibt weder eine universelle
  Batch-Transaktion noch automatische Schreibwiederholung noch einen versteckten
  Ausweichpfad.
- **Beschränkung.** Wurzel-Flags, der Skill, Prüfbelege und die
  MCP-Konfiguration sind keine OS-Sandbox, und auch andere Shell- und
  Datei-Werkzeuge des Hosts brauchen passende Berechtigungen. Geschäftlicher
  Einsatz setzt die lokalen Stufen in [Abnahme](docs/acceptance.md) und die
  Maßnahmen in [SECURITY.md](SECURITY.md) voraus.

## Entwicklung

Python **3.11+** führt die Kernwerkzeuge und Tests aus; GNU Make ist
optionaler Komfort. Die Standard-Checks und der Build brauchen keine
Python-Pakete von Dritten und keinen Netzwerkzugriff.

```bash
make check
make test
make build
make verify-build
```

| Ziel | Zweck |
|---|---|
| `make help` | Alle Ziele auflisten; installiert und startet nichts. |
| `make doctor` | Installierte Fähigkeiten melden, ohne Hosts oder native Apps zu starten. |
| `make check` | Quellen, Links, Identitäten, Katalog, Beispiele und inaktive Paketierung validieren. |
| `make test` | Alle Kerntests in einer isolierten Quellkopie ausführen; kein Netzwerk, keine nativen Binärdateien. |
| `make build` / `make verify-build` | Das gemeinsame Plugin aus freigegebenen kanonischen Dateien erzeugen und anschließend auf Abweichungen prüfen. |
| `make package` / `make source` | Das deterministische Plugin-ZIP und das vollständige Quell-ZIP erzeugen, jeweils mit Prüfsumme. |
| `make release` | Geordnete Checks, Kerntests und reproduzierbare Paketierung; keine Veröffentlichung, keine Behauptung nativer Abnahme. |
| `make setup` / `make setup-probe` | Eine lokale `.venv` anlegen; danach als ausdrückliches Netzwerk-Opt-in das hash-gesperrte offizielle MCP-SDK (`mcp==2.3.0`) installieren. |
| `make test-sdk` | Das echte SDK gegen ein synthetisches stdio-Fixture prüfen, nicht gegen die Craft-Apps. |
| `make refresh-releases` / `make sign-releases` | Die Netzwerkschritte des täglichen Workflows (Signieren braucht cosign). |
| `make setup-confined` | Die sechs wurzelbeschränkten Apps auf diesem Rechner installieren, pinnen, prüfen und registrieren. |
| `make clean` | Nur markierte `.build/` und `dist/` entfernen; Workspaces und `.venv` bleiben. |

Builds und Tests committen, pushen und installieren nie; nur die ausdrücklich
benannten `make github-*`-Ziele committen oder pushen. Das [Makefile](Makefile)
listet alle Ziele, und [CONTRIBUTING.md](CONTRIBUTING.md) beschreibt die
Beitragsregeln.

## Verifikationsstand

Die Offline-Kerntests, der Vertragstest mit dem offiziellen MCP-SDK, die
strikte Validierung der Claude-Manifeste und die Installation in Claude Code und
Codex mit Skill-Erkennung wurden ausgeführt. `setup` hat alle dreizehn
Craft-CLIs auf macOS-, Linux- und Windows-Runnern installiert, geprüft und per
Sigstore verifiziert, zwölf davon auch auf einem Entwickler-Mac. Das ist ein
Nachweis auf Protokollebene, keine native Abnahme: Die Stufen in
[Abnahme](docs/acceptance.md) führt der Betreiber selbst aus. Der
[Verifikationsbericht](docs/verification.md) trennt, was für jedes Release
ausgeführt wurde, von dokumentarischen Belegen.

## Repository-Übersicht

| Pfad | Zuständigkeit |
|---|---|
| `skills/craft/` | Ein anleitender Skill, dreizehn App-Karten und zwei Workflows |
| `config/` | Geprüfter Startkatalog, Release-Manifest und Sigstore-Bundle-Speicher, inaktive Vorlagen, Beispiel-Lock und -Env |
| `storytold_tools/`, `storytold.py` | Deterministische CLI und optionale kurzlebige SDK-Prüfung |
| `scripts/`, `Makefile` | Offline-Checks, Tests, abgesicherte Builds und Paketierung |
| `tests/` | Kern-Regressionstests, synthetisches SDK-Fixture, native Abnahmeszenarien |
| `docs/` | Architektur, Betrieb, Abnahme, Quellen und Verifikation |
| `plugins/storytold/` | Generierte gemeinsame Laufzeit; niemals direkt bearbeiten |
| `.github/workflows/` | Offline-CI-Matrix sowie tägliche Release-Aktualisierung, Signierung und Verifikation auf drei Betriebssystemen |

[Architektur](docs/architecture.md) hält fest, warum der native Plan Vorrang vor
der älteren Gateway-Referenz hat und welche Komponente wofür zuständig ist.

## Lizenz und Zugehörigkeit

Veröffentlicht unter der [MIT-Lizenz](LICENSE). Native Apps, SDKs, Schriften
und Medien werden nicht mitgeliefert und behalten ihre eigenen Lizenzen; siehe
den [Lizenzhinweis](LICENSE-NOTICE.md).

Storytold ist eine Devsolux-Integration. Es wird keine Zugehörigkeit zur oder
Billigung durch die Upstream-Organisation `storytold`, Anthropic oder OpenAI
behauptet.
