const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

console.log('Running post-install setup...');

const rootDir = path.resolve(__dirname, '..');

try {
  if (fs.existsSync(path.join(rootDir, 'apps', 'api'))) {
    console.log('Setting up Python dependencies...');
    try {
      execSync('uv sync', { cwd: path.join(rootDir, 'apps', 'api'), stdio: 'inherit' });
    } catch (e) {
      console.log('uv not found, skipping Python setup');
    }
  }

  console.log('Post-install complete!');
} catch (error) {
  console.error('Post-install error:', error.message);
}