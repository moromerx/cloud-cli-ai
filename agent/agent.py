from llm.llm import Session, FunctionCaller, SafetyControls
from typing import List
from llm.interfaces import ToolCallResult, LLMProvider
from typing import Union, Callable, Any
from llm.openai import OpenAIProvider
from llm.ollama import OllamaProvider
import json

class Agent:
    DEFAULT_MODELS = {
        "openai": "gpt-4o",
        "ollama": "llama3.1",
        "groq": "llama-3.3-70b-versatile"
    }
    
    PROVIDERS = {
        "openai": OpenAIProvider(),
        "ollama": OllamaProvider(),
        "groq": OpenAIProvider()
    }
    
    def __init__(
        self,
        client: Any,
        session: Session,
        model: str,
        function_caller: FunctionCaller,
        safety_controls: SafetyControls,
        tools: Any,
        provider: LLMProvider,
        tool_use_behavior: Union[str, List[str], Callable[[str, Any], bool]] = "run_llm_again",
    ):
        self.client = client
        self.session = session
        self.function_caller = function_caller
        self.safety_controls = safety_controls
        self.tools = tools
        self.tool_use_behavior = tool_use_behavior
        self.provider = provider
        self.model = model
        
    def switch_provider(self, new_provider):
        if new_provider not in self.DEFAULT_MODELS:
            raise ValueError(f"Unsupported provider: {new_provider}")
        if new_provider not in self.PROVIDERS:
            raise ValueError(f"Provider {new_provider} not initialized")

        # Get new provider instance
        provider_instance = self.PROVIDERS[new_provider]

        # Rebuild client from provider instance
        if new_provider == "openai":
            client = provider_instance.build_openai_client()
        elif new_provider == "groq":
            client = provider_instance.build_groq_client()
        elif new_provider == "ollama":
            client = provider_instance.build_ollama_client()
        else:
            raise ValueError(f"No client builder defined for provider: {new_provider}")

        self.provider = new_provider
        self.model = self.DEFAULT_MODELS[new_provider]
        self.client = client
        self.provider = provider_instance
        self.session.provider = provider_instance


    def set_model(self, model_name):
        self.model = model_name
        
    def run(self, user_input: str):
        self.session.add_message("user", user_input)
        return self.agentic_loop()
    
    def should_stop_after_tool(self, tool_name: str, tool_result: Any) -> bool:
        if self.tool_use_behavior == "stop_on_first_tool":
            return True
        elif isinstance(self.tool_use_behavior, list):
            return tool_name in self.tool_use_behavior
        elif callable(self.tool_use_behavior):
            return self.tool_use_behavior(tool_name, tool_result)
        return False  # default: "run_llm_again"
    
    def agentic_loop(self):
        current_iteration = 0
        MAX_ITERATIONS = self.session.max_iterations

        while current_iteration < MAX_ITERATIONS:
            current_provider_instance = self.session.provider
            message = current_provider_instance.chat(
                client=self.client,
                model=self.model,
                messages=self.session.messages,
                tools=self.tools
            )

            self.session.messages.append(message)

            # If there are tool calls, process them and continue the loop
            if getattr(message, "tool_calls", None):
                for tool in message.tool_calls:
                    name = tool.function.name
                    args = tool.function.arguments

                    if isinstance(args, str):
                        try:
                            args = json.loads(args)
                        except json.JSONDecodeError:
                            print(f"Invalid JSON in arguments: {args}")

                    if not self.safety_controls.check(args):
                        return

                    result = self.function_caller.call(name, args)
                    tool_result = ToolCallResult(
                        result=result,
                        tool_call_id=getattr(tool, 'id', None),
                        tool_name=name
                    )
                    self.session.add_tool_response(tool_result)
                # Continue to next iteration after handling tool calls

            else:
                # No tool calls: this is the final answer, so exit the loop
                # Do NOT print again, just return for programmatic use
                return (message.content.strip(), "green")

            current_iteration += 1

        return ("Max iterations reached.", "yellow")
        
    # def agentic_loop(self):
    #     current_iteration = 0
    #     MAX_ITERATIONS = self.session.max_iterations
    #     action_re = re.compile(r"Action:\s*(\w+)\((.*)\)")

    #     next_prompt = self.session.messages[-1]["content"] if self.session.messages else ""

    #     while current_iteration < MAX_ITERATIONS:
    #         self.session.add_message("user", next_prompt)

    #         # Get model response
    #         current_provider_instance = self.session.provider
    #         message = current_provider_instance.chat(
    #             client=self.client,
    #             model=self.model,
    #             messages=self.session.messages,
    #             tools=self.tools
    #         )

    #         self.session.messages.append(message)
    #         result = message.content.strip()
    #         print(f"Result: {result}")

    #         # Check for final answer
    #         if result.lower().startswith("answer:"):
    #             return (result.split("Answer:", 1)[1].strip(), "green")

    #         # Look for Action line(s)
    #         actions = [
    #             action_re.match(line) for line in result.splitlines()
    #             if action_re.match(line)
    #         ]

    #         if actions:
    #             action, args_str = actions[0].groups()
    #             try:
    #                 action_inputs = self._parse_arguments(args_str)
    #             except Exception as e:
    #                 print(f"Failed to parse arguments: {args_str}")
    #                 return (f"Argument parsing error: {str(e)}", "red")

    #             tool = self.tools.get(action)
    #             if not tool:
    #                 return (f"Unknown action: {action}", "red")

    #             print(f"Calling Function {action} with {action_inputs}")
    #             observation = tool(*action_inputs)
    #             print(f"Observation: {observation}")

    #             self.session.add_message("user", f"Observation: {observation}")
    #             next_prompt = f"Observation: {observation}"

    #             if self.should_stop_after_tool(action, observation):
    #                 return (str(observation), "blue")
    #         else:
    #             # No action found and no answer — ambiguous
    #             return ("No actionable step or answer identified.", "yellow")

    #         current_iteration += 1

    #     return ("Max iterations reached.", "yellow")

    
    # def agentic_loop(self):
    #     current_iteration = 0
    #     MAX_ITERATIONS = self.session.max_iterations

    #     while current_iteration < MAX_ITERATIONS:    
    #         # Fix: Get current provider instance and call chat with proper parameters
    #         current_provider_instance = self.session.provider
    #         message = current_provider_instance.chat(
    #             client=self.client,
    #             model=self.model,
    #             messages=self.session.messages,
    #             tools=self.tools
    #         )
            
    #         self.session.messages.append(message)
            
    #         if message.tool_calls:
    #             for tool in message.tool_calls:
    #                 name = tool.function.name
    #                 args = tool.function.arguments
                    
    #                 if isinstance(args, str):
    #                     try:
    #                         args = json.loads(args)
    #                     except json.JSONDecodeError:
    #                         print(f"Invalid JSON in arguments: {args}")

    #                 if not self.safety_controls.check(args):
    #                     return

    #                 result = self.function_caller.call(name, args)
                    
    #                 # Create proper ToolCallResult
    #                 tool_result = ToolCallResult(
    #                     result=result,
    #                     tool_call_id=getattr(tool, 'id', None),
    #                     tool_name=name
    #                 )
    #                 self.session.add_tool_response(tool_result)

    #                 if self.should_stop_after_tool(name, result):
    #                     return (str(result), "blue")  # Tool result is final
    #         else:
    #             # No tool call – assume this is the final answer
    #             final_output = message.content.strip()

    #             if final_output.lower().startswith("answer:"):
    #                 final_output = final_output[len("answer:"):].lstrip()

    #             return (final_output, "green")

    #         current_iteration += 1

    #     return ("Max iterations reached.", "yellow")

