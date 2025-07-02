tools = [
   {
        "type": "function",
        "function": {
            "name": "run_python_code",
            "description": "Executes Python code in an isolated REPL environment and returns the printed output or error message.",
            "parameters": {
            "type": "object",
            "properties": {
                "command": {
                "type": "string",
                "description": "A string of Python code to execute in a REPL environment."
                },
                "modifies_resource": {
                "type": "string",
                "description": """ 
                    Whether the command modifies a AWS resource.
                    
                    Possible values:
                    - "yes" if the command modifies a resource
                    - "no" if the command does not modify a resource
                    - "unknown" if the command's effect on the resource is unknown
                """
                },
                "modified_resource_name": {
                "type": "string",
                "description": """ 
                    The name or ID of the AWS resource being modified.
                    
                    Possible values:
                    - 'i-0abcd1234efgh5678' (for an EC2 instance ID)
                    - 'my-s3-bucket' (for an S3 bucket name)
                """
                },
            },
            "required": [
                "command", "modifies_resource"
            ],
            "additionalProperties": False
            },
            "strict": True
        }
    },
]