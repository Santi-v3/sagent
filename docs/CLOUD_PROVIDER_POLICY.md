# Policy für optionale Cloud-Modellprovider

## Status und Zweck

Dieses Dokument definiert ausschließlich Sicherheits- und Architekturgrenzen für eine
spätere optionale Cloud-Modellintegration. Es implementiert keinen Provider, erlaubt
kein `remote_http`, enthält keinen Endpoint und startet keinen Netzwerk- oder
Modellaufruf.

Sagent bleibt **local-first**. Der deterministische In-Process-Fake und die ausdrücklich
konfigurierten Loopback-Provider bleiben die einzigen heute verfügbaren Modellpfade.
Eine spätere DeepSeek-Cloud-Integration ist eine optionale Produktidee für große
Coding- und Reasoning-Aufgaben, kein Bestandteil des aktuellen Runtime-Vertrags.

## Verbindliche Provider-Trennung

Lokale und entfernte Provider gehören in getrennte Vertrauens- und Transportklassen:

| Klasse | Beispiele | Transport | Standard |
| --- | --- | --- | --- |
| In Process | deterministischer Fake | `in_process` | erlaubt |
| Lokal | Ollama, LM Studio | `loopback_http` | deaktiviert, explizites lokales Opt-in |
| Cloud | später optional DeepSeek Cloud | `remote_http` | vollständig deaktiviert |

- Ollama bleibt ausschließlich an `127.0.0.1:11434` gebunden.
- LM Studio bleibt ausschließlich an `127.0.0.1:1234` gebunden.
- DeepSeek Cloud darf niemals als Ollama-Modell, lokales Profil oder Loopback-Adapter
  registriert werden.
- Provider-ID, Transportklasse und Datenfreigabe müssen vor Routing feststehen. Eine
  Modell-ID oder Nutzereingabe darf die Transportklasse nicht verändern.
- Es gibt keinen automatischen Fallback von lokal zu Cloud. Fehler, Timeout,
  Überlastung oder zu kleiner lokaler Kontext führen zu einem sichtbaren Stopp, nicht
  zu einer stillen Datenübertragung.

## Aktivierungs- und Freigabemodell

Ein späterer Cloud-Lauf benötigt mindestens zwei voneinander unabhängige Gates:

1. **Lokale Umgebungs-/Prozesskonfiguration:** Der konkrete Cloud-Provider ist im
   lokalen Prozess ausdrücklich aktiviert; ohne diese Konfiguration wird kein
   Remote-Adapter registriert.
2. **Laufgebundene Nutzerfreigabe:** Der Nutzer bestätigt exakt einen angezeigten Lauf
   mit gebundenem Provider, Modell, Datenmanifest und Zweck.

Eine dauerhafte Provideraktivierung ersetzt niemals die Freigabe pro Lauf. Eine
Freigabe gilt nicht für Wiederholungen, Fallbacks, andere Modelle, zusätzliche Dateien
oder veränderte Diffs. Hintergrundjobs, automatische Retries und zeitgesteuerte
Cloud-Aufrufe bleiben ohne eine weitere Architekturentscheidung verboten.

Vor jeder späteren Cloud-Nutzung muss Sagent anzeigen:

- Provider-ID und sichtbares Providerlabel,
- exakte Modell-ID,
- Zweck und Aufgabenklasse,
- welche Datenfelder und Inhalte übertragen werden,
- ob Repository-Kontext enthalten ist,
- ob Diffs enthalten sind,
- welche Dateien oder Ausschnitte enthalten sind,
- ob und wie Inhalte redigiert wurden,
- Byte-/Größenbudget der Übertragung,
- dass Cloud-Verarbeitung externe Datenverarbeitung bedeutet,
- ob der Nutzer genau dieses Manifest ausdrücklich bestätigt hat.

Ändert sich ein Eintrag, verfällt die Freigabe. Der lokale Approval-Core, nicht das
Cloud-Modell und nicht allein die UI, entscheidet über die Gültigkeit.

## Aufgabenklassifikation

### Lokal beziehungsweise Ollama

Diese Aufgaben bleiben standardmäßig lokal:

