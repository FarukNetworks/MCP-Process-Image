"""Data models for image processing responses and configurations."""

from __future__ import annotations

import time
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


class APIProvider(str, Enum):
    """Supported API providers for image processing."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    AZURE = "azure"


class AnalysisType(str, Enum):
    """Types of image analysis available."""

    DESCRIPTION = "description"
    OBJECTS = "objects"
    TEXT = "text"
    COMPREHENSIVE = "comprehensive"
    # New UI-specific analysis types
    UI_ANALYSIS = "ui_analysis"
    ACCESSIBILITY_CHECK = "accessibility_check"
    DESIGN_REVIEW = "design_review"
    UX_ISSUES = "ux_issues"


class BoundingBox(BaseModel):
    """Bounding box coordinates for detected objects or text."""

    x: float = Field(..., description="X coordinate of top-left corner")
    y: float = Field(..., description="Y coordinate of top-left corner")
    width: float = Field(..., description="Width of the bounding box")
    height: float = Field(..., description="Height of the bounding box")


class DetectedObject(BaseModel):
    """Detected object in an image."""

    name: str = Field(..., description="Name of the detected object")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    bounding_box: Optional[BoundingBox] = Field(None, description="Object location")
    attributes: dict[str, Any] = Field(
        default_factory=dict, description="Additional attributes"
    )


class ExtractedText(BaseModel):
    """Text extracted from an image."""

    content: str = Field(..., description="Extracted text content")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    bounding_box: Optional[BoundingBox] = Field(None, description="Text location")
    language: Optional[str] = Field(None, description="Detected language")


class ImageMetadata(BaseModel):
    """Metadata about the processed image."""

    width: int = Field(..., description="Image width in pixels")
    height: int = Field(..., description="Image height in pixels")
    format: str = Field(..., description="Image format (JPEG, PNG, etc.)")
    size_bytes: Optional[int] = Field(None, description="Image size in bytes")
    processing_time: float = Field(..., description="Processing time in seconds")
    api_provider: APIProvider = Field(..., description="API provider used")


class ImageAnalysis(BaseModel):
    """Complete image analysis results."""

    description: Optional[str] = Field(None, description="Image description")
    objects: list[DetectedObject] = Field(
        default_factory=list, description="Detected objects"
    )
    text: list[ExtractedText] = Field(
        default_factory=list, description="Extracted text"
    )
    metadata: Optional[ImageMetadata] = Field(None, description="Image metadata")
    raw_response: Optional[dict[str, Any]] = Field(None, description="Raw API response")

    # UI-specific analysis results
    ui_issues: list[UIIssue] = Field(
        default_factory=list, description="UI/UX issues detected"
    )
    accessibility_issues: list[AccessibilityIssue] = Field(
        default_factory=list, description="Accessibility issues detected"
    )
    design_review: Optional[DesignReview] = Field(
        None, description="Design review feedback"
    )


class ProcessingResult(BaseModel):
    """Result of image processing operation."""

    success: bool = Field(..., description="Whether processing was successful")
    provider: APIProvider = Field(..., description="API provider used")
    analysis: Optional[ImageAnalysis] = Field(None, description="Analysis results")
    error: Optional[str] = Field(None, description="Error message if failed")
    request_id: Optional[str] = Field(None, description="Unique request identifier")
    timestamp: float = Field(
        default_factory=time.time, description="Processing timestamp"
    )


class BatchProcessingResult(BaseModel):
    """Result of batch image processing operation."""

    total_images: int = Field(..., description="Total number of images processed")
    successful: int = Field(..., description="Number of successfully processed images")
    failed: int = Field(..., description="Number of failed images")
    results: list[ProcessingResult] = Field(
        ..., description="Individual processing results"
    )
    processing_time: float = Field(..., description="Total processing time")


class APICapability(BaseModel):
    """Capabilities of an API provider."""

    provider: APIProvider = Field(..., description="API provider name")
    supports_description: bool = Field(..., description="Supports image description")
    supports_objects: bool = Field(..., description="Supports object detection")
    supports_text: bool = Field(..., description="Supports text extraction")
    supports_faces: bool = Field(False, description="Supports face detection")
    supports_landmarks: bool = Field(False, description="Supports landmark detection")
    max_image_size_mb: float = Field(..., description="Maximum image size in MB")
    supported_formats: list[str] = Field(..., description="Supported image formats")
    rate_limit_per_minute: Optional[int] = Field(
        None, description="Rate limit per minute"
    )


class ServerConfig(BaseModel):
    """Server configuration settings."""

    default_api_provider: APIProvider = Field(
        APIProvider.OPENAI, description="Default API provider"
    )
    max_image_size_mb: float = Field(10.0, description="Maximum image size in MB")
    request_timeout: int = Field(30, description="Request timeout in seconds")
    max_retries: int = Field(3, description="Maximum number of retries")
    rate_limit_per_minute: int = Field(60, description="Rate limit per minute")

    # API Keys (will be loaded from environment)
    openai_api_key: Optional[str] = Field(None, description="OpenAI API key")
    anthropic_api_key: Optional[str] = Field(None, description="Anthropic API key")
    google_credentials_path: Optional[str] = Field(
        None, description="Google credentials path"
    )
    azure_endpoint: Optional[str] = Field(None, description="Azure endpoint URL")
    azure_api_key: Optional[str] = Field(None, description="Azure API key")

    @field_validator("max_image_size_mb")
    @classmethod
    def validate_max_image_size(cls, v: float) -> float:
        """Validate maximum image size is reasonable."""
        if v <= 0 or v > 100:
            raise ValueError("max_image_size_mb must be between 0 and 100")
        return v

    @field_validator("request_timeout")
    @classmethod
    def validate_request_timeout(cls, v: int) -> int:
        """Validate request timeout is reasonable."""
        if v <= 0 or v > 300:
            raise ValueError("request_timeout must be between 1 and 300 seconds")
        return v


class UIIssue(BaseModel):
    """UI/UX issue detected in the interface."""

    type: str = Field(
        ..., description="Type of issue (layout, accessibility, design, etc.)"
    )
    severity: str = Field(
        ..., description="Severity level (critical, high, medium, low)"
    )
    title: str = Field(..., description="Brief title of the issue")
    description: str = Field(..., description="Detailed description of the issue")
    location: Optional[str] = Field(
        None, description="Location/element where issue occurs"
    )
    recommendation: str = Field(..., description="Suggested fix or improvement")
    bounding_box: Optional[BoundingBox] = Field(
        None, description="Location of the issue"
    )


class AccessibilityIssue(BaseModel):
    """Accessibility issue detected in the interface."""

    guideline: str = Field(..., description="WCAG guideline violated")
    level: str = Field(..., description="WCAG level (A, AA, AAA)")
    issue: str = Field(..., description="Description of accessibility issue")
    element: Optional[str] = Field(None, description="UI element affected")
    fix: str = Field(..., description="How to fix the issue")
    impact: str = Field(..., description="Impact on users with disabilities")


class DesignReview(BaseModel):
    """Design review feedback for the interface."""

    overall_score: float = Field(
        ..., ge=0.0, le=10.0, description="Overall design score"
    )
    strengths: list[str] = Field(default_factory=list, description="Design strengths")
    weaknesses: list[str] = Field(default_factory=list, description="Design weaknesses")
    suggestions: list[str] = Field(
        default_factory=list, description="Improvement suggestions"
    )
    consistency_score: float = Field(
        ..., ge=0.0, le=10.0, description="Design consistency score"
    )
    usability_score: float = Field(..., ge=0.0, le=10.0, description="Usability score")
