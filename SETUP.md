# Setup Guide for GitHub and NPM Distribution

This guide will help you prepare the MCP Process Image server for distribution via GitHub and NPM.

## Prerequisites

- Node.js 16+ installed
- NPM account for publishing
- GitHub account
- Git installed

## Step 1: Initialize NPM Package

```bash
# Install Node.js dependencies
npm install

# Test the CLI locally
node bin/mcp-process-image.js --help
```

## Step 2: GitHub Repository Setup

1. **Create a new GitHub repository**:

   - Go to GitHub and create a new repository named `mcp-process-image`
   - Don't initialize with README (we already have one)

2. **Update package.json with your GitHub URL**:

   ```bash
   # Replace "FarukNetworks" with your actual GitHub username
   sed -i 's/FarukNetworks/YOUR_GITHUB_USERNAME/g' package.json
   ```

3. **Initialize Git and push to GitHub**:
   ```bash
   git init
   git add .
   git commit -m "Initial commit: MCP Process Image NPX package"
   git branch -M main
   git remote add origin https://github.com/FarukNetworks/mcp-process-image.git
   git push -u origin main
   ```

## Step 3: NPM Publishing Setup

1. **Login to NPM**:

   ```bash
   npm login
   ```

2. **Check if package name is available**:

   ```bash
   npm view mcp-process-image
   ```

   If the package exists, you'll need to choose a different name or scope it (e.g., `@FarukNetworks/mcp-process-image`).

3. **Update package name if needed**:
   Edit `package.json` and change the name field:
   ```json
   {
     "name": "@FarukNetworks/mcp-process-image",
     ...
   }
   ```

## Step 4: Set up GitHub Secrets

For automated publishing, add these secrets to your GitHub repository:

1. Go to your GitHub repository
2. Navigate to Settings → Secrets and variables → Actions
3. Add these secrets:
   - `NPM_TOKEN`: Your NPM automation token (create at npmjs.com → Access Tokens)

## Step 5: Test Local Installation

Before publishing, test the package locally:

```bash
# Pack the package
npm pack

# Install globally from the packed file
npm install -g mcp-process-image-1.0.0.tgz

# Test the installation
mcp-process-image --help
mcp-process-image status

# Uninstall after testing
npm uninstall -g mcp-process-image
```

## Step 6: Publish to NPM

### Manual Publishing

```bash
# Ensure you're logged in
npm whoami

# Publish the package
npm publish
```

### Automated Publishing via GitHub

1. **Create a release on GitHub**:

   - Go to your repository → Releases → Create a new release
   - Tag version: `v1.0.0`
   - Release title: `v1.0.0`
   - Description: Initial release
   - Publish release

2. **The GitHub Action will automatically**:
   - Run tests
   - Publish to NPM
   - Create release notes

## Step 7: Test NPX Installation

After publishing, test the NPX installation:

```bash
# Test NPX installation (use your actual package name)
npx mcp-process-image --help

# Test with a dummy OpenAI key (for testing CLI flow)
npx mcp-process-image install --openai-key sk-test-key-for-testing
```

## Step 8: Update Documentation

1. **Update README.md** with the correct NPX command:

   ```bash
   # Replace with your actual package name
   npx your-actual-package-name install --openai-key sk-your-key
   ```

2. **Create release notes** describing:
   - What the package does
   - How to install it
   - How to configure it with Claude Desktop

## Troubleshooting

### Common Issues

1. **Package name already exists**:

   - Use a scoped package: `@FarukNetworks/mcp-process-image`
   - Choose a different name

2. **NPM publish fails**:

   - Check you're logged in: `npm whoami`
   - Verify package.json is valid: `npm run prepublishOnly`
   - Check NPM token permissions

3. **GitHub Actions fail**:

   - Verify NPM_TOKEN secret is set correctly
   - Check the token has publish permissions

4. **Python installation fails**:
   - Ensure Python 3.10+ is available on target systems
   - Test on different platforms (Windows, macOS, Linux)

## Maintenance

### Updating the Package

1. **Make changes to the code**
2. **Update version**:
   ```bash
   npm version patch  # or minor/major
   ```
3. **Push changes**:
   ```bash
   git push && git push --tags
   ```
4. **Create a new GitHub release** (triggers auto-publish)

### Monitoring

- Monitor NPM download stats
- Check GitHub Issues for user problems
- Update dependencies regularly

## Security Considerations

- Never commit API keys to the repository
- Use environment variables for sensitive data
- Regularly update dependencies for security patches
- Consider adding vulnerability scanning to CI/CD

## Support

- Create GitHub Issues template
- Add contributing guidelines
- Set up discussions for community support