- kleine Aufgaben und kurze Hilfsfragen,
- private Notizen,
- lokale Dateien,
- sensible Repository-Diffs,
- Aufgaben mit persönlichen Daten,
- Aufgaben, die Secrets oder Zugangsdaten berühren könnten.

Diese Klassifikation erteilt keine Lesefreigabe für Secrets. Bestehende Regeln für
`.env`, Schlüssel, Tokens und Credential-Pfade bleiben auch lokal verbindlich.

### DeepSeek Cloud später optional

Nach Implementierung aller Gates kann DeepSeek Cloud für folgende, zuvor bereinigte
Aufgaben angeboten werden:

- große Architekturplanung,
- komplexes Refactoring,
- große Coding-Aufgaben,
- lange Debugging-Analysen,
- allgemeine Programmierfragen ohne private oder vertrauliche Daten.

Die Größe oder Schwierigkeit einer Aufgabe autorisiert Cloud-Nutzung nicht. Sagent darf
nur eine Option anbieten; Providerwahl und Freigabe bleiben beim Nutzer.

### Cloud-Datenverbote und Sonderfreigaben

Folgende Inhalte dürfen niemals an einen Cloud-Provider gesendet werden:

- `.env`-Inhalte,
- API-Keys,
- Tokens, Passwörter und Session-Cookies,
- private Schlüssel und andere Credentials.

Folgende Inhalte bleiben standardmäßig ebenfalls ausgeschlossen und benötigen, falls
eine spätere Produktentscheidung sie überhaupt zulässt, eine zusätzliche eng
begrenzte Datenfreigabe und vorherige Redaction:

- private Dateien,
- vollständige Repository-Dumps,
- persönliche Daten,
- Kundendaten,
- sensible Universitäts-, Schul- oder Arbeitsdokumente.

Eine allgemeine Cloud-Zustimmung, eine Provideraktivierung oder eine Coding-Freigabe
reicht für diese Daten nicht aus. Unklare Klassifikation wird als verboten behandelt.

## Datenminimierung und Persistenz

- Es wird nur der kleinste für die bestätigte Aufgabe notwendige Ausschnitt übertragen.
- Repository-Kontext wird allowlist-basiert ausgewählt; rekursive Voll-Uploads sind
  verboten.
- Sensible Pfade und bekannte Secret-Muster werden vor Anzeige des Manifests und erneut
  unmittelbar vor dem Versand blockiert oder redigiert.
- Quelllabels wie `user`, `workspace`, `memory` und `tool_result` bleiben erhalten.
- Prompt- und vollständige Modellantworttexte werden standardmäßig weder in Logs,
  Jobs, Benchmark-Berichten, Memory noch Telemetrie persistiert.
- Zulässige Auditdaten sind begrenzte Metadaten wie Provider-ID, Modell-ID,
  Aufgabenklasse, Freigabe-ID, Zeit, Byteanzahl, Redaction-Status, Terminalstatus und
  generische Fehlerklasse.
- Eine spätere Textpersistenz benötigt eine eigene Datenschutzentscheidung, sichtbare
  Aufbewahrungsfrist, Löschweg und separate Nutzerfreigabe.

Sagent kann keine Aussagen über Aufbewahrung beim externen Provider machen, solange
dessen Bedingungen und technische Optionen nicht separat geprüft und dem Nutzer vor
Freigabe angezeigt wurden.

## Secret-Vertrag

- API-Keys werden niemals committed, in Beispieldateien mit echten Werten gezeigt,
  geloggt, in Prompts eingebettet oder an die Weboberfläche zurückgegeben.
- Eine spätere Implementierung darf Secrets nur aus kurzlebigen lokalen
  Prozessvariablen oder einer gesondert geprüften Secret-Verwaltung beziehen.
- Providerkonfiguration und Secretmaterial bleiben getrennt. Metadaten- und
  Discovery-Endpunkte dürfen niemals das Secret offenlegen.
- Fehlendes oder ungültiges Secret führt zu einem sicheren Stopp. Es gibt keinen
  Fallback auf einen anderen Provider und keine interaktive Speicherung im Repository.

## Coding-Agent-Regel

Ein späteres DeepSeek-Cloud-Modell darf analysieren und Vorschläge erzeugen, aber keine
Aktion autorisieren oder direkt ausführen.

