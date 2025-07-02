from rich.markdown import Markdown
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.text import Text
from prompt_toolkit.styles import Style
from prompt_toolkit import prompt
import textwrap

class UI:
    def __init__(self, console: Console):
        self.console = console
        self.style = Style.from_dict({'prompt': 'orange'})
        
    def display_welcome(self):
        markdown_text = textwrap.dedent("""
        # cloud-cli-ai

        A CLI tool to interact with your cloud environment using natural language.

        Type `--provider [openai|ollama]` to switch provider.  
        Type `--model [MODEL NAME]` to change the model.  
        Type `exit` to quit.

        How can I help you today?
        """)

        self.console.print(Markdown(markdown_text))

    def get_user_input(self) -> str:
        return prompt("\n>> ", style=self.style).strip()

    def display_message(self, message: str, color: str = "grey"): 
        self.console.print(f"[{color}]{message}[/{color}]")
        
    def display_response(self, message: str):
        formatted = Panel(
            Text(message, style="white"),
            title="🤖 Assistant",
            title_align="left",
            border_style="cyan"
        )
        self.console.print(formatted)
        self.console.print()

    def display_markdown(self, md: str):
        self.console.print(Markdown(md))

    def display_code_block(self, code: str, language: str = "python"):
        syntax = Syntax(code, language, theme="monokai", line_numbers=True)
        self.console.print(syntax)

    def confirm_modification(self, resource_name: str) -> str:
        self.console.print(
            Panel.fit(
                f"[bold yellow]{resource_name}[/bold yellow] will be modified.\n"
                "Do you want to proceed?\n\n"
                "[bold]1)[/bold] Yes\n"
                "[bold]2)[/bold] Yes, and don't ask me again\n"
                "[bold]3)[/bold] No",
                title="⚠️ Confirmation",
                border_style="red"
            )
        )
        return prompt("Enter your choice (1/2/3): ", style=self.style).strip()