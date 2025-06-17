"""Main MCP server for image processing."""

import json
import time
import uuid
from typing import Any, List, Optional

from mcp.server.fastmcp import Context, FastMCP

from .api_clients.openai_client import OpenAIImageClient
from .config import get_api_key, get_supported_providers, load_config
from .models import (
    APICapability,
    APIProvider,
    AnalysisType,
    BatchProcessingResult,
    ProcessingResult,
    ServerConfig,
)
from .utils import (
    ImageLoadError,
    ImageValidationError,
    load_image_data,
    validate_and_process_image,
)

# Global configuration
config: ServerConfig = load_config()

# Create MCP server
mcp = FastMCP("Image Processor")


def create_api_client(provider: APIProvider, api_key: str) -> Any:
    """Create an API client for the specified provider."""
    if provider == APIProvider.OPENAI:
        return OpenAIImageClient(api_key, config.request_timeout, config.max_retries)
    else:
        raise ValueError(f"Unsupported API provider: {provider}")


@mcp.resource("config://supported-apis")
def get_supported_apis() -> str:
    """Get list of supported API providers and their status."""
    supported = get_supported_providers(config)

    api_info: List[dict[str, Any]] = []
    for provider in APIProvider:
        status = "available" if provider in supported else "no_api_key"
        api_info.append(
            {
                "provider": provider.value,
                "status": status,
                "description": _get_provider_description(provider),
            }
        )

    return json.dumps(api_info, indent=2)


@mcp.resource("config://api-capabilities")
def get_api_capabilities() -> str:
    """Get detailed capabilities of each API provider."""
    capabilities: List[dict[str, Any]] = []

    for provider in APIProvider:
        if provider == APIProvider.OPENAI:
            capability = APICapability(
                provider=provider,
                supports_description=True,
                supports_objects=True,
                supports_text=True,
                supports_faces=False,
                supports_landmarks=False,
                max_image_size_mb=20.0,
                supported_formats=["JPEG", "PNG", "WebP", "GIF"],
                rate_limit_per_minute=60,
            )
        else:
            # Placeholder for other providers
            capability = APICapability(
                provider=provider,
                supports_description=False,
                supports_objects=False,
                supports_text=False,
                supports_faces=False,
                supports_landmarks=False,
                max_image_size_mb=0.0,
                supported_formats=[],
                rate_limit_per_minute=None,
            )

        capabilities.append(capability.model_dump())

    return json.dumps(capabilities, indent=2)


@mcp.resource("schema://analysis-result")
def get_analysis_schema() -> str:
    """Get JSON schema for analysis results."""
    schema = {
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "provider": {"type": "string", "enum": [p.value for p in APIProvider]},
            "analysis": {
                "type": "object",
                "properties": {
                    "description": {"type": "string"},
                    "objects": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "confidence": {
                                    "type": "number",
                                    "minimum": 0,
                                    "maximum": 1,
                                },
                                "bounding_box": {
                                    "type": "object",
                                    "properties": {
                                        "x": {"type": "number"},
                                        "y": {"type": "number"},
                                        "width": {"type": "number"},
                                        "height": {"type": "number"},
                                    },
                                },
                            },
                        },
                    },
                    "text": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "content": {"type": "string"},
                                "confidence": {
                                    "type": "number",
                                    "minimum": 0,
                                    "maximum": 1,
                                },
                                "bounding_box": {
                                    "type": "object",
                                    "properties": {
                                        "x": {"type": "number"},
                                        "y": {"type": "number"},
                                        "width": {"type": "number"},
                                        "height": {"type": "number"},
                                    },
                                },
                            },
                        },
                    },
                    "metadata": {
                        "type": "object",
                        "properties": {
                            "width": {"type": "integer"},
                            "height": {"type": "integer"},
                            "format": {"type": "string"},
                            "processing_time": {"type": "number"},
                        },
                    },
                },
            },
            "error": {"type": "string"},
        },
        "required": ["success", "provider"],
    }

    return json.dumps(schema, indent=2)