# class Agent:
#     DEFAULT_MODELS = {
#         "openai": "gpt-4o",
#         "ollama": "llama3.1",
#         "groq": "llama-3.3-70b-versatile"
#     }
    
#     def __init__(
#         self,
#         client: Client,
#         session: Session,
#         function_caller: FunctionCaller,
#         safety_controls: SafetyControls,
#         tools: List[Function],
#         provider: LLMProvider,
#         tool_use_behavior: Union[str, List[str], Callable[[str, Any], bool]] = "run_llm_again",
#         model: str = None,
#     ):
#         self.client = client
#         self.session = session
#         self.function_caller = function_caller
#         self.safety_controls = safety_controls
#         self.tools = tools
#         self.tool_use_behavior = tool_use_behavior
#         self.react_action_re = re.compile(r'(?:\*\*)?Action(?:\*\*)?:\s*(\w+)\s*\((.*?)\)', re.IGNORECASE)
#         self.model = model or self.DEFAULT_MODELS[provider]
#         self.provider = provider
        
#     def switch_provider(self, new_provider):
#         if new_provider not in self.DEFAULT_MODELS:
#             raise ValueError(f"Unsupported provider: {new_provider}")
#         self.provider = new_provider
#         self.model = self.DEFAULT_MODELS[new_provider]

