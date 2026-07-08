const { app, BrowserWindow, Menu, globalShortcut } = require("electron");
const { spawn } = require("child_process");
const http = require("http");
const net = require("net");
const path = require("path");
const fs = require("fs");
const os = require("os");

const DEV = !app.isPackaged;
let WEB_PORT = 3000;
const API_PORT = 8765;
const STATE_PATH = path.join(os.homedir(), ".sagent", "window-state.json");

let mainWindow = null;
let splashWindow = null;
let backendProcess = null;
let frontendServer = null;
let booting = false;

const MIME_TYPES = {
  ".html": "text/html",
  ".js":  "application/javascript",
  ".css": "text/css",
  ".svg": "image/svg+xml",
  ".png": "image/png",
  ".json": "application/json",
  ".txt": "text/plain",
  ".ico": "image/x-icon",
};

const isWin = process.platform === "win32";
const isMac = process.platform === "darwin";

const COMMON_PATHS = isWin ? [
  `${os.homedir()}\\AppData\\Local\\Programs\\Python\\Python313`,
  `${os.homedir()}\\AppData\\Local\\Programs\\Python\\Python312`,
] : [
  "/opt/homebrew/bin",
  "/usr/local/bin",
  `${os.homedir()}/.local/bin`,
  `${os.homedir()}/.cargo/bin`,
];

function splashHtml(status, detail) {
  const detailLine = detail ? `<div class="detail">${detail}</div>` : "";
  return `<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Sagent</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#f7f7f5;display:flex;align-items:center;justify-content:center;height:100vh;font-family:-apple-system,BlinkMacSystemFont,sans-serif;color:#333;padding:20px}
.wrap{text-align:center;max-width:300px}
.logo{font-size:36px;font-weight:600;letter-spacing:-1px;margin-bottom:6px}
.sub{font-size:14px;color:#888}
.detail{font-size:11px;color:#bbb;margin-top:8px;word-break:break-all;max-height:60px;overflow-y:auto}
.spinner{width:22px;height:22px;border:3px solid #ddd;border-top-color:#333;border-radius:50%;animation:spin .8s linear infinite;margin:20px auto 0}
.error .logo{color:#c00}
.error .sub{color:#666}
.error .spinner{display:none}
@keyframes spin{to{transform:rotate(360deg)}}
</style></head>
<body><div class="wrap${detail && detail.includes('Fehler') ? ' error' : ''}">
<div class="logo">Sagent</div>
<div class="sub">${status}</div>
${detailLine}
<div class="spinner"></div>
</div></body></html>`;
}

function updateSplash(status, detail) {
  if (splashWindow && !splashWindow.isDestroyed()) {
    splashWindow.loadURL(`data:text/html,${encodeURIComponent(splashHtml(status, detail))}`);
  }
}

function showSplash(status = "wird gestartet...") {
  if (splashWindow && !splashWindow.isDestroyed()) { updateSplash(status); return; }
  splashWindow = new BrowserWindow({
    width: 320, height: 260, frame: false, resizable: false,
    show: false, center: true,
    webPreferences: { nodeIntegration: false, contextIsolation: true },
  });
  splashWindow.loadURL(`data:text/html,${encodeURIComponent(splashHtml(status))}`);
  splashWindow.once("ready-to-show", () => splashWindow.show());
}

function closeSplash() {
  if (splashWindow && !splashWindow.isDestroyed()) {
    splashWindow.close();
    splashWindow = null;
  }
}

function findUv() {
  const uvName = isWin ? "uv.exe" : "uv";
  for (const dir of COMMON_PATHS) {
    const p = path.join(dir, uvName);
    if (fs.existsSync(p)) return p;
  }
  return "uv";
}

function augmentPath() {
  return [...COMMON_PATHS, process.env.PATH || ""].join(path.delimiter);
}

function packagesDir() {
  return DEV ? path.resolve(__dirname, "../../packages") : path.resolve(__dirname, "../packages");
}

