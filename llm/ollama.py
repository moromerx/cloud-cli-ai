from typing import Any
from .interfaces import LLMProvider, ToolCallResult
from ollama import Client

class OllamaProvider(LLMProvider):
    def chat(self, client: Any,model: str, messages: list, tools: list):
        response = client.chat(
            model=model, 
            messages=messages,
            tools=tools
        )
        
        return response.message
    
    def format_tool_result(self, tool_result: ToolCallResult) -> dict:
        return {
            "role": "tool",
            "tool_name": tool_result.tool_name,
            "content": str(tool_result.result)
        }
        
    def build_ollama_client(self):
        return Client(
        host='http://localhost:11434',
        headers={'x-some-header': 'some-value'}
        )