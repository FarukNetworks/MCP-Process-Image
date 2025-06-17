"""OpenAI GPT-4 Vision API client implementation."""

import json
import time
import uuid
from typing import Any, Dict, List

import openai
from PIL import Image
from tenacity import retry, stop_after_attempt, wait_exponential

from ..models import (
    AnalysisType,
    APIProvider,
    DetectedObject,
    ExtractedText,
    ImageAnalysis,
    ImageMetadata,
    ProcessingResult,
)
from ..utils import image_to_base64
from .base import BaseImageClient


class OpenAIImageClient(BaseImageClient):
    """OpenAI GPT-4 Vision API client for image processing."""

    def __init__(self, api_key: str, timeout: int = 30, max_retries: int = 3):
        """Initialize OpenAI client."""
        super().__init__(api_key, timeout, max_retries)
        self.client = openai.AsyncOpenAI(api_key=api_key, timeout=timeout)

    @property
    def provider(self) -> APIProvider:
        """Return the API provider type."""
        return APIProvider.OPENAI

    @property
    def supported_analysis_types(self) -> List[AnalysisType]:
        """Return list of supported analysis types."""
        return [
            AnalysisType.DESCRIPTION,
            AnalysisType.OBJECTS,
            AnalysisType.TEXT,
            AnalysisType.COMPREHENSIVE,
        ]

    @property
    def max_image_size_mb(self) -> float:
        """Return maximum supported image size in MB."""
        return 20.0

    @property
    def supported_formats(self) -> List[str]:
        """Return list of supported image formats."""
        return ["JPEG", "PNG", "WebP", "GIF"]

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True,
    )
    async def _make_api_call(
        self, messages: List[Dict[str, Any]], **kwargs: Any
    ) -> str:
        """Make API call to OpenAI with retry logic."""
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o",  # Use GPT-4o which supports vision
                messages=messages,
                max_tokens=16000,
                **kwargs,
            )

            if not response.choices:
                raise ValueError("No response from OpenAI API")

            content = response.choices[0].message.content
            if not content:
                raise ValueError("Empty response from OpenAI API")

            return content

        except openai.RateLimitError as e:
            raise ValueError(f"OpenAI rate limit exceeded: {e}")
        except openai.AuthenticationError as e:
            raise ValueError(f"OpenAI authentication failed: {e}")
        except openai.APIError as e:
            raise ValueError(f"OpenAI API error: {e}")
        except Exception as e:
            raise ValueError(f"Unexpected error calling OpenAI API: {e}")

    async def describe_image(self, image: Image.Image, **kwargs: Any) -> str:
        """Generate a description of the image."""
        self.validate_image(image)

        # Convert image to base64
        image_data = image_to_base64(image, "JPEG")

        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Please provide a detailed description of this image. Focus on the main subjects, setting, colors, composition, and any notable details.",
                    },
                    {"type": "image_url", "image_url": {"url": image_data}},
                ],
            }
        ]

        return await self._make_api_call(messages, **kwargs)

    async def extract_text(
        self, image: Image.Image, **kwargs: Any
    ) -> List[ExtractedText]:
        """Extract text from the image using OCR."""
        self.validate_image(image)

        # Convert image to base64
        image_data = image_to_base64(image, "JPEG")

        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Please extract all visible text from this image. Return the results as a JSON array where each item has 'content' (the text) and 'confidence' (estimated confidence from 0.0 to 1.0). If no text is found, return an empty array.",
                    },
                    {"type": "image_url", "image_url": {"url": image_data}},
                ],
            }
        ]

        response = await self._make_api_call(messages, **kwargs)

        try:
            # Try to parse JSON response
            text_data = json.loads(response)
            if not isinstance(text_data, list):
                # If not a list, treat the whole response as text
                return [ExtractedText(content=response, confidence=0.8)]

            extracted_texts = []
            for item in text_data:
                if isinstance(item, dict) and "content" in item:
                    extracted_texts.append(
                        ExtractedText(
                            content=item["content"],
                            confidence=item.get("confidence", 0.8),
                            bounding_box=None,
                            language=None,
                        )
                    )
                elif isinstance(item, str):
                    extracted_texts.append(
                        ExtractedText(
                            content=item,
                            confidence=0.8,
                            bounding_box=None,
                            language=None,
                        )
                    )

            return extracted_texts

        except json.JSONDecodeError:
            # If JSON parsing fails, treat the whole response as text
            return [
                ExtractedText(
                    content=response,
                    confidence=0.8,
                    bounding_box=None,
                    language=None,
                )
            ]

    async def detect_objects(
        self, image: Image.Image, **kwargs: Any
    ) -> List[DetectedObject]:
        """Detect objects in the image."""
        self.validate_image(image)

        # Convert image to base64
        image_data = image_to_base64(image, "JPEG")

        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Please identify and list all objects, people, animals, and significant items visible in this image. Return the results as a JSON array where each item has 'name' (object name) and 'confidence' (estimated confidence from 0.0 to 1.0). Focus on the most prominent and clearly visible objects.",
                    },
                    {"type": "image_url", "image_url": {"url": image_data}},
                ],
            }
        ]

        response = await self._make_api_call(messages, **kwargs)

        try:
            # Try to parse JSON response
            objects_data = json.loads(response)
            if not isinstance(objects_data, list):
                # If not a list, extract object names from text
                return self._extract_objects_from_text(response)

            detected_objects = []
            for item in objects_data:
                if isinstance(item, dict) and "name" in item:
                    detected_objects.append(
                        DetectedObject(
                            name=item["name"],
                            confidence=item.get("confidence", 0.8),
                        )
                    )
                elif isinstance(item, str):
                    detected_objects.append(DetectedObject(name=item, confidence=0.8))

            return detected_objects

        except json.JSONDecodeError:
            # If JSON parsing fails, extract objects from text
            return self._extract_objects_from_text(response)

    def _extract_objects_from_text(self, text: str) -> List[DetectedObject]:
        """Extract object names from text response."""
        # Simple extraction - split by common delimiters and clean up
        import re

        # Remove common prefixes and clean up
        text = re.sub(
            r"^(I can see|In this image|The image shows|This image contains)",
            "",
            text,
            flags=re.IGNORECASE,
        )

        # Split by common delimiters
        objects = re.split(r"[,;.\n]", text)

        detected_objects = []
        for obj in objects:
            obj = obj.strip()
            if obj and len(obj) > 2:  # Filter out very short strings
                # Remove articles and common words
                obj = re.sub(
                    r"^(a|an|the|some|several|many|few)\s+",
                    "",
                    obj,
                    flags=re.IGNORECASE,
                )
                if obj:
                    detected_objects.append(DetectedObject(name=obj, confidence=0.7))

        return detected_objects[:10]  # Limit to top 10 objects

    async def analyze_image(
        self,
        image: Image.Image,
        analysis_type: AnalysisType = AnalysisType.COMPREHENSIVE,
        **kwargs: Any,
    ) -> ImageAnalysis:
        """Analyze an image and return structured results."""
        self.validate_image(image)

        analysis = ImageAnalysis()  # metadata will be set by the base class

        if analysis_type in [AnalysisType.DESCRIPTION, AnalysisType.COMPREHENSIVE]:
            analysis.description = await self.describe_image(image, **kwargs)

        if analysis_type in [AnalysisType.TEXT, AnalysisType.COMPREHENSIVE]:
            analysis.text = await self.extract_text(image, **kwargs)

        if analysis_type in [AnalysisType.OBJECTS, AnalysisType.COMPREHENSIVE]:
            analysis.objects = await self.detect_objects(image, **kwargs)

        return analysis

    async def analyze_with_custom_prompt(
        self,
        image: Image.Image,
        image_metadata: Dict[str, Any],
        custom_prompt: str,
        **kwargs: Any,
    ) -> "ProcessingResult":
        """Analyze an image using a custom prompt provided by the agent."""
        start_time = time.time()
        request_id = str(uuid.uuid4())

        try:
            self.validate_image(image)

            # Convert image to base64
            image_data = image_to_base64(image, "JPEG")

            # Create message with custom prompt
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": custom_prompt,
                        },
                        {"type": "image_url", "image_url": {"url": image_data}},
                    ],
                }
            ]

            # Get response from OpenAI
            response = await self._make_api_call(messages, **kwargs)

            # Create analysis with the custom response
            analysis = ImageAnalysis(
                description=response,
                objects=[],
                text=[],
            )

            # Create metadata
            processing_time = time.time() - start_time
            metadata = ImageMetadata(
                width=image_metadata["width"],
                height=image_metadata["height"],
                format=image_metadata["format"],
                size_bytes=image_metadata.get("size_bytes", 0),
                processing_time=processing_time,
                api_provider=self.provider,
            )
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
