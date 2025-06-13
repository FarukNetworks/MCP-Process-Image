"""Base abstract class for image processing API clients."""

import time
import uuid
from abc import ABC, abstractmethod
from typing import Any, Dict, List

from PIL import Image

from ..models import (
    AnalysisType,
    APIProvider,
    DetectedObject,
    ExtractedText,
    ImageAnalysis,
    ImageMetadata,
    ProcessingResult,
)


class BaseImageClient(ABC):
    """Abstract base class for image processing API clients."""

    def __init__(self, api_key: str, timeout: int = 30, max_retries: int = 3):
        """Initialize the client with API key and configuration."""
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries

    @property
    @abstractmethod
    def provider(self) -> APIProvider:
        """Return the API provider type."""
        pass

    @property
    @abstractmethod
    def supported_analysis_types(self) -> List[AnalysisType]:
        """Return list of supported analysis types."""
        pass

    @property
    @abstractmethod
    def max_image_size_mb(self) -> float:
        """Return maximum supported image size in MB."""
        pass

    @property
    @abstractmethod
    def supported_formats(self) -> List[str]:
        """Return list of supported image formats."""
        pass

    @abstractmethod
    async def analyze_image(
        self,
        image: Image.Image,
        analysis_type: AnalysisType = AnalysisType.COMPREHENSIVE,
        **kwargs: Any,
    ) -> ImageAnalysis:
        """Analyze an image and return structured results."""
        pass

    @abstractmethod
    async def describe_image(self, image: Image.Image, **kwargs: Any) -> str:
        """Generate a description of the image."""
        pass

    @abstractmethod
    async def extract_text(
        self, image: Image.Image, **kwargs: Any
    ) -> List[ExtractedText]:
        """Extract text from the image using OCR."""
        pass

    @abstractmethod
    async def detect_objects(
        self, image: Image.Image, **kwargs: Any
    ) -> List[DetectedObject]:
        """Detect objects in the image."""
        pass

    async def process_image(
        self,
        image: Image.Image,
        image_metadata: Dict[str, Any],
        analysis_type: AnalysisType = AnalysisType.COMPREHENSIVE,
        **kwargs: Any,
    ) -> ProcessingResult:
        """Process an image and return complete results with error handling."""
        start_time = time.time()
        request_id = str(uuid.uuid4())

        try:
            # Create metadata object
            metadata = ImageMetadata(
                width=image_metadata["width"],
                height=image_metadata["height"],
                format=image_metadata["format"],
                size_bytes=image_metadata.get("size_bytes", 0),
                processing_time=0.0,  # Will be updated below
                api_provider=self.provider,
            )

            # Perform analysis
            analysis = await self.analyze_image(image, analysis_type, **kwargs)

            # Update processing time
            processing_time = time.time() - start_time
            metadata.processing_time = processing_time
            analysis.metadata = metadata

            return ProcessingResult(
                success=True,
                provider=self.provider,
                analysis=analysis,
                error=None,
                request_id=request_id,
                timestamp=time.time(),
            )

        except Exception as e:
            processing_time = time.time() - start_time
            return ProcessingResult(
                success=False,
                provider=self.provider,
                analysis=None,
                error=str(e),
                request_id=request_id,
                timestamp=time.time(),
            )

    def validate_image(self, image: Image.Image) -> None:
        """Validate that the image meets the client's requirements."""
        # Get the image format, handling cases where PIL couldn't detect it
        image_format = image.format

        # If PIL couldn't detect the format, try to determine it from the image data
        if image_format is None:
            # Try to get format from the image's internal data or use a reasonable default
            # This handles cases where PIL loads the image but can't determine the format
            if hasattr(image, "_getexif") or image.mode in ["RGB", "RGBA"]:
                # Likely a JPEG if it has EXIF or is RGB
                image_format = "JPEG"
            elif image.mode in ["P", "L"]:
                # Likely PNG for palette or grayscale
                image_format = "PNG"
            else:
                # Default to JPEG for unknown formats
                image_format = "JPEG"

        # Check format against supported formats
        if image_format not in self.supported_formats:
            raise ValueError(
                f"Unsupported image format: {image_format}. "
                f"Supported formats: {', '.join(self.supported_formats)}"
            )

        # Check size (approximate)
        # This is a rough estimate since we don't have the exact file size
        estimated_size_mb = (image.width * image.height * 3) / (
            1024 * 1024
        )  # Assume RGB
        if estimated_size_mb > self.max_image_size_mb:
            raise ValueError(
                f"Image too large: ~{estimated_size_mb:.1f}MB. "
                f"Maximum size: {self.max_image_size_mb}MB"
            )

    def _create_error_result(self, error_message: str) -> ProcessingResult:
        """Create a standardized error result."""
        return ProcessingResult(
            success=False,
            provider=self.provider,
            analysis=None,
            error=error_message,
            request_id=str(uuid.uuid4()),
            timestamp=time.time(),
        )
