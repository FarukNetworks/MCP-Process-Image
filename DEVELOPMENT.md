# Development Guide

This guide is for developers working with the cloned repository of MCP Process Image.

## Quick Start for Cloned Repository

When you clone this repository and want to test the MCP server locally, follow these steps:

### 1. Install Dependencies

```bash
npm install
```

### 2. Install MCP Server (Development Mode)

Instead of using `npx mcp-process-image install`, use the development script:

```bash
# Using the development script
node scripts/dev-install.js --openai-key sk-your-openai-api-key

# OR using npm script
npm run dev:install -- --openai-key sk-your-openai-api-key
```

### 3. Available Development Commands

```bash
# Install MCP server
npm run dev:install -- --openai-key sk-your-key

# Check installation status
npm run dev:status

# View configuration
npm run dev:config

# Update configuration
npm run dev:config -- --openai-key sk-new-key

# Start server for testing
npm run dev:start

# Uninstall
npm run dev:uninstall
```

### 4. Alternative: Direct Node Commands

You can also run the CLI directly with Node.js:

```bash
# Install
node bin/mcp-process-image.js install --openai-key sk-your-key

# Status
node bin/mcp-process-image.js status

# Config
node bin/mcp-process-image.js config

# Help
node bin/mcp-process-image.js --help
```

## Why Not Use NPX with Cloned Repository?

When you clone the repository and run `npx mcp-process-image`, NPX tries to use the local version but may have issues with module resolution because:

1. The package isn't installed globally or in node_modules
2. The relative paths in require statements may not resolve correctly
3. NPX expects a published package structure

## Development Workflow

### 1. Making Changes

1. **Edit the code** in `src/`, `bin/`, or `lib/`
2. **Test locally** using the development commands above
3. **Verify the installation works** on your machine

### 2. Testing Installation

```bash
# Clean install
npm run dev:uninstall -- --force
npm run dev:install -- --openai-key sk-your-test-key

# Check status
npm run dev:status

# Test configuration
npm run dev:config
```

### 3. Testing the MCP Server

```bash
# Start the server (for debugging)
npm run dev:start

# Or test the Python module directly
cd ~/.mcp-process-image
./venv/bin/python -c "import mcp_process_image.server; print('✅ Module loads correctly')"
```

## Project Structure

```
mcp-process-image/
├── bin/
│   └── mcp-process-image.js     # Main CLI script
├── lib/
│   ├── installer.js             # Python environment management
│   └── config-generator.js      # MCP configuration generation
├── scripts/
│   └── dev-install.js           # Development installation script
├── src/
│   └── mcp_process_image/       # Python MCP server code
├── package.json                 # NPM package configuration
├── pyproject.toml              # Python package configuration
└── README.md                   # User documentation
```

## Debugging Common Issues

### 1. "Cannot find module" Error

If you get module resolution errors:

```bash
# Make sure you're in the project root
pwd  # Should show the mcp-process-image directory

# Use the development scripts instead of npx
npm run dev:install -- --openai-key sk-your-key
```

### 2. Python Installation Issues

```bash
# Check Python version
python3 --version  # Should be 3.10+

# Check if virtual environment was created
ls ~/.mcp-process-image/venv/

# Test Python module import
cd ~/.mcp-process-image
./venv/bin/python -c "import sys; print(sys.path)"
```

### 3. Configuration Issues

```bash
# Check if config file exists
ls ~/.mcp-process-image/mcp-config.json

# View configuration
npm run dev:config

# Regenerate configuration
npm run dev:config -- --openai-key sk-your-key
```

## Publishing Workflow

When you're ready to publish to NPM:

1. **Test thoroughly** using development commands
2. **Update version** in package.json
3. **Commit changes** to Git
4. **Create a release** on GitHub (triggers auto-publish)

Or manually:

```bash
npm version patch  # or minor/major
npm publish
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test using development commands
5. Submit a pull request

## Support

For development issues:

- Check this guide first
- Look at existing GitHub issues
- Create a new issue with detailed error messages
