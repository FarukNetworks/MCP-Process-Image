"""Utility functions for image processing and validation."""

import base64
import io
import os
from pathlib import Path
from typing import Any, Dict, Tuple, Union
from urllib.parse import urlparse

import httpx
from PIL import Image

from .models import APIProvider


class ImageValidationError(Exception):
    """Raised when image validation fails."""

    pass


class ImageLoadError(Exception):
    """Raised when image loading fails."""

    pass


def validate_image_size(image_data: bytes, max_size_mb: float) -> None:
    """Validate that image size is within limits."""
    size_mb = len(image_data) / (1024 * 1024)
    if size_mb > max_size_mb:
        raise ImageValidationError(
            f"Image size {size_mb:.2f}MB exceeds maximum allowed size {max_size_mb}MB"
        )


def validate_image_format(image: Image.Image) -> None:
    """Validate that image format is supported."""
    supported_formats = {"JPEG", "PNG", "WebP", "GIF", "BMP", "TIFF"}
    if image.format not in supported_formats:
        raise ImageValidationError(
            f"Unsupported image format: {image.format}. "
            f"Supported formats: {', '.join(supported_formats)}"
        )


def is_url(source: str) -> bool:
    """Check if a string is a valid URL."""
    try:
        result = urlparse(source)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def is_base64_image(source: str) -> bool:
    """Check if a string is base64 encoded image data."""
    # Check for data URL format
    if source.startswith("data:image/"):
        return True

    # Check for plain base64 (basic validation)
    try:
        # Remove data URL prefix if present
        if "," in source:
            source = source.split(",", 1)[1]

        # Try to decode
        decoded = base64.b64decode(source, validate=True)
        return len(decoded) > 0
    except Exception:
        return False


def sanitize_file_path(file_path: str) -> Path:
    """Sanitize and validate file path to prevent directory traversal."""
    # Remove any potential directory traversal attempts
    clean_path = os.path.normpath(file_path)

    # Check for directory traversal patterns (but allow absolute paths)
    if ".." in clean_path:
        raise ImageValidationError(f"Invalid file path: {file_path}")

    path = Path(clean_path)

    # Ensure file exists and is readable
    if not path.exists():
        raise ImageLoadError(f"File not found: {file_path}")

    if not path.is_file():
        raise ImageLoadError(f"Path is not a file: {file_path}")

    return path


async def load_image_from_url(url: str, timeout: int = 30) -> bytes:
    """Load image data from a URL."""
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url)
            response.raise_for_status()

            # Check content type
            content_type = response.headers.get("content-type", "")
            if not content_type.startswith("image/"):
                raise ImageLoadError(f"URL does not point to an image: {content_type}")

            return response.content
    except httpx.RequestError as e:
        raise ImageLoadError(f"Failed to load image from URL: {e}")
    except httpx.HTTPStatusError as e:
        raise ImageLoadError(f"HTTP error loading image: {e.response.status_code}")


def load_image_from_base64(base64_data: str) -> bytes:
    """Load image data from base64 string."""
    try:
        # Handle data URL format
        if base64_data.startswith("data:image/"):
            # Extract base64 part after comma
            if "," in base64_data:
                base64_data = base64_data.split(",", 1)[1]

        return base64.b64decode(base64_data, validate=True)
    except Exception as e:
        raise ImageLoadError(f"Failed to decode base64 image data: {e}")


def load_image_from_file(file_path: Union[str, Path]) -> bytes:
    """Load image data from a file."""
    try:
        path = sanitize_file_path(str(file_path))
        return path.read_bytes()
    except Exception as e:
        raise ImageLoadError(f"Failed to load image from file: {e}")


async def load_image_data(source: str, timeout: int = 30) -> Tuple[bytes, str]:
    """Load image data from various sources and return data with source type."""
    if is_url(source):
        data = await load_image_from_url(source, timeout)
        return data, "url"
    elif is_base64_image(source):
        data = load_image_from_base64(source)
        return data, "base64"
    else:
        # Assume it's a file path
        data = load_image_from_file(source)
        return data, "file"