function startBackend() {
  const apiDir = path.resolve(__dirname, DEV ? "../../apps/agent-api" : "../agent-api");
  const pkgsDir = packagesDir();
  const sagentDir = path.join(os.homedir(), ".sagent");
  const venvDir = path.join(sagentDir, "venv");
  const pythonPath = [
    path.join(apiDir, "src"),
    path.join(pkgsDir, "tools", "src"),
    path.join(pkgsDir, "agent-core", "src"),
    path.join(pkgsDir, "memory", "src"),
  ].join(path.delimiter);

  const baseEnv = {
    ...process.env,
    PYTHONPATH: pythonPath,
    PATH: augmentPath(),
    UV_PROJECT_ENVIRONMENT: venvDir,
  };

  const uvBin = findUv();
  const venvPython = isWin ? path.join(venvDir, "Scripts", "python.exe") : path.join(venvDir, "bin", "python3");

  updateSplash("Backend startet...");

  fs.mkdirSync(sagentDir, { recursive: true });

  backendProcess = spawn(uvBin, [
    "run", "uvicorn", "sagent_agent_api.main:app",
    "--app-dir", "src",
    "--host", "127.0.0.1",
    "--port", String(API_PORT),
  ], { cwd: apiDir, env: baseEnv, stdio: "pipe" });

  let stderrBuf = "";
  backendProcess.stdout.on("data", (d) => process.stdout.write(`[backend] ${d}`));
  backendProcess.stderr.on("data", (d) => {
    const text = d.toString();
    process.stderr.write(`[backend] ${text}`);
    stderrBuf += text;
    if (stderrBuf.length > 500) stderrBuf = stderrBuf.slice(-500);
    updateSplash("Backend startet...", stderrBuf.slice(-120));
  });
  backendProcess.on("exit", (code) => {
    console.log(`Backend exited with code ${code}`);
    backendProcess = null;
    if (booting) updateSplash("Backend abgestürzt", `exit code ${code}`);
  });
  backendProcess.on("error", (err) => {
    console.error("Backend error:", err.message);
    updateSplash("Backend Fehler", err.message);
    backendProcess = null;
  });
}

function findFreePort(preferred, cb) {
  const srv = net.createServer();
  srv.on("error", () => srv.listen(0, "127.0.0.1", () => { const p = srv.address().port; srv.close(() => cb(p)); }));
  srv.listen(preferred, "127.0.0.1", () => { const p = srv.address().port; srv.close(() => cb(p)); });
}

function checkServer(url, retries = 30, delay = 500) {
  return new Promise((resolve) => {
    function tryOnce(n) {
      http.get(url, (res) => { res.resume(); resolve(true); })
        .on("error", () => {
          if (n >= retries) resolve(false);
          else setTimeout(() => tryOnce(n + 1), delay);
        });
    }
    tryOnce(0);
  });
}

function serveStatic(dir) {
  const server = http.createServer((req, res) => {
    const safePath = path.normalize(req.url).replace(/^(\.\.(\/|\\|$))+/, "");
    const requested = req.url === "/" ? "index.html" : safePath;
    const filePath = path.join(dir, requested);
    if (!filePath.startsWith(path.resolve(dir))) { res.writeHead(403); res.end("Forbidden"); return; }
    const ext = path.extname(filePath);
    try {
      const content = fs.readFileSync(filePath);
      res.writeHead(200, { "Content-Type": MIME_TYPES[ext] || "text/plain", "Cache-Control": "no-cache" });
      res.end(content);
    } catch {
      const fb = path.join(dir, "404.html");
      if (fs.existsSync(fb)) { res.writeHead(404, { "Content-Type": "text/html" }); res.end(fs.readFileSync(fb)); }
      else { res.writeHead(404); res.end("Not found"); }
    }
  });
  server.listen(WEB_PORT, "127.0.0.1");
  return server;
}

function loadWindowState() {
  try { return JSON.parse(fs.readFileSync(STATE_PATH, "utf8")); }
  catch { return { width: 1280, height: 860 }; }
}

