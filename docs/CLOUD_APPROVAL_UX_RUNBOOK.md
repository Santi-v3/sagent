# Cloud-Approval-UX-Runbook

## Zweck und aktueller Stand

Dieses Runbook spezifiziert einen möglichen späteren UX-Ablauf für genau einen
Cloud-Modelllauf. Es ist ausschließlich Dokumentation und erteilt keine Runtime-,
Netzwerk- oder Datenfreigabe.

Der aktuelle Stand bleibt **Preview only**:

- Die Web-UI zeigt read-only Metadaten aus der lokalen Agent-API oder aus ihrem
  versionierten statischen Fallback.
- `Cloud execution` bleibt `No`.
- Die Preview akzeptiert nur einen denied Zustand ohne Ausführungswirkung.
- Der Cloud-Provider-Guard blockiert `remote_http` weiterhin.
- Es gibt keinen Cloud-Adapter, keinen konfigurierten Cloud-Endpoint, keinen
  Cloud-Startbutton und keine Modellwahl.

Die verbindliche Grundlage bleibt die
[Cloud-Provider-Policy](CLOUD_PROVIDER_POLICY.md). Dieses Runbook beschreibt nur, was
vor einer späteren Implementierung sichtbar und technisch erzwungen werden müsste.

## Späterer Zielzustand

Eine spätere Cloud-Nutzung darf ausschließlich als explizit bestätigte
`one_run_only`-Freigabe möglich werden. Sie muss an den exakt angezeigten Provider,
das serverseitig konfigurierte Modell, den Zweck und das vollständige Datenmanifest
gebunden sein. Jede Änderung und jeder weitere Lauf benötigen eine neue Preview und
eine neue Bestätigung.

Eine gültige Freigabe darf weder einen Provider registrieren noch einen Transport
freischalten. Lokale Prozesskonfiguration, Provider-Allowlist, Cloud-Guard und
laufgebundene Nutzerfreigabe bleiben voneinander unabhängige Gates. Bis diese Gates
in einem separaten Security-Inkrement implementiert und geprüft sind, bleibt jede
Cloud-Ausführung blockiert.

Das deaktivierte `CloudProviderConfig`-Schema kann dafür ausschließlich read-only
Statusmetadaten liefern. Es liest keine Secrets oder Umgebungswerte und darf weder
einen Provider erzeugen noch Router-Gates oder Transport-Policies verändern.
Die lokale UI darf diese disabled/not_configured Metadaten read-only anzeigen; eine
API-Abweichung muss zur statischen disabled Vorschau führen und darf keine Aktion
freischalten.

## Pflichtanzeigen vor jedem späteren Lauf

Vor einer Bestätigung muss die UI mindestens folgende Informationen vollständig und
unveränderlich anzeigen:

- Provider-ID und sichtbare Einordnung als Cloud-Provider,
- Modellname, falls er später serverseitig konfiguriert wurde,
- Zweck des Laufs,
- Scope `one_run_only`,
- genaue Kategorien und den geschätzten Umfang der Daten, die gesendet würden,
- `repo_context_included`,
- `diffs_included`,
- `files_included`,
- Redaction-Status,
- `secrets_excluded`,
- `full_repo_dump forbidden`,
- Cloud-Ausführungsstatus,
- alle Risk Hints.

Die Anzeige muss klar zwischen Metadaten und tatsächlichen Inhalten unterscheiden.
Sie darf keine Secrets, Tokens oder Zugangsdaten darstellen. Falls später einzelne
Dateien oder Ausschnitte erlaubt werden, braucht deren exakte Auswahl einen eigenen,
inhaltlich gebundenen Datenschutz- und Redaction-Vertrag.

## Pflicht-Blocker

Die Preview und jede spätere Ausführung müssen sicher stoppen, wenn mindestens einer
dieser Fälle vorliegt:

- `secrets_excluded=false`,
- ein vollständiger Repository-Dump ist enthalten oder erlaubt,
- `explicit_confirmed` fehlt oder ist nicht wahr,
- der Scope ist nicht exakt `one_run_only`,
- die Provider-ID ist unbekannt,
- ein lokaler Provider wird als Cloud-Provider ausgegeben,
- Payload oder Manifest enthalten API-Keys, Secrets oder Tokens,
- Prompt- oder vollständige Antworttexte würden ohne eine spätere separate
  Persistenz-, Aufbewahrungs- und Löschfreigabe gespeichert.