- Cloud-Antworten bleiben technisch und semantisch `untrusted=true`.
- Der Adapter erhält keine Tool-Definitionen und keine Datei-, Shell-, Git-, Netzwerk-
  oder Approval-Schnittstelle.
- Das Modell darf nicht autonom schreiben, löschen, stagen, committen, pushen oder
  mergen.
- Modelltext darf keine lokale Policy ändern und keine Freigabe darstellen.
- Vorschläge werden lokal validiert und durchlaufen weiterhin ChangeProposal,
  sichtbaren Diff, Tests und Sagents inhaltsgebundenen Approval-Flow.
- Tool-Aktionen werden ausschließlich vom lokalen deterministischen Core anhand einer
  separaten menschlichen Freigabe ausgelöst.

## DeepSeek-spezifische spätere Zielarchitektur

Die folgende Form ist nur ein Architekturziel, keine aktuelle Konfiguration:

- vorgeschlagene Provider-ID: `deepseek-cloud`,
- Zweck: große Coding- und Reasoning-Aufgaben ohne private Daten,
- Transportklasse: `remote_http`, strikt getrennt von `loopback_http`,
- Default: `disabled`,
- Registrierung nur bei expliziter lokaler Prozesskonfiguration,
- Ausführung nur mit zusätzlicher laufgebundener Runtime-Freigabe,
- feste serverseitige Provider- und Modell-Allowlist statt nutzerdefinierter URL,
- Secretbezug ausschließlich über lokale Prozessumgebung oder spätere sichere
  Secret-Verwaltung,
- keine API-Route, kein Endpoint und kein Modellname werden durch dieses Konzept
  implementiert oder endgültig festgelegt.

Eine spätere Umsetzung benötigt ein eigenes kleines Inkrement mit Threat Model,
Providervertragsprüfung, Datenschutzprüfung und negativen Sicherheitstests.

### Deaktivierter Konfigurationsvertrag

Der Core darf bereits vor einer Runtime-Integration unveränderliche, nicht
ausführbare Cloud-Konfigurationsmetadaten typisieren. Dieser Vertrag bleibt stets
deaktiviert, kennt keinen Endpoint und liest weder Secret- noch Umgebungswerte.
`remote_http` ist darin nur die getrennte Transportklassifikation, keine Allowlist-
oder Runtime-Freigabe. Eine solche Konfiguration darf keinen Provider bauen,
`cloud_providers_enabled` nicht setzen und die erlaubten Router-Transporte nicht
erweitern.

## Anforderungen an einen späteren Remote-HTTP-Transport

`remote_http` darf erst freigegeben werden, wenn mindestens folgende Grenzen technisch
erzwungen und offline testbar sind:

- fester Provider-spezifischer HTTPS-Ursprung; keine URL aus Request oder Modelltext,
- keine Redirects und kein Wechsel von Host, Schema, Port oder Pfad,
- Schutz vor DNS-/IP-Ausbruch und Zugriff auf Loopback, private Netze, Link-Local,
  Metadatenservices und andere interne Ziele,
- `trust_env=false`, keine geerbten Proxies, Cookies oder Ambient Credentials,
- Authorization nur im Transport aus dem lokalen Secret; niemals im Requestmodell,
- feste Requestfelder sowie Byte-, Token-, Zeit-, Parallelitäts- und Kostenlimits,
- begrenzte, aktiv abbrechbare Jobs ohne automatische Wiederholung,
- generische Fehler nach außen; keine Providerantworten, Header oder Secrets in Logs,
- Response-Validierung, Größenlimit, Modellidentitätsprüfung und blockierte Tool-Calls,
- vollständige Offline-Tests mit Mock-Transport vor jedem echten Verbindungstest.

## Bewusst nicht Teil dieses Inkrements

- keine DeepSeek- oder andere Cloud-Adapterimplementierung,
- keine Freigabe von `remote_http`,
- keine API- oder UI-Route,
- keine Endpoint- oder Modellentscheidung,
- keine API-Keys, Secretdateien oder `.env`-Änderung,
- keine Cloud-Verbindung, Providerprüfung oder Modellanfrage,
- kein Benchmark, Fallback, Download, Paketinstallation oder OpenCode-Start.
