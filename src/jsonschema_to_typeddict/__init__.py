"""
Generates a python file with a TypedDict definition that attempts to match what is in a given JsonSchema.
The generated TypedDict is looser than the schema and is intended only to catch simple usage errors.
"""

from ._version import __version__

__all__ = [
    "__version__",
]