Ein Blocker darf nicht durch UI-Zustand, Modelltext, Wiederholung, Fallback oder eine
allgemeine Provideraktivierung übergangen werden. Unsicherheit wird als Ablehnung
behandelt.

## Vorgesehene Nutzeraktion

Ein späterer sicherer Flow besteht aus genau diesen Schritten:

1. Die lokale Agent-API erzeugt eine read-only Preview ohne Cloud-Kontakt.
2. Der Nutzer prüft Provider, Modell, Zweck, Scope, Datenumfang, Redaction und Risiken.
3. Der Nutzer bestätigt bewusst exakt diese Preview für genau einen Lauf.
4. Der lokale Core prüft unmittelbar vor der Ausführung erneut alle Gates und die
   Bindung an das unveränderte Manifest.
5. Nach Erfolg, Fehler, Abbruch oder Timeout verfällt die Freigabe. Retry,
   Wiederholung, anderes Modell oder veränderte Daten benötigen eine neue Preview und
   Bestätigung.

Die UI allein darf keine Freigabe erzeugen. Eine spätere Bestätigung muss
serverseitig an den unveränderten Approval-Request gebunden sein.

## Weiterhin verboten

Auch nach einer späteren Umsetzung bleiben verboten:

- automatischer Local-to-Cloud-Fallback,
- Cloud-Start ohne sichtbare, laufgebundene Nutzerbestätigung,
- vollständige Repository-Dumps,
- Übertragung oder Anzeige von Secrets,
- Eingabe oder Speicherung von API-Keys in der Web-UI,
- Tool-Autorität für Modellantworten,
- direkte Shell-, Git-, Datei- oder Netzwerkaktionen aus Cloud-Antworten,
- automatische Retries, Hintergrundläufe oder dauerhafte Freigaben,
- Persistenz vollständiger Prompts oder Antworten ohne separate spätere Freigabe.

Cloud-Antworten bleiben `untrusted=true`. Coding-Vorschläge müssen weiterhin lokal
validiert werden und den bestehenden Diff-, Test- und Approval-Flow durchlaufen.

## Abbruch- und Fehlerfälle

| Fall | Sicheres Verhalten |
| --- | --- |
| Lokale Agent-API nicht erreichbar | Statische denied Preview anzeigen; keine Bestätigung oder Ausführung anbieten. |
| Preview-Response weicht vom denied Vertrag ab | Response verwerfen und auf die statische denied Preview zurückfallen. |
| Secrets erkannt | Preview und Lauf blockieren; keine sensiblen Treffer anzeigen oder speichern. |
| Provider unbekannt oder falsch klassifiziert | Vor Freigabe stoppen; keinen alternativen Provider wählen. |
| Cloud-Guard blockiert `remote_http` | Sichtbar beendet lassen; keine Umgehung, Reparatur oder automatische Freigabe versuchen. |

Fehler führen nie zu einem Providerwechsel, Retry oder erweitertem Datenumfang. Die
Fehlermeldung bleibt generisch und darf keine Secrets, Providerinternas oder
vollständigen Eingabe- beziehungsweise Antworttexte enthalten.

## Testanforderungen vor einer späteren Implementierung

Eine spätere Implementierung benötigt mindestens:

- Unit Tests für unveränderliche Requests, Manifestbindung, Ablauf und alle Blocker,
- API-Tests für denied Defaults, exakte `one_run_only`-Bestätigung und sichere Fehler,
- UI-Sicherheitschecks für Pflichtanzeigen, fehlende Secret-/Endpoint-Felder und
  fehlende automatische Aktionen,
- Secret-Scans für Request, Logs, Jobs, Persistenz und sichtbare Fehlermeldungen,
- explizite Tests, dass `remote_http` ohne gültige laufgebundene Freigabe blockiert
  bleibt,
- Tests für verbotene lokale Provideridentitäten und unbekannte Provider,
- Tests für fehlenden Local-to-Cloud-Fallback und verfallene Freigaben,
- Tests, dass Modellantworten keine Tool-Autorität erhalten.

Alle Tests müssen offline und deterministisch laufen. Sie dürfen keinen Provider
kontaktieren, keinen Modellaufruf ausführen und keinen externen Netzwerkzugriff
benötigen. Ein erster echter Cloud-Kontakt wäre ein eigenes, später ausdrücklich zu
bestätigendes Inkrement nach abgeschlossenem Security-, Datenschutz- und
Providervertragsreview.
