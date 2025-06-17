const fs = require('fs-extra');
const path = require('path');
const os = require('os');

class ConfigGenerator {
  constructor() {
    this.configDir = path.join(os.homedir(), '.mcp-process-image');
    this.configPath = path.join(this.configDir, 'mcp-config.json');
  }

  getConfigPath() {
    return this.configPath;
  }

  async generateConfig(openaiApiKey, installPath) {
    // Ensure config directory exists
    await fs.ensureDir(this.configDir);

    const isWindows = process.platform === 'win32';
    const binDir = isWindows ? 'Scripts' : 'bin';
    const pythonName = isWindows ? 'python.exe' : 'python';
    const pythonPath = path.join(installPath, 'venv', binDir, pythonName);
    const srcPath = path.join(installPath, 'src');

    const config = {
      mcpServers: {
        "mcp-process-image": {
          command: pythonPath,
          args: ["-m", "mcp_process_image.server"],
          cwd: installPath,
          env: {
            PYTHONPATH: srcPath,
            OPENAI_API_KEY: openaiApiKey,
            DEFAULT_API_PROVIDER: "openai"
          }
        }
      }
    };

    await fs.writeJson(this.configPath, config, { spaces: 2 });
    return config;
  }

  async getConfig() {
    if (await fs.pathExists(this.configPath)) {
      return await fs.readJson(this.configPath);
    }
    return null;
  }

  async removeConfig() {
    if (await fs.pathExists(this.configPath)) {
      await fs.remove(this.configPath);
    }
  }

  async updateOpenAIKey(newApiKey) {
    const config = await this.getConfig();
    if (config && config.mcpServers && config.mcpServers['mcp-process-image']) {
      config.mcpServers['mcp-process-image'].env.OPENAI_API_KEY = newApiKey;
      await fs.writeJson(this.configPath, config, { spaces: 2 });
      return config;
    }
    throw new Error('Configuration not found');
  }

  getClaudeDesktopInstructions() {
    const isWindows = process.platform === 'win32';
    const isMac = process.platform === 'darwin';

    let configLocation;
    if (isMac) {
      configLocation = '~/Library/Application Support/Claude/claude_desktop_config.json';
    } else if (isWindows) {
      configLocation = '%APPDATA%\\Claude\\claude_desktop_config.json';
    } else {
      configLocation = '~/.config/claude/claude_desktop_config.json';
    }

    return {
      configLocation,
      instructions: [
        '1. Open Claude Desktop',
        '2. Go to Settings (gear icon)',
        '3. Navigate to the MCP section',
        '4. Add the configuration shown above',
        '5. Restart Claude Desktop',
        '6. The MCP Process Image server will be available in new conversations'
      ]
    };
  }
}

module.exports = { ConfigGenerator }; 