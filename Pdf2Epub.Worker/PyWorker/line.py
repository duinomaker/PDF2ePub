from typing import Any, Callable, Literal, NoReturn, TypeAlias, TypeVar
from enum import Enum

T = TypeVar('T')

JsonLike: TypeAlias = dict[str, Any]
BBox: TypeAlias = tuple[float, float, float, float]
Line: TypeAlias = JsonLike


class LineType(Enum):
    TEXT = 1
    IMAGE = 2


def make_line(data: JsonLike, t: LineType) -> Line:
    """Add a type tag to line data."""

    assert '_type' not in data
    data['_type'] = t
    return data


def line_type(line: Line) -> LineType:
    """Text line or image line."""

    assert '_type' in line and isinstance(line['_type'], LineType)
    return line['_type']