def validate_and_process_image(
    image_data: bytes, max_size_mb: float, resize_if_needed: bool = True
) -> Tuple[Image.Image, Dict[str, Any]]:
    """Validate and optionally resize image, return PIL Image and metadata."""
    try:
        # Validate size
        validate_image_size(image_data, max_size_mb)

        # Load image with PIL
        image = Image.open(io.BytesIO(image_data))

        # Ensure format is detected - if None, try to determine from image data
        if image.format is None:
            # Try to detect format from the image data header
            if image_data.startswith(b"\x89PNG"):
                image.format = "PNG"
            elif image_data.startswith(b"\xff\xd8\xff"):
                image.format = "JPEG"
            elif image_data.startswith(b"RIFF") and b"WEBP" in image_data[:12]:
                image.format = "WEBP"
            elif image_data.startswith(b"GIF8"):
                image.format = "GIF"
            else:
                # Default to PNG if we can't detect
                image.format = "PNG"

        # Validate format
        validate_image_format(image)

        # Get metadata
        metadata: Dict[str, Any] = {
            "width": image.width,
            "height": image.height,
            "format": image.format,
            "mode": image.mode,
            "size_bytes": len(image_data),
        }

        # Resize if image is too large and resize is enabled
        if resize_if_needed:
            max_dimension = 2048  # Most APIs have limits around this
            if image.width > max_dimension or image.height > max_dimension:
                # Calculate new size maintaining aspect ratio
                ratio = min(max_dimension / image.width, max_dimension / image.height)
                new_size = (int(image.width * ratio), int(image.height * ratio))
                image = image.resize(new_size, Image.Resampling.LANCZOS)
                metadata["resized"] = True
                metadata["original_size"] = (metadata["width"], metadata["height"])
                metadata["width"] = image.width
                metadata["height"] = image.height

        return image, metadata

    except Exception as e:
        if isinstance(e, (ImageValidationError, ImageLoadError)):
            raise
        raise ImageValidationError(f"Failed to process image: {e}")


def image_to_base64(image: Image.Image, format: str = "JPEG") -> str:
    """Convert PIL Image to base64 string."""
    buffer = io.BytesIO()

    # Convert RGBA to RGB for JPEG
    if format.upper() == "JPEG" and image.mode == "RGBA":
        # Create white background
        background = Image.new("RGB", image.size, (255, 255, 255))
        background.paste(image, mask=image.split()[-1])  # Use alpha channel as mask
        image = background

    image.save(buffer, format=format)
    buffer.seek(0)

    image_data = buffer.getvalue()
    base64_data = base64.b64encode(image_data).decode("utf-8")

    return f"data:image/{format.lower()};base64,{base64_data}"


def get_provider_image_limits(provider: APIProvider) -> Dict[str, Any]:
    """Get image size and format limits for each provider."""
    limits: Dict[APIProvider, Dict[str, Any]] = {
        APIProvider.OPENAI: {
            "max_size_mb": 20,
            "max_dimension": 2048,
            "supported_formats": ["JPEG", "PNG", "WebP", "GIF"],
        },
        APIProvider.ANTHROPIC: {
            "max_size_mb": 5,
            "max_dimension": 1568,
            "supported_formats": ["JPEG", "PNG", "WebP", "GIF"],
        },
        APIProvider.GOOGLE: {
            "max_size_mb": 20,
            "max_dimension": 4096,
            "supported_formats": ["JPEG", "PNG", "WebP", "GIF", "BMP", "TIFF"],
        },
        APIProvider.AZURE: {
            "max_size_mb": 4,
            "max_dimension": 4200,
            "supported_formats": ["JPEG", "PNG", "BMP", "GIF"],
        },
    }

    return limits.get(provider, limits[APIProvider.OPENAI])
