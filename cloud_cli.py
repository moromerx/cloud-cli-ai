from rich.console import Console
from prompt_toolkit.styles import Style
from ui.ui import UI
from agent.agent import Agent

class CloudCLI:
    def __init__(self, agent: Agent, ui: UI):
        self.agent = agent
        self.ui = ui

    def run(self):
        self.ui.display_welcome()

        while True:
            try:
                user_input = self.ui.get_user_input()

                if not user_input:
                    continue

                if user_input.lower() in ["exit", "quit"]:
                    break

                if user_input.startswith("--provider "):
                    new_provider = user_input.split("--provider ", 1)[1].strip().lower()
                    try:
                        self.agent.switch_provider(new_provider)
                        self.ui.display_message(f"Provider switched to '{new_provider}' with model '{self.agent.model}'", "bold green")
                    except ValueError as e:
                        self.ui.display_message(str(e), "red")
                    continue

                if user_input.startswith("--model "):
                    new_model = user_input.split("--model ", 1)[1].strip()
                    self.agent.set_model(new_model)
                    self.ui.display_message(f"Model switched to '{new_model}' for provider '{self.agent.provider}'", "bold green")
                    continue

                # Normal prompt
                result, style = self.agent.run(user_input)

                if style == "green":
                    self.ui.display_response(result)
                else:
                    self.ui.display_message(result, style)

            except KeyboardInterrupt:
                self.ui.display_message("Use 'exit' to quit.", "bold red")
            except EOFError:
                break
            except Exception as e:
                self.ui.display_message(f"Error: {str(e)}", "red")