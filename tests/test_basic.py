"""Basic tests for the MCP Image Processing Server."""

import pytest
from unittest.mock import Mock, patch

from mcp_process_image.models import APIProvider, AnalysisType, ServerConfig
from mcp_process_image.config import load_config, get_api_key, validate_api_key
from mcp_process_image.utils import is_url, is_base64_image


def test_api_provider_enum():
    """Test that API provider enum works correctly."""
    assert APIProvider.OPENAI == "openai"
    assert APIProvider.ANTHROPIC == "anthropic"
    assert APIProvider.GOOGLE == "google"
    assert APIProvider.AZURE == "azure"


def test_analysis_type_enum():
    """Test that analysis type enum works correctly."""
    assert AnalysisType.DESCRIPTION == "description"
    assert AnalysisType.OBJECTS == "objects"
    assert AnalysisType.TEXT == "text"
    assert AnalysisType.COMPREHENSIVE == "comprehensive"


def test_server_config_defaults():
    """Test that server config has reasonable defaults."""
    config = ServerConfig()
    assert config.default_api_provider == APIProvider.OPENAI
    assert config.max_image_size_mb == 10.0
    assert config.request_timeout == 30
    assert config.max_retries == 3
    assert config.rate_limit_per_minute == 60


def test_server_config_validation():
    """Test that server config validation works."""
    # Test valid values
    config = ServerConfig(max_image_size_mb=5.0, request_timeout=60)
    assert config.max_image_size_mb == 5.0
    assert config.request_timeout == 60

    # Test invalid values
    with pytest.raises(ValueError):
        ServerConfig(max_image_size_mb=0)

    with pytest.raises(ValueError):
        ServerConfig(max_image_size_mb=200)

    with pytest.raises(ValueError):
        ServerConfig(request_timeout=0)

    with pytest.raises(ValueError):
        ServerConfig(request_timeout=500)


@patch.dict(
    "os.environ",
    {
        "DEFAULT_API_PROVIDER": "anthropic",
        "MAX_IMAGE_SIZE_MB": "5.0",
        "OPENAI_API_KEY": "test-openai-key",
        "ANTHROPIC_API_KEY": "test-anthropic-key",
    },
)
def test_load_config():
    """Test loading configuration from environment variables."""
    config = load_config()
    assert config.default_api_provider == APIProvider.ANTHROPIC
    assert config.max_image_size_mb == 5.0
    assert config.openai_api_key == "test-openai-key"
    assert config.anthropic_api_key == "test-anthropic-key"


def test_get_api_key():
    """Test getting API keys for different providers."""
    config = ServerConfig(
        openai_api_key="openai-key",
        anthropic_api_key="anthropic-key",
        azure_api_key="azure-key",
    )

    # Test getting keys for each provider
    assert get_api_key(APIProvider.OPENAI, config) == "openai-key"
    assert get_api_key(APIProvider.ANTHROPIC, config) == "anthropic-key"
    assert get_api_key(APIProvider.AZURE, config) == "azure-key"
    assert get_api_key(APIProvider.GOOGLE, config) is None

    # Test override key
    assert get_api_key(APIProvider.OPENAI, config, "override-key") == "override-key"


def test_validate_api_key():
    """Test API key validation."""
    assert validate_api_key(APIProvider.OPENAI, "valid-key") is True
    assert validate_api_key(APIProvider.OPENAI, "   valid-key   ") is True
    assert validate_api_key(APIProvider.OPENAI, None) is False
    assert validate_api_key(APIProvider.OPENAI, "") is False
    assert validate_api_key(APIProvider.OPENAI, "   ") is False


def test_is_url():
    """Test URL detection utility."""
    assert is_url("https://example.com/image.jpg") is True
    assert is_url("http://example.com/image.png") is True
    assert is_url("ftp://example.com/file.jpg") is True
    assert is_url("example.com/image.jpg") is False
    assert is_url("/path/to/image.jpg") is False
    assert is_url("image.jpg") is False
    assert is_url("") is False


def test_is_base64_image():
    """Test base64 image detection utility."""
    # Data URL format
    assert is_base64_image("data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD") is True
    assert is_base64_image("data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA") is True

    # Plain base64 (basic test)
    assert (
        is_base64_image(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
        )
        is True
    )

    # Invalid base64
    assert is_base64_image("not-base64-data") is False
    assert is_base64_image("") is False
    assert is_base64_image("data:text/plain;base64,invalid") is False


if __name__ == "__main__":
    pytest.main([__file__])