#     def set_model(self, model_name):
#         self.model = model_name

#     def run(self, user_input: str):
#         self.session.add_message("user", user_input)
#         return self.agentic_loop()

#     def should_stop_after_tool(self, tool_name: str, tool_result: Any) -> bool:
#         if self.tool_use_behavior == "stop_on_first_tool":
#             return True
#         elif isinstance(self.tool_use_behavior, list):
#             return tool_name in self.tool_use_behavior
#         elif callable(self.tool_use_behavior):
#             return self.tool_use_behavior(tool_name, tool_result)
#         return False  # default: "run_llm_again"
    
#     def agentic_loop(self):
#         current_iteration = 0
#         MAX_ITERATIONS = self.session.max_iterations

#         while current_iteration < MAX_ITERATIONS:    
#             message = self.provider.chat()
            
#             self.session.messages.append(message)
            
#             if message.tool_calls:
#                 for tool in message.tool_calls:
#                     name = tool.function.name
#                     args = tool.function.arguments

#                     if not self.safety_controls.check(args):
#                         return

#                     result = self.function_caller.call(name, args)
#                     self.session.add_tool_response(str(result),tool.function.name)

#                     if self.should_stop_after_tool(name, result):
#                         return (str(result), "blue")  # Tool result is final
#             else:
#                 # No tool call – assume this is the final answer
#                 final_output = message.content.strip()

#                 if final_output.lower().startswith("answer:"):
#                     final_output = final_output[len("answer:"):].lstrip()

#                 return (final_output, "green")

#             current_iteration += 1

#         return ("Max iterations reached.", "yellow")

# def agentic_loop(self):
#         current_iteration = 0
#         MAX_ITERATIONS = self.session.max_iterations

#         while current_iteration < MAX_ITERATIONS:    
#             response: ChatResponse = ollama_chat(
#                 self.model,
#                 messages=self.session.messages,
#                 tools=self.tools
#             )
            
#             message = response.message
#             self.session.messages.append(message)
            
#             if message.tool_calls:
#                 for tool in message.tool_calls:
#                     name = tool.function.name
#                     args = tool.function.arguments

#                     if not self.safety_controls.check(args):
#                         return

#                     result = self.function_caller.call(name, args)
#                     self.session.add_tool_response(str(result),tool.function.name)

#                     if self.should_stop_after_tool(name, result):
#                         return (str(result), "blue")  # Tool result is final
#             else:
#                 # No tool call – assume this is the final answer
#                 final_output = message.content.strip()

#                 if final_output.lower().startswith("answer:"):
#                     final_output = final_output[len("answer:"):].lstrip()

#                 return (final_output, "green")

#             current_iteration += 1

