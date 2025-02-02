from datetime import datetime

MOCK_RESEARCH_REQUEST = {
    "topic": "Test Research Topic",
    "depth": 1,
    "max_sources": 3
}

MOCK_RESEARCH_RESPONSE = {
    "topic": "Test Research Topic",
    "summary": "Test summary of the research",
    "key_findings": {
        "Tax and Financial Changes": [
            "Test finding 1",
            "Test finding 2"
        ],
        "Economic Measures": [
            "Test measure 1",
            "Test measure 2"
        ],
        "Social Initiatives": [],
        "Infrastructure Development": [],
        "Other Important Highlights": []
    },
    "statistics": {
        "fiscal_indicators": [],
        "budget_allocations": [],
        "targets_and_goals": []
    },
    "sources": [
        {
            "title": "Test Source 1",
            "url": "http://test1.com"
        }
    ],
    "metadata": {
        "depth": 1,
        "source_count": 1,
        "completion_time": datetime.now(),
        "duration": "0:00:01.234567",
        "errors": []
    }
} 