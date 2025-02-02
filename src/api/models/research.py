from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from datetime import datetime

class ResearchRequest(BaseModel):
    """Research request model"""
    topic: str = Field(..., description="Research topic to investigate")
    depth: int = Field(
        default=1, 
        ge=1, 
        le=3, 
        description="Research depth (1-3)"
    )
    max_sources: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Maximum number of sources to use"
    )

class ResearchSource(BaseModel):
    """Research source model"""
    title: str
    url: str

class ResearchStatistics(BaseModel):
    """Research statistics model"""
    fiscal_indicators: List[str] = Field(default_factory=list)
    budget_allocations: List[str] = Field(default_factory=list)
    targets_and_goals: List[str] = Field(default_factory=list)

class ResearchMetadata(BaseModel):
    """Research metadata model"""
    depth: int
    source_count: int
    completion_time: datetime
    duration: str
    errors: List[str] = Field(default_factory=list)

class ResearchResponse(BaseModel):
    """Research response model"""
    topic: str
    summary: str
    key_findings: Dict[str, List[str]]
    statistics: Dict[str, List[str]]
    sources: List[ResearchSource]
    metadata: ResearchMetadata 