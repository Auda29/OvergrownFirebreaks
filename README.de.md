# Overgrown Firebreaks

Dieses unabhängige NeoForge-Addon verbindet Burnt Basic mit Overgrown Vegetation
von yayuy_0227. Es funktioniert ohne TerraVista und ohne Paxi.

Downloads gibt es unter
[GitHub Releases](https://github.com/Auda29/OvergrownFirebreaks/releases).

## Installieren

Vorausgesetzt werden Minecraft 1.21.1, Java 21, NeoForge aus der 21.1-Reihe ab
21.1.150, Burnt 1.10.5.2 und Overgrown 0.1.2. Getestet wird NeoForge 21.1.248.
Die Originalmods und ihre Bibliotheken müssen separat installiert werden.
Geprüft sind Cloth Config 15.0.140, GeckoLib 4.9.3 und Player Animation Library
von ZigytheBird 1.1.6.

Die Hauptdatei `overgrown-firebreaks-0.1.0-alpha.1-neoforge-1.21.1.jar` gehört
in den Ordner `mods`. Sie ergänzt Brennregeln für 45 Overgrown-Blöcke.
32 Blöcke werden in Burnt-Reste umgewandelt, 13 Ranken oder Leichen entfernt.

Für geschützte Brandflächen zusätzlich
`overgrown-firebreaks-protection-0.1.0-alpha.1-neoforge-1.21.1.jar` installieren.
Diese zweite JAR schützt 336 Burnt-Blöcke vor Overgrowns Blockinfektion.
Zum Abschalten nur diese zweite JAR entfernen und das Spiel neu starten.
Für den unterstützten Mehrspielerbetrieb auf Server und Clients dieselben
Addon-Module verwenden.

Das Installations-ZIP enthält die Haupt-JAR und das Schutzmodul im Unterordner
`optional`. Zuerst entpacken, dann die gewünschten JARs nach `mods` kopieren.
Die Originalmods sind nicht enthalten. Der Quellcode liegt in einem separaten ZIP.

## Grenzen des Schutzes

Auch verkohlte Baumaterialien werden geschützt. Das verändert die Balance.
Wer nur Brennkompatibilität möchte, installiert ausschließlich die Hauptdatei.
Gewöhnliches Gras bleibt infizierbar, auch nach der Regeneration einer Brandfläche.
Sporen, Biominfektion, Gegner und Weltphasen ändern sich nicht. Hive Node und
Overgrown Nexus behalten ihre Feuerimmunität.

Die Alpha erlaubt genau die oben genannten Versionen der beiden Originalmods.
Bei Updates müssen Blocknamen und Verhalten erneut geprüft werden.
Ein bekanntes Problem der ursprünglichen Overgrown-Schwimanimation erscheint
beim Clientstart im Log, verhindert den geprüften Start aber nicht.
Vier ursprüngliche Schmelz- und Hochofenrezepte für Chlorophyllite und Sap Crystal
laden wegen eines Formatfehlers nicht. Dieses Addon verändert diese Rezepte nicht.
Die geprüften Brenn- und Schutzregeln sind davon unabhängig.

## Bauen und weitergeben

Mit Python 3.11 oder neuer `python build.py` ausführen. Im Ordner `dist` liegen
beide reproduzierbaren JARs, der Quellcode als ZIP und SHA-256-Prüfsummen.
Unser Quellcode und unsere Regeln stehen unter MIT. Fremde Moddateien, Grafiken,
Modelle, Animationen und Sounds sind nicht enthalten.

Die englische `README.md` enthält die vollständigen Versions- und Testhinweise.
Der weitergebbare Prüfbericht steht in `VALIDATION.md`.
GitHub Actions baut und prüft die Pakete für Windows und Linux.
Der lokale Build lädt selbst keine Dateien hoch.
