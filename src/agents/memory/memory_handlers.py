from typing import Dict, Any, List
from langchain.memory import ConversationBufferMemory
from datetime import datetime

class EnhancedMemory(ConversationBufferMemory):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.metadata: Dict[str, Any] = {
            "created_at": datetime.now(),
            "interactions": []
        }
    
    def add_interaction(self, input_text: str, output_text: str):
        """Add an interaction to memory with metadata."""
        self.metadata["interactions"].append({
            "timestamp": datetime.now(),
            "input": input_text,
            "output": output_text
        })
        return super().save_context({"input": input_text}, {"output": output_text})
    
    def get_relevant_history(self, query: str, k: int = 5) -> List[Dict[str, str]]:
        """Get relevant historical interactions."""
        return self.metadata["interactions"][-k:]

class MemoryFactory:
    @staticmethod
    def create_memory(memory_type: str = "enhanced", **kwargs) -> ConversationBufferMemory:
        if memory_type == "enhanced":
            return EnhancedMemory(**kwargs)
        return ConversationBufferMemory(**kwargs)
