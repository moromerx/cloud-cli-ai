from abc import ABC, abstractmethod
from typing import Any
    
class ToolCallResult:
    def __init__(self, result, tool_call_id=None, tool_name=None):
        self.result = result
        self.tool_call_id = tool_call_id
        self.tool_name = tool_name
        

class LLMProvider(ABC):
    
    @abstractmethod
    def chat(self, client: Any, model: str, messages: list, tools: list):
        """Return a message from the model."""
        pass
    
    @abstractmethod
    def format_tool_result(self, tool_result: ToolCallResult) -> dict:
        pass