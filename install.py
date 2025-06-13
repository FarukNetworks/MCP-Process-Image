#!/usr/bin/env python3
"""Installation script for MCP Process Image Server."""

import os
import sys
import subprocess
from pathlib import Path


def run_command(command: str, description: str) -> bool:
    """Run a command and return success status."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(
            command, shell=True, check=True, capture_output=True, text=True
        )
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        if e.stdout:
            print(f"stdout: {e.stdout}")
        if e.stderr:
            print(f"stderr: {e.stderr}")
        return False


def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 9):
        print("❌ Python 3.9 or higher is required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} is compatible")
    return True


def check_uv_installed():
    """Check if uv is installed."""
    try:
        subprocess.run(["uv", "--version"], check=True, capture_output=True)
        print("✅ uv is already installed")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  uv is not installed")
        return False


def install_uv():
    """Install uv package manager."""
    print("🔄 Installing uv...")
    try:
        if sys.platform == "win32":
            command = 'powershell -c "irm https://astral.sh/uv/install.ps1 | iex"'
        else:
            command = "curl -LsSf https://astral.sh/uv/install.sh | sh"

        subprocess.run(command, shell=True, check=True)
        print("✅ uv installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install uv")
        return False


def install_dependencies():
    """Install project dependencies."""
    return run_command("uv sync --all-extras", "Installing dependencies")


def create_env_file():
    """Create environment file from example."""
    env_file = Path(".env")
    example_file = Path("example.env")

    if env_file.exists():
        print("✅ .env file already exists")
        return True

    if example_file.exists():
        try:
            env_file.write_text(example_file.read_text())
            print("✅ Created .env file from example")
            print("⚠️  Please edit .env file and add your API keys")
            return True
        except Exception as e:
            print(f"❌ Failed to create .env file: {e}")
            return False
    else:
        print("⚠️  example.env file not found, creating basic .env file")
        env_content = """# Default API provider (openai, anthropic, google, azure)
DEFAULT_API_PROVIDER=openai

# API Keys - Replace with your actual keys
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
"""
        try:
            env_file.write_text(env_content)
            print("✅ Created basic .env file")
            print("⚠️  Please edit .env file and add your API keys")
            return True
        except Exception as e:
            print(f"❌ Failed to create .env file: {e}")
            return False


def test_installation():
    """Test the installation by running basic checks."""
    print("🔄 Testing installation...")

    # Test import
    try:
        import mcp_process_image

        print("✅ Package imports successfully")
    except ImportError as e:
        print(f"❌ Failed to import package: {e}")
        return False

    # Test server creation
    try:
        from mcp_process_image.server import create_server

        server = create_server()
        print("✅ Server creates successfully")
    except Exception as e:
        print(f"❌ Failed to create server: {e}")
        return False

    return True


def main():
    """Main installation process."""
    print("🚀 MCP Process Image Server Installation")
    print("=" * 50)

    # Check Python version
    if not check_python_version():
        sys.exit(1)

    # Check/install uv
    if not check_uv_installed():
        if not install_uv():
            print(
                "❌ Please install uv manually: https://docs.astral.sh/uv/getting-started/installation/"
            )
            sys.exit(1)

    # Install dependencies
    if not install_dependencies():
        sys.exit(1)

    # Create environment file
    if not create_env_file():
        sys.exit(1)

    # Test installation
    if not test_installation():
        print("⚠️  Installation completed but tests failed")
        print("   Please check your configuration and dependencies")
    else:
        print("✅ Installation completed successfully!")

    print("\n" + "=" * 50)
    print("📋 Next Steps:")
    print("1. Edit .env file and add your API keys")
    print("2. Run the server: uv run python -m mcp_process_image.server")
    print(
        "3. Or install in Claude Desktop: mcp install src/mcp_process_image/server.py"
    )
    print("\n📖 See README.md for detailed usage instructions")


if __name__ == "__main__":
    main()
