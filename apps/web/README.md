# Web App

Lokale Next.js-Oberfläche für die erste technische Minimalversion von Sagent.

Sie sendet Aufgaben an die lokale Agent-API, zeigt die strukturierte Platzhalterantwort und behandelt Verbindungsfehler. Es gibt keine Authentifizierung, Modellwahl oder produktiven Agent-Tools.

## Start

Vom Repository-Root:

```bash
pnpm --filter @sagent/web dev
```

Danach läuft die Oberfläche unter `http://127.0.0.1:3000`.
