from tools.run_python_code import run_python_code
from .interfaces import LLMProvider, ToolCallResult
from ui.ui import UI

class FunctionCaller:
    def __init__(self):
        self.function_map = {
            "run_python_code": run_python_code.run,
        }

    def call(self, name, args):
        func = self.function_map.get(name)
        if func:
            return func(**args)
        raise ValueError(f"Unknown tool function: {name}")

class Session:
    def __init__(self, system_prompt: str, max_iterations: int, provider: LLMProvider):
        self.messages = [{"role": "system", "content": system_prompt}]
        self.skip_permissions = False
        self.max_iterations = max_iterations
        self.provider = provider

    def add_message(self, role, content):
        self.messages.append({"role": role, "content": content})

    def add_tool_response(self, tool_result: ToolCallResult):
        formatted = self.provider.format_tool_result(tool_result)
        self.messages.append(formatted)
        
class SafetyControls:
    def __init__(self, ui: UI):
        self.ui = ui
        self.skip_permissions = False

    def check(self, args):
        if args.get("modifies_resource", "").lower() == "yes":
            return self.confirm_resource_modification(args)
        return True  # If no special safety check is needed

    def confirm_resource_modification(self, args):
        if self.skip_permissions:
            return True

        name = args.get("modified_resource_name", "This resource")
        
        confirmation = self.ui.confirm_modification(name)

        if confirmation == "3":
            self.ui.display_message("Aborting operation as requested.", "red")
            return False
        elif confirmation == "2":
            self.skip_permissions = True

        return True