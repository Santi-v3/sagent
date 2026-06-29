# Web App

Lokale Next.js-Oberfläche für die erste technische Minimalversion von Sagent.

Sie sendet Aufgaben an die lokale Agent-API, zeigt Plan, Risiken und Änderungsvorschlag und ermöglicht Freigeben, Ablehnen oder Überarbeitung anfordern. Nach einer Freigabe kann der Nutzer ein sichtbares Allowlist-Testprofil starten, begrenzte Logs prüfen sowie lokalen Branch, Worktree-Status und redigierten Diff sehen. Die Oberfläche kann einen lokalen Feature-Branch nach enger Namensregel anlegen, bietet aber bewusst keinen Commit, Push oder Merge an. Verbindungsfehler und Retry werden sichtbar behandelt. Es gibt keine Authentifizierung, Modellwahl oder LLM-Anbindung.

## Start

Vom Repository-Root:

```bash
pnpm --filter @sagent/web dev
```

Danach läuft die Oberfläche unter `http://127.0.0.1:3000`.
