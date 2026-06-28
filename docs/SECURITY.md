# Sicherheitsmodell

Sagent behandelt Sicherheit als Kernfunktion. Modellantworten, Repository-Inhalte, Memory und UI-Eingaben gelten immer als potenziell fehlerhaft oder bösartig.

## Unverhandelbare Regeln

1. **Workspace-Grenze:** Tools dürfen nur innerhalb eines explizit gewählten und kanonisch aufgelösten Workspace arbeiten.
2. **Read-only by default:** Neue Tools haben zunächst ausschließlich Leserechte.
3. **Explizites Approval:** Schreiben, Löschen, Umbenennen, Prozessstart und Netzwerkzugriff benötigen eine konkrete Freigabe.
4. **Proposal-Bindung:** Eine Freigabe gilt nur für den angezeigten Proposal-Hash, nicht für ähnliche oder später veränderte Aktionen.
5. **Keine freie Shell:** Kommandos werden als Argumentlisten aus einer Allowlist gestartet, nie über `shell=True` oder interpolierte Shell-Strings.
6. **Pfadvalidierung:** Absolute Pfade, Traversal und Symlink-Ausbrüche werden abgewiesen.
7. **Minimale Daten:** Secrets, `.env`-Inhalte, Schlüssel und bekannte Credential-Pfade werden weder gelesen noch geloggt.
8. **Ressourcenlimits:** Datei-, Output-, Prozesszeit- und Speicherlimits verhindern unkontrollierte Arbeit.
9. **Kein Netzwerk per Default:** Netzwerkzugriff ist in Tools standardmäßig deaktiviert.
10. **Auditierbarkeit:** Tool-Anfrage, Policy-Entscheidung, Approval und Ergebnis werden lokal und redigiert protokolliert.

## Approval-Stufen

- **Stufe 0 – Lesen:** Erlaubte Textdateien innerhalb des Workspace; bekannte sensible Pfade bleiben gesperrt.
- **Stufe 1 – Vorschlagen:** Pläne und Patches in einem isolierten Bereich erzeugen; keine Workspace-Mutation.
- **Stufe 2 – Ändern:** Exakt angezeigten Patch nach expliziter Freigabe anwenden.
- **Stufe 3 – Ausführen:** Einen angezeigten, allowlist-basierten Befehl mit Limits starten.
- **Stufe 4 – Extern:** Netzwerk, Git-Push, Paketveröffentlichung oder andere externe Effekte; separate, besonders deutliche Freigabe.

## Sandbox-Anforderungen

- Kanonischer Workspace-Root wird beim Sitzungsstart fixiert.
- Schreiboperationen laufen zunächst gegen eine temporäre Kopie oder einen Git-Worktree.
- Tools erhalten nur die benötigten Verzeichnisse und Umgebungsvariablen.
- Prozesse laufen mit festem Arbeitsverzeichnis, bereinigter Umgebung und Timeout.
- Änderungen werden vor Übernahme erneut gegen den freigegebenen Hash geprüft.

## Prompt Injection

Text in Projekten kann Anweisungen enthalten. Diese Inhalte sind Daten, keine Systemanweisungen. Sie dürfen keine Policies ändern, Tools freigeben, Secrets anfordern oder den Workspace erweitern. Herkunft und Rolle jedes Kontextblocks müssen erhalten bleiben.

## Secret Handling

- `.env` wird nie committed.
- Logs redigieren Tokens, Schlüssel und verdächtige Werte.
- Secrets werden nicht in Prompts, Memory oder Diffs übernommen.
- Spätere Integrationen nutzen macOS Keychain oder kurzlebige Prozessvariablen.

## Sicherheitsmeldung

Bis ein privater Meldeweg dokumentiert ist, keine sensiblen Schwachstellendetails in öffentliche Issues schreiben. Das Projekt ist noch nicht für untrusted Multi-User-Betrieb freigegeben.