function saveWindowState() {
  if (!mainWindow) return;
  try {
    const b = mainWindow.getBounds();
    fs.mkdirSync(path.dirname(STATE_PATH), { recursive: true });
    fs.writeFileSync(STATE_PATH, JSON.stringify({ width: b.width, height: b.height, x: b.x, y: b.y }));
  } catch {}
}

function createMainWindow(url) {
  const state = loadWindowState();
  mainWindow = new BrowserWindow({
    width: state.width, height: state.height, x: state.x, y: state.y,
    minWidth: 900, minHeight: 600,
    title: "Sagent",
    titleBarStyle: isMac ? "hiddenInset" : "default",
    show: false,
    webPreferences: { nodeIntegration: false, contextIsolation: true },
  });
  mainWindow.loadURL(url);
  mainWindow.once("ready-to-show", () => { closeSplash(); mainWindow.show(); });
  mainWindow.on("closed", () => { mainWindow = null; });
  mainWindow.on("resize", saveWindowState);
  mainWindow.on("move", saveWindowState);
}

function buildMenu() {
  const isMac = process.platform === "darwin";
  Menu.setApplicationMenu(Menu.buildFromTemplate([
    ...(isMac ? [{
      label: "Sagent",
      submenu: [
        { role: "about" }, { type: "separator" },
        { role: "hide" }, { role: "hideOthers" }, { role: "unhide" },
        { type: "separator" }, { role: "quit" },
      ],
    }] : []),
    {
      label: "Edit",
      submenu: [
        { role: "undo" }, { role: "redo" }, { type: "separator" },
        { role: "cut" }, { role: "copy" }, { role: "paste" },
        ...(isMac ? [{ role: "pasteAndMatchStyle" }, { role: "delete" }, { role: "selectAll" }]
                    : [{ role: "delete" }, { type: "separator" }, { role: "selectAll" }]),
      ],
    },
    {
      label: "View",
      submenu: [
        { role: "reload" }, { role: "forceReload" }, { role: "toggleDevTools" },
        { type: "separator" },
        { role: "resetZoom" }, { role: "zoomIn" }, { role: "zoomOut" },
        { type: "separator" }, { role: "togglefullscreen" },
      ],
    },
    {
      label: "Window",
      submenu: [
        { role: "minimize" }, { role: "zoom" },
        ...(isMac ? [{ type: "separator" }, { role: "front" }, { type: "separator" }, { role: "window" }]
                    : [{ role: "close" }]),
      ],
    },
  ]));
}

async function boot() {
  booting = true;
  buildMenu();
  showSplash();

  if (!DEV) {
    startBackend();

    await new Promise((resolve) => findFreePort(WEB_PORT, (port) => { WEB_PORT = port; resolve(); }));
    updateSplash("Frontend wird gestartet...");
    frontendServer = serveStatic(path.resolve(__dirname, "web-out"));

    updateSplash("Warte auf Backend...");
    const apiOk = await checkServer(`http://127.0.0.1:${API_PORT}`, 40);
    if (!apiOk) { updateSplash("Backend nicht erreichbar", "Bitte starte die App neu"); booting = false; return; }

    updateSplash("Warte auf Frontend...");
    const webOk = await checkServer(`http://127.0.0.1:${WEB_PORT}`, 10);
    if (!webOk) { updateSplash("Frontend nicht erreichbar", "Bitte starte die App neu"); booting = false; return; }
  } else {
    const [apiOk, webOk] = await Promise.all([
      checkServer(`http://127.0.0.1:${API_PORT}`, 3, 200),
      checkServer(`http://127.0.0.1:${WEB_PORT}`, 3, 200),
    ]);
    if (!apiOk || !webOk) { closeSplash(); app.quit(); return; }
  }

  booting = false;
  createMainWindow(`http://127.0.0.1:${WEB_PORT}`);
}

function cleanup() {
  if (backendProcess) { backendProcess.kill(); backendProcess = null; }
  if (frontendServer) { frontendServer.close(); frontendServer = null; }
  saveWindowState();
}

app.whenReady().then(boot);

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") { cleanup(); app.quit(); }
});

app.on("activate", () => {
  if (!mainWindow && !booting) boot();
});

app.on("before-quit", cleanup);
