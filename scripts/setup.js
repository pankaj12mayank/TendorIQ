const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const API = path.join(ROOT, 'api');
const WEB = path.join(ROOT, 'web');
const VENV = path.join(API, 'venv');
const isWin = process.platform === 'win32';
const PY = () => isWin ? `"${path.join(VENV, 'Scripts', 'python.exe')}"` : `"${path.join(VENV, 'bin', 'python')}"`;
const PIP = () => isWin ? `"${path.join(VENV, 'Scripts', 'pip.exe')}"` : `"${path.join(VENV, 'bin', 'pip')}"`;

function run(cmd, opts = {}) {
  console.log(`  > ${cmd}`);
  try { execSync(cmd, { stdio: 'inherit', ...opts }); return true }
  catch (e) { console.error(`  FAILED: ${e.message}`); return false }
}

function exists(f) { return fs.existsSync(f) }

console.log('\n=== TenderIQ Setup ===\n');

// 1. .env
console.log('[1/6] Environment...');
if (!exists(path.join(ROOT, '.env'))) {
  if (exists(path.join(ROOT, '.env.example'))) {
    fs.copyFileSync(path.join(ROOT, '.env.example'), path.join(ROOT, '.env'));
    console.log('  Created .env from .env.example');
  }
} else { console.log('  .env OK') }

// 2. Python venv
console.log('[2/6] Python venv...');
if (!exists(path.join(VENV, isWin ? 'Scripts' : 'bin', 'python' + (isWin ? '.exe' : '')))) {
  run(`python -m venv "${VENV}"`, { cwd: API });
  console.log('  Venv created');
} else { console.log('  Venv OK') }

// 3. Python deps
console.log('[3/6] Python dependencies...');
run(`${PIP()} install --upgrade pip`, { cwd: API });
run(`${PIP()} install -r "${path.join(API, 'requirements.txt')}"`, { cwd: API });

// 4. Database dir
console.log('[4/6] Database...');
const dbDir = path.join(ROOT, '.tenderiq', 'data');
if (!exists(dbDir)) { fs.mkdirSync(dbDir, { recursive: true }); console.log('  Created .tenderiq/data/') }
run(`${PY()} -m alembic upgrade head`, { cwd: API });

// 5. Web deps
console.log('[5/6] Web dependencies...');
run('pnpm install', { cwd: WEB });

// 6. Web env
console.log('[6/6] Web environment...');
const webEnv = [
  'NEXT_PUBLIC_API_URL=http://127.0.0.1:8000',
  'NEXT_PUBLIC_APP_URL=http://localhost:3000',
  'NEXT_PUBLIC_AUTH_PROVIDER=local',
  'NEXT_PUBLIC_USE_API_PROXY=1',
  'NEXT_PUBLIC_FEATURE_AI_ANALYSIS=true',
  'NEXT_PUBLIC_FEATURE_DOCUMENT_OCR=false',
  'NEXT_PUBLIC_FEATURE_ADVANCED_ANALYTICS=false',
  'NEXT_PUBLIC_FEATURE_SSO=false',
].join('\n') + '\n';
fs.writeFileSync(path.join(WEB, '.env.local'), webEnv, 'utf-8');
console.log('  web/.env.local synced');

console.log('\n✅ Setup complete. Run: pnpm dev\n');
