import pytest
import os
from pathlib import Path
import yaml
import logging
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# Test environment and configuration
@pytest.mark.fast
def test_environment():
    """Test environment setup and configuration loading"""
    load_dotenv()  # Load environment variables first
    # Quick environment check
    api_key = os.getenv('OPENAI_API_KEY')
    assert api_key is not None, "OPENAI_API_KEY not found in environment"

# Test core imports
def test_imports():
    """Test all critical imports work"""
    try:
        import langchain
        import langgraph
        import openai
        from langchain_core.tools import BaseTool
        from langchain_openai import ChatOpenAI
        print("✅ Core dependencies imported successfully")
    except ImportError as e:
        pytest.fail(f"Import failed: {str(e)}")

# Test project structure
@pytest.mark.fast
def test_project_structure():
    """Test project directory structure"""
    required_dirs = [
        'src/agents/base',
        'src/agents/tools',
        'src/core',
        'src/utils',
        'tests',
        'config'
    ]
    for dir_path in required_dirs:
        assert Path(dir_path).exists(), f"Required directory {dir_path} not found"

# Test logging setup
def test_logging():
    """Test logging configuration"""
    from src.utils.logger import setup_logging
    
    logger = setup_logging()
    assert isinstance(logger, logging.Logger)
    assert Path('logs').exists(), "Logs directory not created"

# Test OpenAI API access
@pytest.mark.slow
@pytest.mark.asyncio
async def test_openai_access():
    """Test OpenAI API access"""
    llm = ChatOpenAI()
    try:
        response = await llm.ainvoke("Quick test")
        assert response is not None
    except Exception as e:
        pytest.fail(f"OpenAI API test failed: {str(e)}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 