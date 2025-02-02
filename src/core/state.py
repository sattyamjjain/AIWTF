from typing import TypedDict, Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class WorkflowState:
    """Core state management for all agents"""

    messages: List[Any] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    artifacts: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(
        default_factory=lambda: {"start_time": datetime.now(), "steps_taken": []}
    )


@dataclass
class AgentState:
    """State management for agents"""

    conversation_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    context: Dict[str, Any] = field(default_factory=dict)
    memory: Dict[str, Any] = field(default_factory=dict)

    def update(self, key: str, value: Any) -> None:
        """Update state with new information"""
        self.context[key] = value
        self.last_updated = datetime.now()
