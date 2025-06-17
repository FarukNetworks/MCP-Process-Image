#!/usr/bin/env node

const { Command } = require('commander');
const chalk = require('chalk');
const ora = require('ora');
const inquirer = require('inquirer');
const path = require('path');
const os = require('os');
const fs = require('fs-extra');

const { PythonInstaller } = require('../lib/installer');
const { ConfigGenerator } = require('../lib/config-generator');

const program = new Command();
const installer = new PythonInstaller();
const configGenerator = new ConfigGenerator();

program
  .name('mcp-process-image')
  .description('MCP server for processing images using various AI vision APIs')
  .version('1.0.0');

program
  .command('install')
  .description('Install and configure the MCP Process Image server')
  .option('--openai-key <key>', 'OpenAI API key')
  .option('--force', 'Force reinstallation even if already installed')
  .action(async (options) => {
    console.log(chalk.blue.bold('🖼️  MCP Process Image Server Installer\n'));

    try {
      // Check if already installed
      const installPath = installer.getInstallPath();
      const isInstalled = await installer.isInstalled();

      if (isInstalled && !options.force) {
        console.log(chalk.yellow('⚠️  MCP Process Image is already installed.'));
        console.log(chalk.gray(`   Installation path: ${installPath}`));
        console.log(chalk.gray('   Use --force to reinstall or run "config" to update settings.\n'));
        return;
      }

      // Get OpenAI API key
      let openaiKey = options.openaiKey;
      if (!openaiKey) {
        const answers = await inquirer.prompt([
          {
            type: 'password',
            name: 'openaiKey',
            message: 'Enter your OpenAI API key:',
            mask: '*',
            validate: (input) => {
              if (!input || input.trim().length === 0) {
                return 'OpenAI API key is required';
              }
              if (!input.startsWith('sk-')) {
                return 'OpenAI API key should start with "sk-"';
              }
              return true;
            }
          }
        ]);
        openaiKey = answers.openaiKey;
      }

      // Install Python environment and dependencies
      const spinner = ora('Setting up Python environment...').start();

      try {
        await installer.checkPython();
        spinner.text = 'Creating virtual environment...';
        await installer.createVirtualEnvironment();

        spinner.text = 'Installing Python dependencies...';
        await installer.installDependencies();

        spinner.text = 'Generating MCP configuration...';
        await configGenerator.generateConfig(openaiKey, installPath);

        spinner.succeed('Installation completed successfully!');
      } catch (error) {
        spinner.fail('Installation failed');
        throw error;
      }

      // Show success message and next steps
      console.log(chalk.green.bold('\n✅ Installation Complete!\n'));
      console.log(chalk.white('Next steps:'));
      console.log(chalk.gray('1. Copy the generated MCP configuration to your Claude Desktop settings'));
      console.log(chalk.gray('2. Restart Claude Desktop'));
      console.log(chalk.gray('3. The MCP Process Image server will be available in Claude\n'));

      console.log(chalk.blue('Configuration file location:'));
      console.log(chalk.gray(`   ${configGenerator.getConfigPath()}\n`));

      console.log(chalk.blue('To view the configuration:'));
      console.log(chalk.gray('   npx mcp-process-image config\n'));

    } catch (error) {
      console.error(chalk.red.bold('\n❌ Installation failed:'));
      console.error(chalk.red(error.message));
      process.exit(1);
    }
  });

program
  .command('config')
  .description('Show or update MCP configuration')
  .option('--openai-key <key>', 'Update OpenAI API key')
  .option('--show', 'Show current configuration')
  .action(async (options) => {
    try {
      const isInstalled = await installer.isInstalled();
      if (!isInstalled) {
        console.log(chalk.red('❌ MCP Process Image is not installed.'));
        console.log(chalk.gray('   Run "npx mcp-process-image install" first.\n'));
        return;
      }

      if (options.openaiKey) {
        // Update API key
        const spinner = ora('Updating configuration...').start();
        const installPath = installer.getInstallPath();
        await configGenerator.generateConfig(options.openaiKey, installPath);
        spinner.succeed('Configuration updated successfully!');
      }

      // Show current configuration
      const configPath = configGenerator.getConfigPath();
      if (await fs.pathExists(configPath)) {
        console.log(chalk.blue.bold('📋 Current MCP Configuration:\n'));
        const config = await fs.readJson(configPath);
        console.log(chalk.gray(JSON.stringify(config, null, 2)));
        console.log(chalk.blue('\nConfiguration file location:'));
        console.log(chalk.gray(`   ${configPath}\n`));
        console.log(chalk.blue('To use this configuration:'));
        console.log(chalk.gray('1. Copy the JSON above'));
        console.log(chalk.gray('2. Add it to your Claude Desktop MCP settings'));
        console.log(chalk.gray('3. Restart Claude Desktop\n'));
      } else {
        console.log(chalk.red('❌ Configuration file not found.'));
        console.log(chalk.gray('   Run "npx mcp-process-image install" to create it.\n'));
      }

    } catch (error) {
      console.error(chalk.red.bold('\n❌ Configuration error:'));
      console.error(chalk.red(error.message));
      process.exit(1);
    }
  });

