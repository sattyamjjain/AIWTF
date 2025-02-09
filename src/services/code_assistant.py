from typing import Dict, Any
from src.innovations.code_assistant.agent import CodeAssistantAgent
from src.api.models.code_assistant import (
    CodeRequest,
    CodeResponse,
    CodeSuggestion,
    CodeMetadata
)
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class CodeAssistantService:
    """Service for handling code assistance operations"""

    def __init__(self):
        """Initialize the code assistant service"""
        self.agent = CodeAssistantAgent()

    async def process_request(self, request: CodeRequest) -> CodeResponse:
        """Process a code assistance request"""
        try:
            result = await self.agent.assist_with_code(
                request=request.request,
                context=request.context.dict() if request.context else None,
                language=request.language
            )

            # Extract the response string from the agent's output
            response_text = result["code"]
            if isinstance(response_text, dict):
                response_text = response_text.get("response", "")

            return CodeResponse(
                request=request.request,
                code=response_text,  # Make sure this is a string
                explanation=result.get("explanation", ""),
                suggestions=result.get("suggestions", []),
                metadata=CodeMetadata(
                    language=request.language,
                    completion_time=result["metadata"]["completion_time"],
                    duration=result["metadata"]["duration"],
                    errors=result["metadata"]["errors"]
                )
            )
        except Exception as e:
            logger.error(f"Code assistance failed: {str(e)}")
            raise 