@mcp.tool()
async def process_image(
    image_source: str,
    api_provider: Optional[str] = None,
    api_key: Optional[str] = None,
    analysis_type: Optional[str] = None,
    prompt: Optional[str] = None,
    ctx: Optional[Context] = None,
) -> str:
    """
    Analyze an image and return comprehensive results.

    Args:
        image_source: Full absolute file path, URL, or base64 encoded image.
                     For file paths, always provide the complete absolute path
                     (e.g., /Users/username/path/to/image.jpg) to ensure proper file loading.
        api_provider: API provider to use (openai, anthropic, google, azure)
        api_key: API key for the provider (optional if configured)
        analysis_type: Type of analysis (description, objects, text, comprehensive)
        prompt: Custom prompt to guide the analysis. If provided, this will override the default
                analysis behavior and use your specific instructions for what to analyze or extract
                from the image. Examples: "Count all the people in this image", "Describe the UI/UX
                issues in this interface", "Extract only the prices from this menu"

    Returns:
        JSON string with analysis results
    """
    request_id = str(uuid.uuid4())

    try:
        # Validate and set defaults
        provider = APIProvider(api_provider or config.default_api_provider.value)
        analysis = AnalysisType(analysis_type or AnalysisType.COMPREHENSIVE.value)

        # Get API key
        effective_api_key = get_api_key(provider, config, api_key)
        if not effective_api_key:
            raise ValueError(f"No API key available for provider: {provider.value}")

        # Report progress
        if ctx:
            await ctx.info(f"Loading image from: {image_source}")

        # Load and validate image
        image_data, _ = await load_image_data(image_source, config.request_timeout)
        image, metadata = validate_and_process_image(
            image_data, config.max_image_size_mb
        )

        if ctx:
            await ctx.info(
                f"Processing {metadata['width']}x{metadata['height']} {metadata['format']} image"
            )

        # Create API client and process image
        client = create_api_client(provider, effective_api_key)

        # If custom prompt is provided, use it for analysis
        if prompt:
            result = await client.analyze_with_custom_prompt(image, metadata, prompt)
        else:
            result = await client.process_image(image, metadata, analysis)

        if ctx:
            await ctx.info(
                f"Analysis completed in {result.analysis.metadata.processing_time:.2f}s"
                if result.analysis
                else "Analysis failed"
            )

        return json.dumps(result.model_dump(), indent=2)

    except (ImageLoadError, ImageValidationError) as e:
        error_result = ProcessingResult(
            success=False,
            provider=APIProvider(api_provider or config.default_api_provider.value),
            analysis=None,
            error=str(e),
            request_id=request_id,
            timestamp=time.time(),
        )
        return json.dumps(error_result.model_dump(), indent=2)

    except Exception as e:
        error_result = ProcessingResult(
            success=False,
            provider=APIProvider(api_provider or config.default_api_provider.value),
            analysis=None,
            error=f"Unexpected error: {str(e)}",
            request_id=request_id,
            timestamp=time.time(),
        )
        return json.dumps(error_result.model_dump(), indent=2)


@mcp.tool()
async def analyze_image_batch(
    image_sources: List[str],
    api_provider: Optional[str] = None,
    api_key: Optional[str] = None,
    analysis_type: Optional[str] = None,
    prompt: Optional[str] = None,
    ctx: Optional[Context] = None,
) -> str:
    """
    Process multiple images in batch.

    Args:
        image_sources: List of image sources (full absolute file paths, URLs, or base64 data).
                      For file paths, always provide complete absolute paths
                      (e.g., ['/Users/username/path/to/image1.jpg', '/Users/username/path/to/image2.png'])
                      to ensure proper file loading.
        api_provider: API provider to use
        api_key: API key for the provider
        analysis_type: Type of analysis to perform
        prompt: Custom prompt to guide the analysis for all images. If provided, this will override
                the default analysis behavior and use your specific instructions for what to analyze
                or extract from each image. Examples: "Count all the people in each image",
                "Identify the main product in each image", "Extract all text from each image"

    Returns:
        JSON string with batch processing results
    """
    start_time = time.time()
    results: List[ProcessingResult] = []
    successful = 0
    failed = 0

    try:
        # Validate inputs
        provider = APIProvider(api_provider or config.default_api_provider.value)
        analysis = AnalysisType(analysis_type or AnalysisType.COMPREHENSIVE.value)

        # Get API key
        effective_api_key = get_api_key(provider, config, api_key)
        if not effective_api_key:
            raise ValueError(f"No API key available for provider: {provider.value}")

        # Create API client
        client = create_api_client(provider, effective_api_key)

        total_images = len(image_sources)
        if ctx:
            await ctx.info(f"Processing {total_images} images")

        # Process each image
        for i, image_source in enumerate(image_sources):
            try:
                if ctx:
                    await ctx.report_progress(i, total_images)
                    await ctx.info(
                        f"Processing image {i+1}/{total_images}: {image_source}"
                    )

                # Load and validate image
                image_data, _ = await load_image_data(
                    image_source, config.request_timeout
                )
                image, metadata = validate_and_process_image(
                    image_data, config.max_image_size_mb
                )

                # Process image with custom prompt if provided
                if prompt:
                    result = await client.analyze_with_custom_prompt(
                        image, metadata, prompt
                    )
                else:
                    result = await client.process_image(image, metadata, analysis)

                results.append(result)

                if result.success:
                    successful += 1
                else:
                    failed += 1

            except Exception as e:
                error_result = ProcessingResult(
                    success=False,
                    provider=provider,
                    analysis=None,
                    error=str(e),
                    request_id=str(uuid.uuid4()),
                    timestamp=time.time(),
                )
                results.append(error_result)
                failed += 1

        # Create batch result
        batch_result = BatchProcessingResult(
            total_images=total_images,
            successful=successful,
            failed=failed,
            results=results,
            processing_time=time.time() - start_time,
        )

        if ctx:
            await ctx.info(
                f"Batch processing completed: {successful} successful, {failed} failed"
            )

        return json.dumps(batch_result.model_dump(), indent=2)

    except Exception as e:
        error_result = BatchProcessingResult(
            total_images=len(image_sources),
            successful=0,
            failed=len(image_sources),
            results=[],
            processing_time=time.time() - start_time,
        )
        return json.dumps(error_result.model_dump(), indent=2)


