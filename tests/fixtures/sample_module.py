"""A sample module used as a test fixture for AST parsing tests."""
import os
from typing import Optional


CONSTANT = 42


def simple_function(x: int, y: int = 0) -> int:
    """Add two numbers.

    Args:
        x: First number.
        y: Second number.

    Returns:
        Sum of x and y.
    """
    return x + y


def no_docstring(a, b):
    return a * b


async def async_function(url: str) -> Optional[str]:
    """Fetch something asynchronously.

    Args:
        url: Target URL.

    Returns:
        Response body or None.

    Example:
        result = await async_function("http://example.com")
    """
    return None


def complex_function(items: list, threshold: int = 10) -> dict:
    result = {}
    for item in items:
        if item > threshold:
            if item % 2 == 0:
                result[item] = "even-high"
            else:
                result[item] = "odd-high"
        else:
            if item < 0:
                result[item] = "negative"
            else:
                result[item] = "low"
    return result


class SampleClass:
    """A sample class for testing class-level metadata extraction."""

    class_var: str = "hello"

    def __init__(self, name: str, value: int = 0) -> None:
        """Initialize SampleClass.

        Args:
            name: Instance name.
            value: Initial value.
        """
        self.name = name
        self.value = value

    def method_with_decorator(self) -> str:
        return self.name.upper()

    @staticmethod
    def static_method(x: float) -> float:
        """Compute square root heuristic."""
        return x ** 0.5

    @classmethod
    def from_string(cls, s: str) -> "SampleClass":
        parts = s.split(":")
        return cls(parts[0], int(parts[1]) if len(parts) > 1 else 0)


class ChildClass(SampleClass):
    """Inherits from SampleClass."""

    def __init__(self, name: str, value: int, extra: str) -> None:
        super().__init__(name, value)
        self.extra = extra
