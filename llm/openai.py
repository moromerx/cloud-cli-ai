from .interfaces import LLMProvider, ToolCallResult
import os
from openai import OpenAI, Client

class OpenAIProvider(LLMProvider):
    def chat(self, client: Client, model: str, messages: list, tools: list):
        
        completion = client.chat.completions.create(
                model=model,
                messages=messages,
                tools=tools,
        )
        
        return completion.choices[0].message
    
    def format_tool_result(self, tool_result: ToolCallResult) -> dict:
        return {
            "role": "tool",
            "content": str(tool_result.result),
            "tool_call_id": tool_result.tool_call_id
        }
        
    def build_openai_client(self):
        return OpenAI(
            base_url=os.environ.get("OPENAI_API_BASE_URL"),
            api_key=os.environ["OPENAI_API_KEY"]
        )
        
    def build_groq_client(self):
        return OpenAI(
            base_url=os.environ.get("GROQ_API_BASE_URL", "https://api.groq.com/openai/v1"),
            api_key=os.environ["GROQ_API_KEY"]
        )