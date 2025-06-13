# MCP Process Image Server

A Model Context Protocol (MCP) server for processing images using various AI vision APIs. This server provides tools to analyze images, extract text, detect objects, and generate descriptions using multiple AI providers.

## Features

- **Multiple AI Providers**: Support for OpenAI GPT-4 Vision, Anthropic Claude Vision, Google Vision API, and Azure Computer Vision
- **Flexible Input**: Accept images via file paths, URLs, or base64 encoded data
- **Comprehensive Analysis**: Image description, object detection, OCR, and more
- **Batch Processing**: Process multiple images efficiently
- **Error Handling**: Robust error handling with retry logic and fallback options
- **Rate Limiting**: Built-in rate limiting to respect API quotas
- **Secure**: Proper API key management and input validation
- **Easy Installation**: Install via NPX on any machine with automatic setup

## Quick Start (NPX Installation)

The easiest way to install and use MCP Process Image is via NPX:

```bash
# Install and configure with your OpenAI API key
npx mcp-process-image install --openai-key sk-your-openai-api-key

# Check installation status
npx mcp-process-image status

# View configuration for Claude Desktop
npx mcp-process-image config
```

### What the NPX installer does:

1. **Checks Python**: Verifies Python 3.10+ is installed
2. **Creates Environment**: Sets up an isolated Python virtual environment
3. **Installs Dependencies**: Downloads and installs all required Python packages
4. **Generates Configuration**: Creates MCP configuration with your API key
5. **Provides Instructions**: Shows you how to add it to Claude Desktop

### Adding to Claude Desktop

After installation, copy the generated configuration to your Claude Desktop MCP settings:

1. Open Claude Desktop
2. Go to Settings → MCP
3. Add the configuration shown by `npx mcp-process-image config`
4. Restart Claude Desktop

## Alternative Installation Methods

### Using uv (for Python developers)

```bash
uv add mcp-process-image
```

### Using pip

```bash
pip install mcp-process-image
```

### Development Installation

```bash
git clone https://github.com/FarukNetworks/mcp-process-image.git
cd mcp-process-image
npm install

# Install MCP server in development mode
npm run dev:install -- --openai-key sk-your-openai-api-key

# Or use the development script directly
node scripts/dev-install.js --openai-key sk-your-openai-api-key
```

**Note**: When working with the cloned repository, use the development commands instead of `npx mcp-process-image`. See [DEVELOPMENT.md](DEVELOPMENT.md) for detailed instructions.

## NPX Commands

The NPX package provides several commands for managing your MCP Process Image installation:

```bash
# Install and configure
npx mcp-process-image install --openai-key sk-your-key

# Show current configuration
npx mcp-process-image config

# Update OpenAI API key
npx mcp-process-image config --openai-key sk-new-key

# Check installation status
npx mcp-process-image status

# Start server for testing
npx mcp-process-image start

# Uninstall
npx mcp-process-image uninstall

# Show help
npx mcp-process-image --help
```

## Configuration

### Environment Variables (for manual setup)

Create a `.env` file in your project root:

```env
# Default API provider (openai, anthropic, google, azure)
DEFAULT_API_PROVIDER=openai

# API Keys
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GOOGLE_APPLICATION_CREDENTIALS=/path/to/google/credentials.json
AZURE_COMPUTER_VISION_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
AZURE_COMPUTER_VISION_KEY=your_azure_key_here

# Optional: Rate limiting and timeouts
MAX_IMAGE_SIZE_MB=10
REQUEST_TIMEOUT=30
MAX_RETRIES=3
RATE_LIMIT_PER_MINUTE=60
```

## Usage

### Running the Server

```bash
# Using stdio transport (default)
mcp-process-image

# Using SSE transport on custom port
mcp-process-image --transport sse --port 8000

# Development mode
uv run mcp dev src/mcp_process_image/server.py
```

### Installing in Claude Desktop

```bash
mcp install src/mcp_process_image/server.py --name "Image Processor"
```

### Available Tools

#### `process_image`

Analyze an image and return comprehensive results.

**Parameters:**

- `image_source` (str): File path, URL, or base64 encoded image
- `api_provider` (str, optional): API provider to use (openai, anthropic, google, azure)
- `api_key` (str, optional): API key for the provider
- `analysis_type` (str, optional): Type of analysis (description, objects, text, comprehensive)

**Example:**

```python
result = await session.call_tool("process_image", {
    "image_source": "/path/to/image.jpg",
    "api_provider": "openai",
    "analysis_type": "comprehensive"
})
```

#### `analyze_image_batch`

Process multiple images in batch.

**Parameters:**

- `image_sources` (list[str]): List of image sources
- `api_provider` (str, optional): API provider to use
- `api_key` (str, optional): API key for the provider
- `analysis_type` (str, optional): Type of analysis

#### `extract_text`

Extract text from images using OCR.

**Parameters:**

- `image_source` (str): Image source
- `api_provider` (str, optional): API provider to use
- `api_key` (str, optional): API key for the provider

#### `detect_objects`

Detect and identify objects in images.

**Parameters:**

- `image_source` (str): Image source
- `api_provider` (str, optional): API provider to use
- `api_key` (str, optional): API key for the provider

### Available Resources

#### `config://supported-apis`

Returns list of supported API providers and their capabilities.

#### `config://api-capabilities`

Returns detailed capabilities of each API provider.

#### `schema://analysis-result`

Returns JSON schema for analysis results.

## API Providers

### OpenAI GPT-4 Vision

- **Capabilities**: Image description, object detection, text extraction, scene analysis
- **Requirements**: OpenAI API key
- **Rate Limits**: Varies by plan

### Anthropic Claude Vision

- **Capabilities**: Image description, detailed analysis, text extraction
- **Requirements**: Anthropic API key
- **Rate Limits**: Varies by plan

### Google Vision API

- **Capabilities**: OCR, object detection, face detection, landmark detection
- **Requirements**: Google Cloud credentials
- **Rate Limits**: Varies by plan

### Azure Computer Vision

- **Capabilities**: OCR, object detection, image analysis, face detection
- **Requirements**: Azure endpoint and API key
- **Rate Limits**: Varies by plan

## Response Format

All tools return structured responses in the following format:

```json
{
    "success": true,
    "provider": "openai",
    "analysis": {
        "description": "A detailed description of the image",
        "objects": [
            {
                "name": "object_name",
                "confidence": 0.95,
                "bounding_box": [x, y, width, height]
            }
        ],
        "text": [
            {
                "content": "extracted text",
                "confidence": 0.98,
                "bounding_box": [x, y, width, height]
            }
        ],
        "metadata": {
            "image_size": [width, height],
            "format": "JPEG",
            "processing_time": 1.23
        }
    },
    "error": null
}
```

## Error Handling

The server includes comprehensive error handling for:

- Invalid image formats or corrupted files
- Network connectivity issues
- API rate limiting and quota exceeded
- Authentication errors
- Malformed requests
- File system access issues

## Development

### Running Tests

```bash
uv run pytest
```

### Code Formatting

```bash
uv run ruff format .
uv run ruff check .
```

### Type Checking

```bash
uv run pyright
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

For issues and questions, please open an issue on the GitHub repository.
