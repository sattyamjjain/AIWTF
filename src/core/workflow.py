from typing import Dict, Any, Callable
from langgraph.graph import StateGraph


class WorkflowManager:
    """Manages complex agent workflows"""

    def __init__(self):
        self.nodes: Dict[str, Callable] = {}
        self.edges: Dict[str, Dict[str, str]] = {}

    def add_node(self, name: str, func: Callable):
        self.nodes[name] = func

    def create_graph(self, state_type: Any) -> StateGraph:
        builder = StateGraph(state_type)
        for name, func in self.nodes.items():
            builder.add_node(name, func)
        return builder
