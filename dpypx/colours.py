"""Utilities for accepting colour input."""
import enum
import re
from typing import Union

from .canvas import Pixel


class Colour(enum.Enum):
    """A set of common colour codes."""

    BLACK = '000000'
    RED = 'FF0000'
    GREEN = '00FF00'
    BLUE = '0000FF'
    YELLOW = 'FFFF00'
    PINK = MAGENTA = 'FF00FF'
    CYAN = LIGHT_BLUE = '00FFFF'
    WHITE = 'FFFFFF'

    BLURPLE = DISCORD_BLURPLE = '5B55F2'
    DISCORD_RED = 'ED4245'
    DISCORD_GREEN = '57F287'
    DISCORD_YELLOW = 'FEE752'
    DISCORD_PINK = 'EB458E'
    DISCORD_BLACK = '23272A'


def parse_colour(value: Union[int, str, Colour]) -> str:
    """Parse a colour to a hex string.

    Accepts integers, strings and instances of the Colour enum.
    """
    if isinstance(value, int):
        if value >= 0 and value <= 0xFFFFFF:
            return f'{value:0>6x}'
    elif isinstance(value, str):
        neat_value = value.lstrip('#').upper()
        if re.match('[0-9A-F]{6}', neat_value):
            return neat_value
        if value.upper() in Colour.__members__:
            return Colour.__members__[value.upper()].value
    elif isinstance(value, Colour):
        return value.value
    elif isinstance(value, Pixel):
        # Remove leading "#".
        return str(value)[1:]
    raise ValueError(f'Invalid colour "{value}".')
