const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const API = path.join(ROOT, 'api');
const WEB = path.join(ROOT, 'web');
const VENV = path.join(API, 'venv');
const isWin = process.platform === 'win32';

function ready() {
  const py = isWin
    ? path.join(VENV, 'Scripts', 'python.exe')
    : path.join(VENV, 'bin', 'python');
  return fs.existsSync(py);
}

// Auto-setup if venv missing
if (!ready()) {
  console.log('\n⚠️  First time setup detected. Running setup...\n');
  require('./setup.js');
  console.log('');
}

const VENV_PY = isWin
  ? path.join(VENV, 'Scripts', 'python.exe')
  : path.join(VENV, 'bin', 'python');

function start(name, cmd, args, opts = {}) {
  const proc = spawn(cmd, args, { stdio: 'pipe', shell: true, ...opts });
  proc.stdout.on('data', d => {
    d.toString().split('\n').filter(Boolean).forEach(l => console.log(`[${name}] ${l}`));
  });
  proc.stderr.on('data', d => {
    d.toString().split('\n').filter(Boolean).forEach(l => console.error(`[${name}] ${l}`));
  });
  proc.on('error', e => console.error(`[${name}] Error:`, e.message));
  proc.on('exit', code => {
    if (code !== null && code !== 0) console.log(`[${name}] Exited with code ${code}`);
  });
  return proc;
}

console.log('\n=== TenderIQ ===\n');
console.log(`  API  → http://localhost:8000  (${VENV_PY})`);
console.log('  Web  → http://localhost:3000');
console.log('  Docs → http://localhost:8000/docs');
console.log('  Stop → Ctrl+C\n');

const api = start('api', VENV_PY, ['-m', 'uvicorn', 'src.main:app', '--reload', '--port', '8000'], { cwd: API });
const web = start('web', 'pnpm', ['dev'], { cwd: WEB });

process.on('SIGINT', () => {
  console.log('\nShutting down...');
  api.kill();
  web.kill();
  process.exit(0);
});