program
  .command('uninstall')
  .description('Remove the MCP Process Image server installation')
  .option('--force', 'Force removal without confirmation')
  .action(async (options) => {
    try {
      const isInstalled = await installer.isInstalled();
      if (!isInstalled) {
        console.log(chalk.yellow('⚠️  MCP Process Image is not installed.'));
        return;
      }

      let shouldUninstall = options.force;
      if (!shouldUninstall) {
        const answers = await inquirer.prompt([
          {
            type: 'confirm',
            name: 'confirm',
            message: 'Are you sure you want to uninstall MCP Process Image?',
            default: false
          }
        ]);
        shouldUninstall = answers.confirm;
      }

      if (shouldUninstall) {
        const spinner = ora('Removing installation...').start();
        await installer.uninstall();
        await configGenerator.removeConfig();
        spinner.succeed('Uninstallation completed successfully!');

        console.log(chalk.green.bold('\n✅ Uninstallation Complete!\n'));
        console.log(chalk.gray('Remember to remove the MCP configuration from Claude Desktop settings.\n'));
      } else {
        console.log(chalk.gray('Uninstallation cancelled.\n'));
      }

    } catch (error) {
      console.error(chalk.red.bold('\n❌ Uninstallation failed:'));
      console.error(chalk.red(error.message));
      process.exit(1);
    }
  });

program
  .command('start')
  .description('Start the MCP server (for testing)')
  .action(async () => {
    try {
      const isInstalled = await installer.isInstalled();
      if (!isInstalled) {
        console.log(chalk.red('❌ MCP Process Image is not installed.'));
        console.log(chalk.gray('   Run "npx mcp-process-image install" first.\n'));
        return;
      }

      console.log(chalk.blue.bold('🚀 Starting MCP Process Image Server...\n'));
      console.log(chalk.gray('Press Ctrl+C to stop the server\n'));

      await installer.startServer();

    } catch (error) {
      console.error(chalk.red.bold('\n❌ Failed to start server:'));
      console.error(chalk.red(error.message));
      process.exit(1);
    }
  });

program
  .command('status')
  .description('Check installation status')
  .action(async () => {
    try {
      const isInstalled = await installer.isInstalled();
      const installPath = installer.getInstallPath();
      const configPath = configGenerator.getConfigPath();
      const hasConfig = await fs.pathExists(configPath);

      console.log(chalk.blue.bold('📊 MCP Process Image Status:\n'));

      console.log(`Installation: ${isInstalled ? chalk.green('✅ Installed') : chalk.red('❌ Not installed')}`);
      console.log(`Install path: ${chalk.gray(installPath)}`);
      console.log(`Configuration: ${hasConfig ? chalk.green('✅ Present') : chalk.red('❌ Missing')}`);
      console.log(`Config path: ${chalk.gray(configPath)}`);

      if (isInstalled) {
        const pythonVersion = await installer.getPythonVersion();
        console.log(`Python version: ${chalk.gray(pythonVersion)}`);
      }

      console.log();

    } catch (error) {
      console.error(chalk.red.bold('\n❌ Status check failed:'));
      console.error(chalk.red(error.message));
      process.exit(1);
    }
  });

// Handle unknown commands
program.on('command:*', () => {
  console.error(chalk.red(`❌ Unknown command: ${program.args.join(' ')}`));
  console.log(chalk.gray('Run "npx mcp-process-image --help" for available commands.\n'));
  process.exit(1);
});

// Show help if no command provided
if (process.argv.length <= 2) {
  program.help();
}

program.parse(process.argv); 