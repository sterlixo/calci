const { app, BrowserWindow } = require('electron')
const { spawn } = require('child_process')
const path = require('path')

// Force consistent zoom regardless of how app is launched (terminal vs desktop icon)
app.commandLine.appendSwitch('force-device-scale-factor', '1')

let win, server

function startFlask() {
  server = spawn('python3', ['server.py'], {
    cwd: __dirname,
    env: { ...process.env }
  })

  server.stdout.on('data', (data) => {
    console.log(`Flask: ${data}`)
  })

  server.stderr.on('data', (data) => {
    console.error(`Flask error: ${data}`)
  })
}

function createWindow() {
  win = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 900,
    minHeight: 600,
    title: 'Calcium — AI Pentesting Assistant',
    backgroundColor: '#1a1a2e',
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true
    },
    // Frameless titlebar on Linux
    frame: true,
    show: false
  })

  win.setMenuBarVisibility(false)

  // Try to load, retry until Flask is ready
  function tryLoad(retries = 10) {
    win.loadURL('http://localhost:5000').then(() => {
      win.webContents.setZoomFactor(1.5)  // Force consistent zoom level always
      win.show()
    }).catch(() => {
      if (retries > 0) {
        setTimeout(() => tryLoad(retries - 1), 800)
      } else {
        win.loadFile('error.html')
        win.show()
      }
    })
  }

  setTimeout(() => tryLoad(), 1500)

  win.on('closed', () => { win = null })
}

app.whenReady().then(() => {
  startFlask()
  createWindow()
})

app.on('window-all-closed', () => {
  if (server) server.kill()
  app.quit()
})

app.on('activate', () => {
  if (win === null) createWindow()
})
