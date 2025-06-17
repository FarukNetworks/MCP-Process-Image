#!/usr/bin/env node

/**
 * Development installation script for MCP Process Image
 * Use this when working with the cloned repository instead of the published NPM package
 */

const path = require('path');
const { spawn } = require('child_process');

// Get the OpenAI API key from command line arguments
const args = process.argv.slice(2);
let openaiKey = null;

for (let i = 0; i < args.length; i++) {
  if (args[i] === '--openai-key' && i + 1 < args.length) {
    openaiKey = args[i + 1];
    break;
  }
}

if (!openaiKey) {
  console.error('❌ Error: OpenAI API key is required');
  console.log('Usage: node scripts/dev-install.js --openai-key sk-your-key');
  process.exit(1);
}

// Run the CLI script directly
const cliScript = path.join(__dirname, '..', 'bin', 'mcp-process-image.js');
const child = spawn('node', [cliScript, 'install', '--openai-key', openaiKey], {
  stdio: 'inherit',
  cwd: path.join(__dirname, '..')
});

child.on('close', (code) => {
  process.exit(code);
});

child.on('error', (error) => {
  console.error('❌ Failed to run installation:', error.message);
  process.exit(1);
}); 