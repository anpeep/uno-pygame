from enum import Enum
from typing import TypeVar, Generic, Union, Dict, Any

T = TypeVar('T')

class SuccessResult(Generic[T]):
  def __init__(self, data: T):
    self.data = data
    self.error = None

  def __bool__(self):
    return True

class ErrorResult:
  def __init__(self, error: str):
    self.error = error
    self.data = None

  def __bool__(self):
    return False

# Type alias for the Result union
Result = Union[SuccessResult[T], ErrorResult]

# Helper functions to create results
def success(data: T) -> SuccessResult[T]:
  return SuccessResult(data)

def error(message: str) -> ErrorResult:
  return ErrorResult(message)

class GameCheat(str, Enum):
  GIVE_WILD_FOUR = "gw4"
  GIVE_WILD_EIGHT = "gw8"
