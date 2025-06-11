const { app, BrowserWindow, globalShortcut, dialog } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const http = require('http');

let mainWindow;
let serverProcess;
const SERVER_PORT = 8000;
const ROOT_DIR = path.join(__dirname, '..');
const PYTHON_BIN = process.platform === 'win32' ? 'python' : 'python3';

function startServer() {
  return new Promise((resolve, reject) => {
    serverProcess = spawn(PYTHON_BIN, ['-m', 'app.server'], { cwd: ROOT_DIR });
    serverProcess.on('error', reject);

    const maxAttempts = 20;
    let attempts = 0;
    const timer = setInterval(() => {
      http.get(`http://127.0.0.1:${SERVER_PORT}/health`, res => {
        if (res.statusCode === 200) {
          clearInterval(timer);
          resolve();
        }
        res.resume();
      }).on('error', () => {
        // wait until server starts
      });

      attempts += 1;
      if (attempts >= maxAttempts) {
        clearInterval(timer);
        reject(new Error('Server start timeout'));
      }
    }, 500);
  });
}

function stopServer() {
  if (serverProcess) {
    serverProcess.kill();
    serverProcess = null;
  }
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
    },
  });

  mainWindow.loadFile(path.join(__dirname, 'src', 'index.html'));
}

app.whenReady().then(async () => {
  try {
    await startServer();
  } catch (err) {
    dialog.showErrorBox('Server Error', 'Failed to start Python server.');
    app.quit();
    return;
  }

  createWindow();

  globalShortcut.register('Alt+Space', () => {
    if (!mainWindow) return;
    if (mainWindow.isFocused()) {
      mainWindow.blur();
    } else {
      mainWindow.show();
      mainWindow.focus();
    }
  });

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('will-quit', () => {
  globalShortcut.unregisterAll();
  stopServer();
});
