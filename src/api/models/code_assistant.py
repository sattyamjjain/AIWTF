from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

class CodeContext(BaseModel):
    """Model for code context"""
    language: str
    framework: Optional[str] = None
    dependencies: List[str] = []
    existing_code: Optional[str] = None

class CodeRequest(BaseModel):
    """Model for code assistance request"""
    request: str
    context: Optional[CodeContext] = None
    language: str = "python"

class CodeSuggestion(BaseModel):
    """Model for code improvement suggestions"""
    type: str
    description: str
    example: Optional[str] = None

class CodeMetadata(BaseModel):
    """Model for code assistance metadata"""
    language: str
    completion_time: str
    duration: str
    errors: List[str] = []

class CodeResponse(BaseModel):
    """Model for code assistance response"""
    request: str
    code: str
    explanation: str = ""
    suggestions: List[str] = []
    metadata: CodeMetadata 