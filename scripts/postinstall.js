const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const rootDir = path.resolve(__dirname, '..');
const apiDir = path.join(rootDir, 'apps', 'api');
const reqDev = path.join(apiDir, 'requirements-dev.txt');

if (!fs.existsSync(reqDev)) {
  console.log('[postinstall] apps/api/requirements-dev.txt not found — skip Python setup');
  process.exit(0);
}

console.log('[postinstall] Optional API Python setup (use run.bat for full venv)...');

function tryExec(cmd, opts) {
  try {
    execSync(cmd, { stdio: 'inherit', ...opts });
    return true;
  } catch {
    return false;
  }
}

const venvPython =
  process.platform === 'win32'
    ? path.join(apiDir, 'venv', 'Scripts', 'python.exe')
    : path.join(apiDir, 'venv', 'bin', 'python');

if (fs.existsSync(venvPython)) {
  const pip = process.platform === 'win32' ? 'Scripts\\pip.exe' : 'bin/pip';
  const pipPath = path.join(apiDir, 'venv', pip);
  if (fs.existsSync(pipPath)) {
    tryExec(`"${pipPath}" install -r requirements-dev.txt`, { cwd: apiDir });
    process.exit(0);
  }
}

if (tryExec('uv pip install -r requirements-dev.txt', { cwd: apiDir })) {
  process.exit(0);
}

console.log('[postinstall] No venv/uv yet — Python deps installed on first run.bat');
