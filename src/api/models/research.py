from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class ResearchSource(BaseModel):
    """Model for a research source"""
    title: str = Field(..., description="Title of the source")
    url: str = Field(..., description="URL of the source")

class ResearchMetadata(BaseModel):
    """Model for research metadata"""
    depth: int = Field(..., description="Research depth level")
    source_count: int = Field(..., description="Number of sources used")
    completion_time: datetime = Field(..., description="When the research was completed")
    duration: str = Field(..., description="How long the research took")
    errors: List[str] = Field(default_factory=list, description="Any errors encountered")

class ResearchResponse(BaseModel):
    """Model for research response"""
    topic: str = Field(..., description="Research topic")
    summary: str = Field(..., description="Comprehensive summary of findings")
    sources: List[ResearchSource] = Field(..., description="List of sources used")
    metadata: ResearchMetadata = Field(..., description="Research metadata")

class ResearchRequest(BaseModel):
    """Model for research request"""
    topic: str = Field(..., description="Topic to research")
    depth: int = Field(default=1, ge=1, le=3, description="Research depth (1-3)")
    max_sources: int = Field(default=5, ge=1, le=10, description="Maximum number of sources to use")
    provider: str = Field(default="auto", description="Search provider to use")
    api_key: Optional[str] = Field(default=None, description="API key if needed")
    cx: Optional[str] = Field(default=None, description="Custom Search Engine ID if needed")
    num_results: int = Field(default=5, ge=1, le=10, description="Number of results") 