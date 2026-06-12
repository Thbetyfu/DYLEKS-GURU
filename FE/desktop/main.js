/**
 * DyLeks Desktop Orchestrator (Electron Main Process).
 * 
 * Alasan Desain ('Why'):
 *   Mengotomatiskan booting backend FastAPI (Port 3002) dan frontend Next.js (Port 3001)
 *   secara transparan untuk guru. Ketika jendela Electron ditutup, semua sub-proses
 *   latar belakang dibersihkan secara paksa untuk menghindari zombie process.
 */

const { app, BrowserWindow } = require('electron');
const { spawn, exec } = require('child_process');
const path = require('path');
const http = require('http');
const fs = require('fs');

let mainWindow;
let backendProcess;
let frontendProcess;

const BACKEND_PORT = 3004;
const FRONTEND_PORT = 3003;

function isPortInUse(port, callback) {
  const server = http.createServer();
  server.once('error', (err) => {
    if (err.code === 'EADDRINUSE') {
      callback(true);
    } else {
      callback(false);
    }
  });
  server.once('listening', () => {
    server.close();
    callback(false);
  });
  server.listen(port, '127.0.0.1');
}

function killProcessOnPort(port) {
  const cmd = process.platform === 'win32'
    ? `for /f "tokens=5" %a in ('netstat -aon ^| findstr :${port}') do taskkill /F /PID %a`
    : `lsof -t -i:${port} | xargs kill -9`;
  
  exec(cmd, (err) => {
    if (!err) {
      console.log(`[Electron] Sukses membersihkan proses zombie di port ${port}`);
    }
  });
}

function startServers() {
  const isProd = app.isPackaged;
  
  // Deteksi letak direktori backend dan frontend secara dinamis untuk mode terinstalasi
  let beDir = path.join(__dirname, 'backend');
  let feDir = path.join(__dirname, 'frontend');

  if (!fs.existsSync(beDir)) {
    // Mode Development (dari FE/desktop)
    beDir = path.join(__dirname, '..', '..', 'BE');
    feDir = path.join(__dirname, '..');
  }

  console.log(`[Electron] Memulai server dalam mode: ${isProd ? 'Production' : 'Development'}`);

  // 1. Jalankan Backend FastAPI
  isPortInUse(BACKEND_PORT, (inUse) => {
    if (inUse) {
      console.log(`[Electron] Port backend ${BACKEND_PORT} sedang digunakan. Membersihkan...`);
      killProcessOnPort(BACKEND_PORT);
    }
    
    setTimeout(() => {
      if (isProd) {
        // Dalam mode production terkompilasi, jalankan exe backend
        backendProcess = spawn(path.join(process.resourcesPath, 'backend', 'backend.exe'), [], {
          cwd: path.join(process.resourcesPath, 'backend')
        });
      } else {
        // Mode development: Jalankan Python
        backendProcess = spawn('python', ['-m', 'uvicorn', 'app.main:app', '--host', '0.0.0.0', '--port', BACKEND_PORT.toString()], {
          cwd: beDir,
          shell: true
        });
      }

      backendProcess.stdout.on('data', (data) => console.log(`[FastAPI] ${data}`));
      backendProcess.stderr.on('data', (data) => console.error(`[FastAPI Err] ${data}`));
    }, 1000);
  });

  // 2. Jalankan Frontend Next.js
  isPortInUse(FRONTEND_PORT, (inUse) => {
    if (inUse) {
      console.log(`[Electron] Port frontend ${FRONTEND_PORT} sedang digunakan. Membersihkan...`);
      killProcessOnPort(FRONTEND_PORT);
    }

    setTimeout(() => {
      if (isProd) {
        // Prod mode: jalankan server static / compiled
        frontendProcess = spawn(path.join(process.resourcesPath, 'frontend', 'server.exe'), [], {
          cwd: path.join(process.resourcesPath, 'frontend')
        });
      } else {
        // Dev mode: Jalankan npm run dev
        frontendProcess = spawn('npm.cmd', ['run', 'dev'], {
          cwd: feDir,
          shell: true
        });
      }

      frontendProcess.stdout.on('data', (data) => console.log(`[Next.js] ${data}`));
      frontendProcess.stderr.on('data', (data) => console.error(`[Next.js Err] ${data}`));
    }, 1000);
  });
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    title: 'DyLeks Local AI Platform',
    autoHideMenuBar: true,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true
    }
  });

  // Tunggu Next.js boot lengkap sebelum me-load halaman utama
  const loadURL = () => {
    mainWindow.loadURL(`http://localhost:${FRONTEND_PORT}`).catch(() => {
      console.log('[Electron] Menunggu Next.js siap...');
      setTimeout(loadURL, 1000);
    });
  };

  setTimeout(loadURL, 3000);

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// Inisialisasi Aplikasi
app.whenReady().then(() => {
  startServers();
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

// Bersihkan semua server ketika Electron di-close
app.on('window-all-closed', () => {
  console.log('[Electron] Jendela ditutup. Menghentikan semua server...');
  
  if (backendProcess) {
    if (process.platform === 'win32') {
      exec(`taskkill /pid ${backendProcess.pid} /f /t`);
    } else {
      backendProcess.kill('SIGINT');
    }
  }

  if (frontendProcess) {
    if (process.platform === 'win32') {
      exec(`taskkill /pid ${frontendProcess.pid} /f /t`);
    } else {
      frontendProcess.kill('SIGINT');
    }
  }

  // Double check dengan kill port
  killProcessOnPort(BACKEND_PORT);
  killProcessOnPort(FRONTEND_PORT);

  if (process.platform !== 'darwin') {
    app.quit();
  }
});
