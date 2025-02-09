import pytest
from src.api.models.code_assistant import CodeRequest, CodeContext
from src.services.code_assistant import CodeAssistantService
from src.innovations.code_assistant.agent import CodeAssistantAgent

@pytest.fixture
def code_assistant():
    """Create a code assistant service for testing"""
    return CodeAssistantService()

@pytest.mark.asyncio
async def test_code_analysis(code_assistant):
    sample_code = """
    def fibonacci(n):
        if n <= 1:
            return n
        return fibonacci(n-1) + fibonacci(n-2)
    """

    request = CodeRequest(
        request="Analyze this fibonacci implementation",
        context=CodeContext(
            language="python",
            existing_code=sample_code
        )
    )

    result = await code_assistant.process_request(request)
    assert result.code is not None
    assert "fibonacci" in result.code.lower()

@pytest.mark.asyncio
async def test_code_generation(code_assistant):
    request = CodeRequest(
        request="Generate a function to calculate factorial",
        context=CodeContext(language="python")
    )

    result = await code_assistant.process_request(request)
    assert result.code is not None
    assert "factorial" in result.code.lower() 