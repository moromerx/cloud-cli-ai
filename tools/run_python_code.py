import functools
import multiprocessing
import re
import sys
from io import StringIO
from typing import Dict, Optional

from pydantic import BaseModel, Field

class python_repl(BaseModel):
    """Simulates a standalone Python REPL."""

    globals: Optional[Dict] = Field(default_factory=dict, alias="_globals")  # type: ignore[arg-type]
    locals: Optional[Dict] = Field(default_factory=dict, alias="_locals")  # type: ignore[arg-type]

    @staticmethod
    def sanitize_input(query: str) -> str:
        """Sanitize input to the python REPL.

        Remove whitespace, backtick & python
        (if llm mistakes python console as terminal)

        Args:
            query: The query to sanitize

        Returns:
            str: The sanitized query
        """
        query = re.sub(r"^(\s|`)*(?i:python)?\s*", "", query)
        query = re.sub(r"(\s|`)*$", "", query)
        return query
    
    @classmethod
    def worker(
        cls,
        command: str,
        globals: Optional[Dict],
        locals: Optional[Dict],
        queue: multiprocessing.Queue,
    ) -> None:
        old_stdout = sys.stdout
        sys.stdout = mystdout = StringIO()
        try:
            cleaned_command = cls.sanitize_input(command)
            exec(cleaned_command, globals, locals)
            sys.stdout = old_stdout
            queue.put(mystdout.getvalue())
        except Exception as e:
            sys.stdout = old_stdout
            queue.put(repr(e))

    def run(self, command: str, modifies_resource: str,modified_resource_name: str =  None) -> str:
        """Run command with own globals/locals and returns anything printed."""

        queue: multiprocessing.Queue = multiprocessing.Queue()
       
        self.worker(command, self.globals, self.locals, queue)

        return queue.get()

run_python_code = python_repl()