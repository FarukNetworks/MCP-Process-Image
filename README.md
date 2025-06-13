# MCP Process Image Server

A Model Context Protocol (MCP) server for processing images using various AI vision APIs. This server provides tools to analyze images, extract text, detect objects, and generate descriptions using multiple AI providers.

## STEP 1: Clone the repository

Clone the git repository

```
git clone https://github.com/FarukNetworks/MCP-Process-Image
```

Navigate to the MCP-Process-Image folder

```
cd MCP-Process-Image
```

## STEP 2: Install dependencies

```
npm install
```

## STEP 3: Install the development environment

```
npm run dev:install -- --openai-key YOUR_KEY_HERE
```

## STEP 4: Add MCP to your mcp agent configuration

Get the mcp.json file

```
npx mcp-process-image config
```
