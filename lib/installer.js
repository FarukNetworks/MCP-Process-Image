const fs = require('fs-extra');
const path = require('path');
const os = require('os');
const { spawn } = require('cross-spawn');
const chalk = require('chalk');

class PythonInstaller {
  constructor() {
    this.installDir = path.join(os.homedir(), '.mcp-process-image');
    this.venvPath = path.join(this.installDir, 'venv');
    this.srcPath = path.join(this.installDir, 'src');
  }

  getInstallPath() {
    return this.installDir;
  }

  async isInstalled() {
    try {
      const venvExists = await fs.pathExists(this.venvPath);
      const srcExists = await fs.pathExists(this.srcPath);
      return venvExists && srcExists;
    } catch (error) {
      return false;
    }
  }

  async checkPython() {
    return new Promise((resolve, reject) => {
      const python = this.getPythonCommand();
      const child = spawn(python, ['--version'], { stdio: 'pipe' });

      let output = '';
      child.stdout.on('data', (data) => {
        output += data.toString();
      });

      child.stderr.on('data', (data) => {
        output += data.toString();
      });

      child.on('close', (code) => {
        if (code === 0) {
          const version = output.match(/Python (\d+\.\d+)/);
          if (version) {
            const majorMinor = version[1].split('.').map(Number);
            if (majorMinor[0] >= 3 && majorMinor[1] >= 10) {
              resolve(version[1]);
            } else {
              reject(new Error(`Python 3.10+ required, found ${version[1]}`));
            }
          } else {
            reject(new Error('Could not determine Python version'));
          }
        } else {
          reject(new Error('Python not found. Please install Python 3.10 or later.'));
        }
      });
    });
  }

  getPythonCommand() {
    // Try different Python commands based on platform
    const commands = process.platform === 'win32'
      ? ['python', 'python3', 'py']
      : ['python3', 'python'];

    // For now, return the first one. In a real implementation,
    // we'd test each command to see which one works
    return commands[0];
  }

  async createVirtualEnvironment() {
    // Ensure install directory exists
    await fs.ensureDir(this.installDir);

    // Remove existing venv if it exists
    if (await fs.pathExists(this.venvPath)) {
      await fs.remove(this.venvPath);
    }

    return new Promise((resolve, reject) => {
      const python = this.getPythonCommand();
      const child = spawn(python, ['-m', 'venv', this.venvPath], {
        stdio: 'pipe',
        cwd: this.installDir
      });

      let errorOutput = '';
      child.stderr.on('data', (data) => {
        errorOutput += data.toString();
      });

      child.on('close', (code) => {
        if (code === 0) {
          resolve();
        } else {
          reject(new Error(`Failed to create virtual environment: ${errorOutput}`));
        }
      });
    });
  }

  async installDependencies() {
    // Copy source files to installation directory
    const packageRoot = path.resolve(__dirname, '..');
    const srcSource = path.join(packageRoot, 'src');
    const pyprojectSource = path.join(packageRoot, 'pyproject.toml');
    const readmeSource = path.join(packageRoot, 'README.md');

    await fs.copy(srcSource, this.srcPath);
    await fs.copy(pyprojectSource, path.join(this.installDir, 'pyproject.toml'));

    // Copy README.md if it exists (required by hatchling)
    if (await fs.pathExists(readmeSource)) {
      await fs.copy(readmeSource, path.join(this.installDir, 'README.md'));
    }

    // Install dependencies using pip
    const pipPath = this.getPipPath();

    // First upgrade pip to avoid version issues
    await new Promise((resolve, reject) => {
      const upgradeChild = spawn(pipPath, ['install', '--upgrade', 'pip'], {
        stdio: 'pipe',
        cwd: this.installDir
      });

      upgradeChild.on('close', (code) => {
        resolve(); // Continue even if upgrade fails
      });
    });

    return new Promise((resolve, reject) => {
      const child = spawn(pipPath, [
        'install',
        '.',
        '--quiet'
      ], {
        stdio: 'pipe',
        cwd: this.installDir
      });

      let errorOutput = '';
      child.stderr.on('data', (data) => {
        errorOutput += data.toString();
      });

      child.on('close', async (code) => {
        if (code === 0) {
          resolve();
        } else {
          // Try fallback installation method
          try {
            await this.installDependenciesFallback();
            resolve();
          } catch (fallbackError) {
            reject(new Error(`Failed to install dependencies: ${errorOutput}\nFallback also failed: ${fallbackError.message}`));
          }
        }
      });
    });
  }

  async installDependenciesFallback() {
    // Fallback: Install dependencies individually
    const pipPath = this.getPipPath();

    const dependencies = [
      'mcp[cli]>=1.0.0',
      'pillow>=10.0.0',
      'httpx>=0.25.0',
      'pydantic>=2.0.0',
      'python-dotenv>=1.0.0',
      'openai>=1.0.0',
      'anthropic>=0.25.0',
      'google-cloud-vision>=3.4.0',
      'azure-cognitiveservices-vision-computervision>=0.9.0',
      'tenacity>=8.2.0'
    ];

    for (const dep of dependencies) {
      await new Promise((resolve, reject) => {
        const child = spawn(pipPath, ['install', dep, '--quiet'], {
          stdio: 'pipe',
          cwd: this.installDir
        });

        child.on('close', (code) => {
          if (code === 0) {
            resolve();
          } else {
            // Continue with other dependencies even if one fails
            resolve();
          }
        });
      });
    }
  }

  getPipPath() {
    const isWindows = process.platform === 'win32';
    const binDir = isWindows ? 'Scripts' : 'bin';
    const pipName = isWindows ? 'pip.exe' : 'pip';
    return path.join(this.venvPath, binDir, pipName);
  }

  getPythonPath() {
    const isWindows = process.platform === 'win32';
    const binDir = isWindows ? 'Scripts' : 'bin';
    const pythonName = isWindows ? 'python.exe' : 'python';
    return path.join(this.venvPath, binDir, pythonName);
  }

  async getPythonVersion() {
    if (!await this.isInstalled()) {
      return 'Not installed';
    }

    return new Promise((resolve, reject) => {
      const pythonPath = this.getPythonPath();
      const child = spawn(pythonPath, ['--version'], { stdio: 'pipe' });

      let output = '';
      child.stdout.on('data', (data) => {
        output += data.toString();
      });

      child.stderr.on('data', (data) => {
        output += data.toString();
      });

      child.on('close', (code) => {
        if (code === 0) {
          const version = output.match(/Python (\d+\.\d+\.\d+)/);
          resolve(version ? version[1] : 'Unknown');
        } else {
          resolve('Error getting version');
        }
      });
    });
  }

  async startServer() {
    if (!await this.isInstalled()) {
      throw new Error('MCP Process Image is not installed');
    }

    const pythonPath = this.getPythonPath();
    const serverModule = path.join(this.srcPath, 'mcp_process_image', 'server.py');

    return new Promise((resolve, reject) => {
      const child = spawn(pythonPath, ['-m', 'mcp_process_image.server'], {
        stdio: 'inherit',
        cwd: this.installDir,
        env: {
          ...process.env,
          PYTHONPATH: this.srcPath
        }
      });

      child.on('close', (code) => {
        if (code === 0) {
          resolve();
        } else {
          reject(new Error(`Server exited with code ${code}`));
        }
      });

      child.on('error', (error) => {
        reject(error);
      });
    });
  }

  async uninstall() {
    if (await fs.pathExists(this.installDir)) {
      await fs.remove(this.installDir);
    }
  }
}

module.exports = { PythonInstaller }; 