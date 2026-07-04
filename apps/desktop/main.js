const { app, BrowserWindow } = require("electron");
const { spawn } = require("child_process");
const http = require("http");
const path = require("path");

const WEB_URL = "http://127.0.0.1:3000";
const API_URL = "http://127.0.0.1:8765";

let mainWindow = null;

function checkServer(url, retries = 20, delay = 500) {
  return new Promise((resolve) => {
    function tryOnce(attempt) {
      http.get(url, (res) => { res.resume(); resolve(true); })
        .on("error", () => {
          if (attempt >= retries) resolve(false);
          else setTimeout(() => tryOnce(attempt + 1), delay);
        });
    }
    tryOnce(0);
  });
}

async function createWindow() {
  const apiOk = await checkServer(API_URL);
  const webOk = await checkServer(WEB_URL);

  if (!apiOk || !webOk) {
    console.log("Starting backend + frontend...");
    const root = path.resolve(__dirname, "../..");
    const apiDir = path.resolve(__dirname, "../../apps/agent-api");
    const pythonPath = ["src", "../../packages/tools/src", "../../packages/agent-core/src", "../../packages/memory/src"].join(":");

    spawn("uv", ["run", "uvicorn", "sagent_agent_api.main:app", "--app-dir", "src", "--host", "127.0.0.1", "--port", "8765"], {
      cwd: apiDir, env: { ...process.env, PYTHONPATH: pythonPath }, stdio: "pipe",
    });

    spawn("npx", ["next", "dev", "--hostname", "127.0.0.1", "--port", "3000"], {
      cwd: path.resolve(__dirname, "../../apps/web"), stdio: "pipe", shell: true,
    });

    // Wait for servers to start
    await checkServer(API_URL, 40, 500);
    await checkServer(WEB_URL, 40, 500);
  }

  mainWindow = new BrowserWindow({
    width: 1280, height: 860, minWidth: 900, minHeight: 600,
    title: "Sagent",
    titleBarStyle: "hiddenInset",
    webPreferences: { nodeIntegration: false, contextIsolation: true },
  });

  mainWindow.loadURL(WEB_URL);
  // mainWindow.webContents.openDevTools();
}

app.whenReady().then(createWindow);

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});

app.on("activate", () => {
  if (mainWindow === null) createWindow();
});