@mcp.tool()
async def extract_text(
    image_source: str,
    api_provider: Optional[str] = None,
    api_key: Optional[str] = None,
    prompt: Optional[str] = None,
    ctx: Optional[Context] = None,
) -> str:
    """
    Extract text from images using OCR.

    Args:
        image_source: Full absolute file path, URL, or base64 encoded image.
                     For file paths, always provide the complete absolute path
                     (e.g., /Users/username/path/to/image.jpg) to ensure proper file loading.
        api_provider: API provider to use
        api_key: API key for the provider
        prompt: Custom prompt to guide text extraction. If provided, this will override the default
                text extraction behavior. Examples: "Extract only the prices", "Find all email addresses",
                "Get the main heading text", "Extract text in a specific language"

    Returns:
        JSON string with extracted text results
    """
    return await process_image(
        image_source=image_source,
        api_provider=api_provider,
        api_key=api_key,
        analysis_type=AnalysisType.TEXT.value,
        prompt=prompt,
        ctx=ctx,
    )


@mcp.tool()
async def detect_objects(
    image_source: str,
    api_provider: Optional[str] = None,
    api_key: Optional[str] = None,
    prompt: Optional[str] = None,
    ctx: Optional[Context] = None,
) -> str:
    """
    Detect and identify objects in images.

    Args:
        image_source: Full absolute file path, URL, or base64 encoded image.
                     For file paths, always provide the complete absolute path
                     (e.g., /Users/username/path/to/image.jpg) to ensure proper file loading.
        api_provider: API provider to use
        api_key: API key for the provider
        prompt: Custom prompt to guide object detection. If provided, this will override the default
                object detection behavior. Examples: "Count all the cars", "Find only electronic devices",
                "Identify all UI elements", "Detect people and their activities"

    Returns:
        JSON string with object detection results
    """
    return await process_image(
        image_source=image_source,
        api_provider=api_provider,
        api_key=api_key,
        analysis_type=AnalysisType.OBJECTS.value,
        prompt=prompt,
        ctx=ctx,
    )


def _get_provider_description(provider: APIProvider) -> str:
    """Get description for an API provider."""
    descriptions = {
        APIProvider.OPENAI: "OpenAI GPT-4 Vision - Advanced image analysis and description",
        APIProvider.ANTHROPIC: "Anthropic Claude Vision - Detailed image understanding",
        APIProvider.GOOGLE: "Google Vision API - OCR, object detection, and more",
        APIProvider.AZURE: "Azure Computer Vision - Comprehensive image analysis",
    }
    return descriptions.get(provider, "Unknown provider")


def create_server() -> FastMCP:
    """Create and return the MCP server instance."""
    return mcp


def main() -> None:
    """Main entry point for the server."""
    mcp.run()


if __name__ == "__main__":
    main()
