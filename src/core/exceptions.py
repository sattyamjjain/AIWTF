class AIWTFException(Exception):
    """Base exception class for AIWTF project"""
    pass

class ToolExecutionError(AIWTFException):
    """Raised when a tool fails to execute"""
    pass

class AgentExecutionError(AIWTFException):
    """Raised when an agent fails to execute"""
    pass

class ConfigurationError(AIWTFException):
    """Raised when there's a configuration error"""
    pass

class AgentError(AIWTFException):
    """Raised when there's an error in agent execution"""
    pass

class ToolError(AIWTFException):
    """Raised when there's an error in tool execution"""
    pass

class WorkflowError(AIWTFException):
    """Raised when there's an error in workflow execution"""
    pass

class ResearchError(AIWTFException):
    """Raised when there's an error in research operations"""
    pass
