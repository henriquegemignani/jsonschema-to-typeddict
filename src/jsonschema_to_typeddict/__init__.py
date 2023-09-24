"""
Generates a python file with a TypedDict definition that attempts to match what is in a given JsonSchema.
The generated TypedDict is looser than the schema and is intended only to catch simple usage errors.
"""

__version__ = "0.1.0"