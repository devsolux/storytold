# Storytold

Claude-Code- & Codex-Plugin für die quelloffene ArtCraft Craft App Suite: ein
`craft`-Skill steuert 13 lokale, headless laufende Craft-MCP-Apps (Foto,
Vektor, Video, RAW, PDF, Layout, Tabellen, Dokumente, Folien, CAD, Audio,
Motion, Interface-Design) mit bereitgestellten Kopien und verifizierten
Exporten.

[English](README.md) · **Deutsch** · [Türkçe](README.TR.md)

> **Danke, ArtCraft-Team!** Storytold baut auf der Craft App Suite auf, die das
> [ArtCraft](https://getartcraft.com/)-Team als freie, quelloffene Software
> veröffentlicht hat: dreizehn Kreativ-Apps, jede von Grund auf neu geschrieben.
> Wir sind dankbar für diese Großzügigkeit. Ohne ihre Arbeit gäbe es diese
> Integration nicht.
>
> ❤️ **ArtCraft-Team** 💚

**Lokale Kreativarbeit. Native App-Engines. Verifizierte Dateiübergaben.**

Storytold ist das lokale Integrationskit von Devsolux für dreizehn bestehende
Craft-CLI-MCP-Server. Ein kompakter `craft`-Skill leitet den Host an; die Apps
behalten ihre eigenen Schemas, ihren Bearbeitungszustand, ihr Rendering und
ihre Speichersemantik. Deterministische Helfer installieren und pinnen die
dreizehn CLIs auf ausdrücklichen Befehl, stellen Dateien bereit, erzeugen
evidenzgebundene Konfiguration und prüfen Artefakte innerhalb klar benannter
Grenzen. **Kein Gateway-MCP-Server und kein zweiter KI-Agent.**

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

Die Offline-Kerntests, der Vertragstest mit dem offiziellen
MCP-SDK, die strikte Validierung der Claude-Manifeste und die Installation in
Claude Code/Codex mit Skill-Erkennung wurden ausgeführt, und `setup` hat alle
dreizehn Craft-CLIs auf macOS-, Linux- und Windows-Runnern (zwölf davon auch
auf einem Entwickler-Mac) installiert, geprüft und per Sigstore verifiziert;
siehe [Verifikation](docs/verification.md). Craft-Apps werden nicht mitgeliefert:
Die Plugin-Installation installiert Anleitung, das geprüfte Release-Manifest
und inaktive Vorlagen, niemals Binärdateien, Berechtigungen oder laufende
MCP-Prozesse. Nur der ausdrückliche `setup`-Befehl unten installiert und
registriert die CLIs. Geschäftlicher Einsatz setzt die lokalen Abnahmestufen
in [Abnahme](docs/acceptance.md) voraus.

## Skill/Plugin installieren

Repository `devsolux/storytold` · Plugin `storytold` · Marketplace
`devsolux-storytold`. Beide Hosts erwarten **plugin@marketplace**:

```bash
claude plugin marketplace add https://github.com/devsolux/storytold
claude plugin install storytold@devsolux-storytold

codex plugin marketplace add devsolux/storytold
codex plugin add storytold@devsolux-storytold
```

Später aktualisieren (Schritt 1 von 2):

```bash
claude plugin marketplace update devsolux-storytold
claude plugin update storytold@devsolux-storytold

codex plugin marketplace upgrade devsolux-storytold
codex plugin add storytold@devsolux-storytold
```

Codex kennt kein `plugin update`: `marketplace upgrade` aktualisiert den
Git-Snapshot, und ein erneutes `plugin add` installiert daraus die neuere
Version. Ein Plugin-Update bringt Skill, Doku und das aktualisierte
Release-Manifest; installierte CLIs und Host-Registrierungen bleiben
unberührt, und das Plugin-Verzeichnis trägt danach die neue Versionsnummer.
Schritt 2 von 2 bewegt die Craft-CLIs:

```bash
python3 ~/.codex/plugins/cache/devsolux-storytold/storytold/<version>/storytold.py setup --list
```

```bash
python3 ~/.codex/plugins/cache/devsolux-storytold/storytold/<version>/storytold.py setup --all --upgrade --acknowledge-unconfined
```

`--list` zeigt, welche Pins sich bewegt haben (`manifest_commit_pinned: false`);
`--all --upgrade` lädt nur diese Apps erneut, verifiziert und prüft sie erneut
und lässt die Registrierungen unverändert (gleicher Befehlspfad). Ändert ein
Release die Startargumente einer App (WordCrafts Wurzel-Flags in 1.5.0,
SoundCrafts nach 1.5.1), ergänze `--replace`, damit die abweichende
Registrierung neu geschrieben wird; ohne das Flag meldet `setup` sie nur und
lässt sie stehen. SoundCraft beachtet seine Wurzeln erst ab 0.7.0, daher wird
ein älteres installiertes SoundCraft abgelehnt, bis
`setup --app soundcraft --upgrade --replace` es aktualisiert. Entfernen:

```bash
python3 ~/.codex/plugins/cache/devsolux-storytold/storytold/<version>/storytold.py setup --remove --all
claude plugin uninstall storytold@devsolux-storytold
codex plugin remove storytold@devsolux-storytold
```

`setup --remove --all` hebt zuerst die Registrierung der dreizehn von Storytold
verwalteten CLIs auf und löscht sie samt Pins (Workspace und Ausgaben bleiben,
ebenso alles, was das Lock nicht als von Storytold installiert ausweist); ein
bloßes Deinstallieren des Plugins ließe die Server registriert und lauffähig
zurück.

Die generierte Laufzeit `plugins/storytold/` ist eingecheckt, daher
installieren beide Hosts direkt aus dem öffentlichen Repository; bei der
Installation wird nichts gebaut. Aus einem Quell-Checkout installiert
stattdessen `make install-claude-local` oder `make install-codex-local` den
lokalen Marketplace. Diese Befehle ändern den Host-Zustand; Builds und Tests
führen sie nie aus, und nur die ausdrücklichen `make github-*`-Ziele committen
oder pushen.

Claude Code zeigt den Skill als `/storytold:craft`; Codex führt ihn als
`storytold:craft` in seiner Skill-Auswahl. Verwende eine native
MCP-Registrierung pro App. Die lokale Codex-Unterstützung ist eine ergänzende
Paketierungs-/Konfigurationsanpassung, **kein** entfernter ChatGPT-Connector.
Quellen zu Host-Paketierung und Installation sind im
[Quellenverzeichnis](docs/source-ledger.md) festgehalten.

## Craft App Suite

Der ArtCraft Launcher installiert die **Craft App Suite**: freie, quelloffene
Kreativwerkzeuge des [ArtCraft](https://getartcraft.com/)-Teams, jedes von Grund
auf in Rust geschrieben und jedes eigenständig nutzbar.

| | App | Wofür | Code | Mehr |
|:-:|---|---|---|---|
| <img src="https://raw.githubusercontent.com/storytold/photocraft/main/assets/app-icon/hicolor/64x64/apps/ai.storyteller.photocraft.png" alt="" width="32" height="32"> | **PhotoCraft** | Bildbearbeitung: Ebenen, Masken, Text und echte PSD-Dateien | [GitHub](https://github.com/storytold/photocraft) | [Website](https://getartcraft.com/apps/photocraft) |
| <img src="https://raw.githubusercontent.com/storytold/vectorcraft/main/assets/app-icon/hicolor/64x64/apps/ai.storyteller.vectorcraft.png" alt="" width="32" height="32"> | **VectorCraft** | Vektorillustration | [GitHub](https://github.com/storytold/vectorcraft) | [Website](https://getartcraft.com/apps/vectorcraft) |
| <img src="https://raw.githubusercontent.com/storytold/filmcraft/main/assets/app-icon/hicolor/64x64/apps/ai.storyteller.filmcraft.png" alt="" width="32" height="32"> | **FilmCraft** | Videoschnitt, Farbe und Ton | [GitHub](https://github.com/storytold/filmcraft) | [Website](https://getartcraft.com/apps/filmcraft) |
| <img src="https://raw.githubusercontent.com/storytold/lightcraft/main/assets/app-icon/hicolor/64x64/apps/ai.storyteller.lightcraft.png" alt="" width="32" height="32"> | **LightCraft** | Fotobibliothek und RAW-Entwicklung | [GitHub](https://github.com/storytold/lightcraft) | [Website](https://getartcraft.com/apps/lightcraft) |
| <img src="https://raw.githubusercontent.com/storytold/pdfcraft/main/assets/app-icon/hicolor/64x64/apps/ai.storyteller.pdfcraft.png" alt="" width="32" height="32"> | **PdfCraft** | PDFs lesen, ordnen und schützen | [GitHub](https://github.com/storytold/pdfcraft) | [Website](https://getartcraft.com/apps/pdfcraft) |
| <img src="https://raw.githubusercontent.com/storytold/effectcraft/main/assets/app-icon/hicolor/64x64/apps/ai.storyteller.effectcraft.png" alt="" width="32" height="32"> | **EffectCraft** | Motion Graphics und visuelle Effekte | [GitHub](https://github.com/storytold/effectcraft) | [Website](https://getartcraft.com/apps/effectcraft) |
| <img src="https://raw.githubusercontent.com/storytold/designcraft/main/assets/app-icon/hicolor/64x64/apps/ai.storyteller.designcraft.png" alt="" width="32" height="32"> | **DesignCraft** | Seitenlayout und Publishing | [GitHub](https://github.com/storytold/designcraft) | [Website](https://getartcraft.com/apps/designcraft) |
| <img src="https://raw.githubusercontent.com/storytold/gridcraft/main/assets/app-icon/hicolor/64x64/apps/ai.storyteller.gridcraft.png" alt="" width="32" height="32"> | **GridCraft** | Tabellenkalkulation und Daten | [GitHub](https://github.com/storytold/gridcraft) | [Website](https://getartcraft.com/apps/gridcraft) |
| <img src="https://raw.githubusercontent.com/storytold/wordcraft/main/assets/app-icon/hicolor/64x64/apps/ai.storyteller.wordcraft.png" alt="" width="32" height="32"> | **WordCraft** | Textverarbeitung und Dokumente | [GitHub](https://github.com/storytold/wordcraft) | [Website](https://getartcraft.com/apps/wordcraft) |
| <img src="https://raw.githubusercontent.com/storytold/deckcraft/main/assets/app-icon/hicolor/64x64/apps/ai.storyteller.deckcraft.png" alt="" width="32" height="32"> | **DeckCraft** | Präsentationen und Folien | [GitHub](https://github.com/storytold/deckcraft) | [Website](https://getartcraft.com/apps/deckcraft) |
| <img src="https://raw.githubusercontent.com/storytold/cadcraft/main/assets/app-icon/hicolor/64x64/apps/ai.storyteller.cadcraft.png" alt="" width="32" height="32"> | **CADCraft** | Computergestütztes Konstruieren (CAD) | [GitHub](https://github.com/storytold/cadcraft) | [Website](https://getartcraft.com/apps/cadcraft) |
| <img src="https://raw.githubusercontent.com/storytold/soundcraft/main/assets/app-icon/hicolor/64x64/apps/ai.storyteller.soundcraft.png" alt="" width="32" height="32"> | **SoundCraft** | Audioaufnahme und -bearbeitung | [GitHub](https://github.com/storytold/soundcraft) | [Website](https://getartcraft.com/apps/soundcraft) |
| <img src="https://raw.githubusercontent.com/storytold/figcraft/main/assets/app-icon/hicolor/64x64/apps/ai.storyteller.figcraft.png" alt="" width="32" height="32"> | **FigCraft** | Interface-Design und Prototyping | [GitHub](https://github.com/storytold/figcraft) | [Website](https://getartcraft.com/apps/figcraft) |

## Entwickeln ohne Netzwerkzugriff

Python **3.11+** führt die Kernwerkzeuge und Tests aus; GNU Make ist optionaler
Komfort. Für die Standard-Checks und den Build sind keine
Python-Abhängigkeiten von Dritten nötig.

```bash
make help
make doctor
make check
make test
make build
make verify-build
make package
make source
make clean
```

`make setup` legt nur eine lokale virtuelle Umgebung an. `make setup-probe` ist
ein ausdrückliches Netzwerk-Opt-in für `mcp==2.3.0`; danach prüft
`make test-sdk` das echte SDK gegen ein klar synthetisches stdio-Fixture. Die
dreizehn Craft-Apps werden dabei nicht ausgeführt. `make release` ordnet Checks,
Kerntests und reproduzierbare Paketierung; es behauptet keine native Abnahme
und veröffentlicht nichts. `make refresh-releases` und `make sign-releases`
sind die Netzwerkschritte des täglichen Workflows (der zweite braucht cosign);
`make setup-confined` installiert die sechs wurzelbeschränkten Apps auf diesem
Rechner. Das [Makefile](Makefile) listet alle Ziele.

## Native Apps einrichten (ein Befehl)

Der MCP-Server jeder App ist ihre CLI, `<app>-cli`. Weder die
Plugin-Installation noch die Desktop-App stellt sie bereit oder registriert
sie; bis dahin meldet der Skill zu Recht, dass die nativen Werkzeuge der App
nicht verbunden sind. Ein ausdrücklicher Befehl behebt das pro App oder für
alle dreizehn, auf macOS (universal), Linux x86_64 und Windows x64:

```bash
python3 storytold.py setup --app photocraft
```

```bash
python3 storytold.py setup --all --acknowledge-unconfined
```

Führe ihn aus einem Klon oder aus dem installierten Plugin-Verzeichnis aus,
das beide Hosts unter `<home>/plugins/cache/devsolux-storytold/storytold/<version>/`
in `~/.codex` bzw. `~/.claude` ablegen; `python3 storytold.py doctor` gibt für
jede fehlende App den genauen Befehl mit dem richtigen Pfad aus, und der
`craft`-Skill bietet ihn im Chat an, wenn ein Server nicht verbunden ist. Für
jede App lädt `setup` das für deine Plattform in
[`config/releases.json`](config/releases.json) gepinnte Archiv (die
macOS-CLI-Zip, den Linux-Tarball oder die portable Windows-Zip), prüft es gegen
dieses Manifest **und** die `SHA256SUMS.txt` des Releases, entnimmt genau die
eine `<app>-cli`, prüft die Herkunft, legt sie neben der aktiven Installation
bereit, führt Preflight und die Prüfung über das offizielle MCP-SDK
(initialize, tools/list, ein Nur-Lese-Aufruf) gegen diesen bereitgestellten
Kandidaten aus und befördert ihn erst dann (`~/.local/opt/craft/bin` bzw.
`%LOCALAPPDATA%\Storytold\craft\bin` unter Windows), pinnt den Binär-Hash in
einem privaten Lock und registriert den Server bei jeder Host-CLI im PATH
(`codex mcp add`, `claude mcp add --scope user`). Ein Kandidat, der an
irgendeinem Schritt scheitert, lässt die bisherige Binärdatei, ihren Pin und
die Registrierungen unberührt. Danach eine neue Sitzung starten. Ein erneutes `setup` ist idempotent: Eine
App, deren installierte Binärdatei zu ihrem Pin und zum Manifest passt, wird
übersprungen; eine bereits passende Registrierung bleibt bestehen. `--dry-run`
zeigt die Vorschau; `--list` zeigt Manifest-, Installations-, Pin- und
Registrierungsstand; `--upgrade` bringt eine App mit geändertem Pin auf das
Manifest-Release; `--replace` registriert einen gleichnamigen Server neu, der
woanders hinzeigt, und stellt den alten Eintrag wieder her, wenn der neue
nicht hinzugefügt werden kann; `--skip-probe` registriert, ohne die Binärdatei
auszuführen, und sagt das auch; `--remove` hebt nur die Benutzer-Registrierungen
auf, die `setup` selbst geschrieben hat (gleicher Befehl und gleiche
Argumente, App noch gepinnt), und löscht nur eine Binärdatei, deren Bytes zum
Lock passen; alles andere bleibt und wird gemeldet. `--remove --dry-run` zeigt
genau das als Vorschau, ohne etwas zu ändern. Ein Upgrade, das zwischen dem
Ersetzen der Datei und dem Neuschreiben des Locks unterbrochen wurde, bringt
der nächste Lauf in einen konsistenten Zustand. Nichts läuft, ohne dass du es aufrufst;
Python 3.11+ ist erforderlich.

**Herkunft.** Unter macOS muss die Binärdatei vom ArtCraft-Team bei Apple
notarisiert sein. Upstream signiert Linux- und Windows-Builds nicht, daher
signiert der [tägliche Workflow](.github/workflows/releases.yml) jede gepinnte
CLI schlüssellos mit [Sigstore cosign](https://docs.sigstore.dev/) unter seiner
eigenen GitHub-Identität und committet die Bundles nach
[`config/signatures.json`](config/signatures.json); unter Linux und Windows
verifiziert `setup` dieses Bundle vor der Installation mit
`cosign verify-blob` (cosign zuerst installieren), und macOS verifiziert es
ebenfalls, wenn cosign vorhanden ist. Solange ein Release kein Bundle hat oder
cosign fehlt, fährt `--trust-upstream-sums` allein auf Basis von Manifest und
`SHA256SUMS.txt` fort und vermerkt das im Lock.

**Tägliche Aktualisierung.** Der Workflow prüft jeden Tag das neueste Release
jeder App, schreibt das Manifest neu, signiert neue CLIs, baut das Plugin neu,
führt die Checks und das echte `setup` auf Linux-, Windows- und macOS-Runnern
aus und öffnet zur Prüfung einen Pull Request auf `bot/releases` (setze die
Repository-Variable `STORYTOLD_AUTO_MERGE=true`, um grüne Läufe automatisch zu
mergen). Nutzer erhalten die neuen Pins mit dem nächsten Plugin-Update.

PhotoCraft, VectorCraft, EffectCraft, WordCraft, SoundCraft und PdfCraft sind durch native
Wurzel-Flags auf den Workspace beschränkt und werden standardmäßig registriert.
Die anderen sieben können alles lesen und schreiben, was dein Benutzer darf, und
werden daher nur mit `--acknowledge-unconfined` installiert und registriert: Nutze sie für
unkritische Arbeit oder lass sie unter OS-Isolation laufen. Andere Plattformen,
abgeschottete Rechner und eigene Pins nutzen die manuelle Kette in
[Betrieb](docs/operations.md): herunterladen, Lock, `preflight`, `probe`,
`configure`, registrieren.

## Wo was liegt

Das Plugin-Verzeichnis enthält nur Code, Doku und das Release-Manifest; `setup`
hält alles, was es installiert, außerhalb davon, sodass ein Plugin-Update oder
eine Deinstallation nie eine CLI löschen, zurückstufen oder austauschen kann,
und eine installierte Kopie beiden Hosts dient. `python3 storytold.py setup
--list` gibt die verwendeten Pfade aus.

| Wo (macOS/Linux) | Windows | Was | Geschrieben von |
|---|---|---|---|
| `~/.codex/plugins/cache/devsolux-storytold/storytold/<version>/`, ebenso unter `~/.claude` | ebenso unter `%USERPROFILE%` | Das Plugin: `craft`-Skill, Doku, `storytold.py`, `config/releases.json`, `config/signatures.json`. Keine Binärdateien. | `codex plugin add` / `claude plugin install` |
| `~/.local/opt/craft/bin/` | `%LOCALAPPDATA%\Storytold\craft\bin\` | Die dreizehn Craft-CLIs (`photocraft-cli` … `figcraft-cli`, je 16–192 MB). Beide Hosts starten diese, z. B. `…/cadcraft-cli mcp`. | `setup` |
| `~/.local/state/storytold/` (`$XDG_STATE_HOME/storytold` unter Linux) | `%LOCALAPPDATA%\Storytold\state\` | Privater Zustand: `installations.lock.json` (gepinnte Hashes), `evidence/` (Prüfbelege je App), `venv/` (offizielles MCP-SDK für die Prüfung), `setup.json` (gemerkte Pfade). | `setup` |
| `~/craft-work-storytold/` | `%USERPROFILE%\craft-work-storytold\` | Der Workspace: `inputs/`, `outputs/` (Exporte landen hier), `receipts/`. Beschränkte Apps lesen `inputs` und schreiben nur `outputs`. | `setup` legt ihn an; die Apps füllen `outputs` |
| `~/.codex/config.toml` und `~/.claude.json` | ebenso | Eine MCP-Registrierung im Benutzerbereich je App und Host, die auf den absoluten CLI-Pfad oben zeigt. | `codex mcp add`, `claude mcp add --scope user`, ausgeführt von `setup` |

Die vollständigen Unix-Startvorlagen liegen unter `config/`. Sie sind nur
Beispiele, keine aktive Host-Konfiguration. Die echte Konfigurationserzeugung
wählt unter nativem Windows `.exe` und gibt konkrete, geprüfte Pfade aus, statt
darauf zu hoffen, dass Umgebungsvariablen auf allen Hosts gleich expandiert
werden. Rechnerspezifische Konfiguration bleibt aus Paketen heraus.

## Sicherer Kreativ-Workflow

**Prüfen → bereitgestellte Kopie → native Bearbeitung → Vorschau →
speichern/exportieren → erneut öffnen/verifizieren.**

Die [dreizehn App-Karten](skills/craft/SKILL.md) beschreiben besondere
Fallstricke: headless Auswahl in VectorCraft, Bibliothekssperren in LightCraft,
explizites Speichern in PdfCraft, UTF-8-Byte-Offsets in DesignCraft,
typisierte Formeln in GridCraft, Seiteneinheiten in FigCraft, Medien-Timing
und Offline-Warnungen. Das sind
aus den Quellen abgeleitete Hinweise; die verbundene Binärdatei liefert die
maßgebliche API.

Für app-übergreifende Arbeit übergib verifizierte Dateien – nicht die
In-Memory-IDs eines anderen Servers. PhotoCraft kann ein PNG für DesignCraft
exportieren; DesignCraft ein PDF für PdfCraft. Bleib beim letzten verifizierten
Artefakt stehen, wenn eine Stufe scheitert. Es gibt weder eine universelle
Batch-Transaktion noch automatische Schreibwiederholung noch einen versteckten
Ausweichpfad.

Fünf Apps haben in den Quellen dokumentierte getrennte Lese-/Schreibwurzeln;
PdfCraft hat eine Wurzel; sieben Apps sind als OS-benutzerweit zu behandeln.
Weder der Skill noch Prüfbelege noch die MCP-Konfiguration sind eine
OS-Sandbox. Auch andere Shell-/Datei-Werkzeuge des Hosts brauchen passende
Berechtigungen. Siehe [Sicherheit](SECURITY.md).

## Repository-Übersicht

| Pfad | Zuständigkeit |
|---|---|
| `skills/craft/` | Ein anleitender Skill, dreizehn App-Karten und zwei Workflows |
| `config/` | Geprüfter Startkatalog, Release-Manifest und Sigstore-Bundle-Speicher, inaktive Vorlagen, Beispiel-Lock/-Env |
| `storytold_tools/`, `storytold.py` | Deterministische CLI und optionale kurzlebige SDK-Prüfung |
| `scripts/`, `Makefile` | Offline-Checks, Tests, abgesicherte Builds und Paketierung |
| `tests/` | Kern-Regressionstests, synthetisches SDK-Fixture, native Abnahmeszenarien |
| `docs/` | Architektur, Betrieb, Sicherheitsgrenzen, Quellen und Verifikation |
| `plugins/storytold/` | Generierte gemeinsame Laufzeit; niemals eigenständig bearbeiten |
| `.github/workflows/` | Offline-CI-Matrix sowie tägliche Release-Aktualisierung, Signierung und Verifikation auf drei Betriebssystemen |

[Architektur](docs/architecture.md) hält fest, warum der native Plan Vorrang vor
der älteren Gateway-Referenz hat und welche Komponente wofür zuständig ist.

Devsolux-Integration; es wird keine Zugehörigkeit zur oder Billigung durch die
Upstream-Organisation `storytold`, Anthropic oder OpenAI behauptet.
Veröffentlicht unter der [MIT-Lizenz](LICENSE). Native Apps, SDKs, Schriften
und Medien werden nicht mitgeliefert und behalten ihre eigenen Lizenzen; siehe
den [Lizenzhinweis](LICENSE-NOTICE.md).