#         return ("Max iterations reached.", "yellow")

    # def agentic_loop(self):
    #     current_iteration = 0
    #     MAX_ITERATIONS = self.session.max_iterations

    #     while current_iteration < MAX_ITERATIONS:
    #         completion = self.client.chat.completions.create(
    #             model=self.model,
    #             messages=self.session.messages,
    #             tools=self.tools,
    #         )

    #         message = completion.choices[0].message
    #         self.session.messages.append(message)
            
    #         self.ui.display_message(f"\nOriginal Message: {message.content}")

    #         # 1. Native OpenAI tool call support
    #         if hasattr(message, "tool_calls") and message.tool_calls:
    #             for tool_call in message.tool_calls:
    #                 name = tool_call.function.name
    #                 args = json.loads(tool_call.function.arguments)
    #                 self.ui.display_message(f"\nResult being returned:\n{json.dumps(args, indent=2)}")
    #                 if not self.safety_controls.check(args):
    #                     return
    #                 result = self.function_caller.call(name, args)
    #                 self.ui.display_message(f"\nResult being returned: {result}")
    #                 self.session.add_tool_response(tool_call.id, str(result))
    #                 if self.should_stop_after_tool(name, result):
    #                     return (str(result), "blue")
    #         else:
    #             # 2. Manual parsing fallback (shim)
    #             parsed = self.parse_manual_tool_call(message.content)
    #             if parsed:
    #                 name, args = parsed
    #                 self.ui.display_message(f"\n[Shim] Parsed tool call: {name}({args})")
    #                 if not self.safety_controls.check(args):
    #                     return
    #                 result = self.function_caller.call(name, args)
    #                 self.ui.display_message(f"\n[Shim] Result being returned: {result}")
    #                 # Add as an observation (simulate tool response)
    #                 self.session.add_message("tool", str(result))
    #                 # Optionally, check if you want to stop here
    #                 if self.should_stop_after_tool(name, result):
    #                     return (str(result), "blue")
    #                 # Continue loop (the agent will see the observation in the next round)
    #             else:
    #                 # No tool call – assume this is the final answer
    #                 final_output = message.content.strip()
    #                 if final_output.lower().startswith("answer:"):
    #                     final_output = final_output[len("answer:"):].lstrip()
    #                 return (final_output, "green")

    #         current_iteration += 1

    #     return ("Max iterations reached.", "yellow")

    # def agentic_loop(self):
    #     current_iteration = 0
    #     MAX_ITERATIONS = self.session.max_iterations

    #     while current_iteration < MAX_ITERATIONS:
    #         completion = self.client.chat.completions.create(
    #             model=self.model,
    #             messages=self.session.messages,
    #             tools=self.tools,
    #         )

    #         message = completion.choices[0].message
    #         self.session.messages.append(message)
            
    #         self.ui.display_message(f"\nOriginal Message: {message.content}")

    #         if message.tool_calls:
    #             for tool_call in message.tool_calls:
    #                 name = tool_call.function.name
    #                 args = json.loads(tool_call.function.arguments)
                    
    #                 self.ui.display_message(f"\nResult being returned:\n{json.dumps(args, indent=2)}")
                    
    #                 if not self.safety_controls.check(args):
    #                     return

    #                 result = self.function_caller.call(name, args)
    #                 self.ui.display_message(f"\nResult being returned: {result}")
    #                 self.session.add_tool_response(tool_call.id, str(result))

    #                 # 🛑 Check if we're supposed to stop here
    #                 if self.should_stop_after_tool(name, result):
    #                     return (str(result), "blue")  # Tool result is final
    #         else:
    #             # No tool call – assume this is the final answer
    #             final_output = message.content.strip()

    #             if final_output.lower().startswith("answer:"):
    #                 final_output = final_output[len("answer:"):].lstrip()

    #             return (final_output, "green")

    #         current_iteration += 1

    #     return ("Max iterations reached.", "yellow")
    
    
    # def agentic_loop(self):
        
    #     current_iteration = 0
        
    #     MAX_ITERATIONS = self.session.max_iterations
        
    #     while current_iteration < MAX_ITERATIONS:
    #         completion = self.client.chat.completions.create(
    #             model=self.model,
    #             messages=self.session.messages,
    #             tools=self.tools,
    #         )
            
    #         message = completion.choices[0].message
    #         self.session.messages.append(message)

    #         if message.tool_calls:
    #             for tool_call in message.tool_calls:
    #                 name = tool_call.function.name
    #                 args = json.loads(tool_call.function.arguments)

    #                 if not self.safety_controls.check(args):
    #                     return

    #                 # print(f"\nThe code being run:\n{args['command']}")
    #                 result = self.function_caller.call(name, args)
    #                 # print(f"\nThe result after running:\n{result}")
    #                 self.session.add_tool_response(tool_call.id, str(result))
    #         else:
    #             return (message.content, "green")
            
    #         current_iteration += 1

    #     return ("Max iterations reached.", "yellow")