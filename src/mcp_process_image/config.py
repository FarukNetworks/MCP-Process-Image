"""Configuration management for the image processing server."""

import os
from typing import Optional

from dotenv import load_dotenv

from .models import APIProvider, ServerConfig

# Load environment variables from .env file
load_dotenv()


def load_config() -> ServerConfig:
    """Load configuration from environment variables."""
    return ServerConfig(
        default_api_provider=APIProvider(
            os.getenv("DEFAULT_API_PROVIDER", APIProvider.OPENAI.value)
        ),
        max_image_size_mb=float(os.getenv("MAX_IMAGE_SIZE_MB", "10.0")),
        request_timeout=int(os.getenv("REQUEST_TIMEOUT", "30")),
        max_retries=int(os.getenv("MAX_RETRIES", "3")),
        rate_limit_per_minute=int(os.getenv("RATE_LIMIT_PER_MINUTE", "60")),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        google_credentials_path=os.getenv("GOOGLE_APPLICATION_CREDENTIALS"),
        azure_endpoint=os.getenv("AZURE_COMPUTER_VISION_ENDPOINT"),
        azure_api_key=os.getenv("AZURE_COMPUTER_VISION_KEY"),
    )


def get_api_key(
    provider: APIProvider, config: ServerConfig, override_key: Optional[str] = None
) -> Optional[str]:
    """Get API key for a specific provider."""
    if override_key:
        return override_key

    if provider == APIProvider.OPENAI:
        return config.openai_api_key
    elif provider == APIProvider.ANTHROPIC:
        return config.anthropic_api_key
    elif provider == APIProvider.GOOGLE:
        return config.google_credentials_path
    elif provider == APIProvider.AZURE:
        return config.azure_api_key

    return None


def validate_api_key(provider: APIProvider, api_key: Optional[str]) -> bool:
    """Validate that an API key is present for the given provider."""
    if not api_key:
        return False

    # Basic validation - just check if key is not empty
    # More sophisticated validation could be added here
    return len(api_key.strip()) > 0


def get_supported_providers(config: ServerConfig) -> list[APIProvider]:
    """Get list of providers that have valid API keys configured."""
    supported = []

    for provider in APIProvider:
        api_key = get_api_key(provider, config)
        if validate_api_key(provider, api_key):
            supported.append(provider)

    return supported
