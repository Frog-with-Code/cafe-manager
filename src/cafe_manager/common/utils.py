from pathlib import Path
from typing import Callable, Any
from functools import wraps
from decimal import Decimal
import random

def validate_non_negative(*args: int | float | Decimal) -> None:
    """
    Validate that one or more numeric values are non-negative.

    Iterates through all provided arguments to ensure they are instances of 
    numeric types (int, float, Decimal) and that their value is greater 
    than or equal to zero.

    Args:
        *args (int | float | Decimal): Variable length argument list of numbers to validate.

    Raises:
        TypeError: If an argument is not an int, float, or Decimal.
        ValueError: If an argument is less than zero.
    """
    for value in args:
        if not isinstance(value, (int, float, Decimal)):
            raise TypeError(f"Value {value} must be numeric, {type(value).__name__} was given")
        if value < 0:
            raise ValueError(f"Value {value} must be positive")
        
