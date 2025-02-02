# AIWTF

AIWTF: A chaotic playground where generative AI, RAG, and rogue AI agents run wild.

## 🎯 Project Overview

This project is a comprehensive exploration of modern AI capabilities, featuring:

- Advanced AI Agents using LangChain
- Retrieval-Augmented Generation (RAG) systems
- Multi-agent communication and coordination
- Web interaction and data processing capabilities

## 🌟 Features

- **Intelligent Agent System**
  - Built using LangChain and GPT-4 Turbo
  - Conversation memory for context retention
  - Extensible tool integration system
  - Async support for better performance

- **Web Capabilities**
  - DuckDuckGo search integration
  - Web content extraction and processing
  - Clean text processing and summarization

## 🛠️ Technology Stack

### Core AI

- LangChain ecosystem (langchain, langgraph)
- OpenAI GPT-4 Turbo
- ChromaDB for vector storage
- FAISS for similarity search

### Web & Processing

- BeautifulSoup4 for web scraping
- Selenium for dynamic content
- Unstructured for document processing
- Support for PDF, DOCX, PPTX formats

### Infrastructure

- Python 3.9+
- FastAPI & Uvicorn
- Pydantic for data validation
- Streamlit & Chainlit for UI options

## 📁 Project Structure

```text
AIWTF/
├── src/
│   ├── agents/
│   │   ├── base/
│   │   │   ├── __init__.py
│   │   │   ├── base_agent.py          # Original base agent
│   │   │   └── base_innovation.py     # Advanced base agent
│   │   ├── tools/
│   │   │   ├── __init__.py
│   │   │   ├── web_tools.py
│   │   │   ├── code_tools.py
│   │   │   ├── data_tools.py
│   │   │   └── multimedia_tools.py
│   │   └── memory/
│   │       ├── __init__.py
│   │       └── memory_handlers.py
│   ├── innovations/
│   │   ├── __init__.py
│   │   ├── research/
│   │   │   ├── __init__.py
│   │   │   ├── agent.py
│   │   │   └── tools.py
│   │   ├── code_assistant/
│   │   │   ├── __init__.py
│   │   │   ├── agent.py
│   │   │   └── tools.py
│   │   ├── multimodal/
│   │   │   ├── __init__.py
│   │   │   ├── agent.py
│   │   │   └── processors/
│   │   ├── automation/
│   │   │   ├── __init__.py
│   │   │   ├── agent.py
│   │   │   └── workflows/
│   │   └── data_analysis/
│   │       ├── __init__.py
│   │       ├── agent.py
│   │       └── processors/
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── logger.py
│   │   └── decorators.py
│   └── core/
│       ├── __init__.py
│       ├── state.py
│       ├── workflow.py
│       └── exceptions.py
├── tests/
│   ├── __init__.py
│   ├── unit/
│   │   └── test_agents/
│   └── integration/
│       └── test_workflows/
├── examples/
│   ├── research_example.py
│   ├── code_assistant_example.py
│   └── multimodal_example.py
├── docs/
│   ├── agents/
│   ├── tools/
│   └── workflows/
├── config/
│   ├── default.yaml
│   └── logging.yaml
├── requirements/
│   ├── base.txt
│   ├── dev.txt
│   └── prod.txt
├── README.md
├── setup.py
└── .env
```

## 🚀 Getting Started

1. Clone the repository:

```bash
git clone https://github.com/yourusername/AIWTF.git
cd AIWTF
```

2.Set up a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3.Install dependencies:

```bash
pip install -r requirements.txt
```

4.Set up environment variables:

```bash
cp .env.example .env
# Edit .env with your API keys
```

### Run Tests

```bash
# Run all tests
pytest

# Run only fast tests
pytest -m "fast"

# Run specific test file
pytest tests/test_setup.py
```

## 🧩 Components

### Base Agents

- **BaseAgent**: Foundation agent with core functionality
- **BaseInnovationAgent**: Advanced agent with LangGraph integration

### Tools

- **WebTools**: Web search and browsing capabilities
- **CodeTools**: Code analysis and refactoring
- **DataTools**: Data processing and analysis
- **MultimediaTools**: Handle various media types

### Specialized Agents

- **ResearchAgent**: Deep research and analysis
- **CodeAssistant**: Code-focused tasks
- **MultimodalAgent**: Handle multiple types of input/output
- **AutomationAgent**: Task automation
- **DataAnalysisAgent**: Data insights

## 📝 Development

### Adding New Tools

```python
from langchain_core.tools import BaseTool

class NewTool(BaseTool):
    name = "tool_name"
    description = "Tool description"
    
    def _run(self, query: str) -> str:
        # Implementation
        pass
```

### Creating Custom Agents

```python
from src.agents.base.base_innovation import BaseInnovationAgent

class CustomAgent(BaseInnovationAgent):
    def __init__(self, tools, **kwargs):
        system_prompt = """Custom system prompt"""
        super().__init__(tools=tools, system_prompt=system_prompt, **kwargs)
```

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- LangChain team for the amazing framework
- OpenAI for GPT models
- All contributors and users
