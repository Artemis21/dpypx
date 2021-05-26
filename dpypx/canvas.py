"""Container for all the pixels on a canvas."""
from __future__ import annotations

import PIL.Image

from .errors import CanvasFormatError


class Pixel:
    """A single pixel of the canvas."""

    @classmethod
    def from_hex(cls, hex: str) -> Pixel:
        """Load a pixel colour from a hex string."""
        hex = hex.lstrip('#')
        return cls(*(int(hex[i:i + 2], 16) for i in range(0, 6, 2)))

    def __init__(self, red: int, green: int, blue: int):
        """Store the pixel."""
        self.red, self.green, self.blue = red, green, blue

    def __str__(self) -> str:
        """Get the pixel as a hex string."""
        return f'#{self.red:0>2x}{self.green:0>2x}{self.blue:0>2x}'

    def __int__(self) -> int:
        """Get the pixel as a 3-byte int."""
        return self.red << 16 | self.green << 8 | self.blue

    @property
    def triple(self) -> tuple[int, int, int]:
        """Get the pixel as an RGB triple."""
        return self.red, self.green, self.blue

    def __eq__(self, other: Pixel) -> bool:
        """Check if this pixel holds the same value as another."""
        return self.triple == other.triple


class Canvas:
    """Container for all the pixels on a canvas."""

    def __init__(self, size: tuple[int, int], data: bytes):
        """Parse the raw canvas data."""
        self.width, self.height = size
        expected_length = self.width * self.height * 3
        actual_length = len(data)
        if expected_length != actual_length:
            raise CanvasFormatError(
                f'Expected {expected_length} bytes, got {actual_length} '
                'bytes.'
            )
        pixels = []
        for start_idx in range(0, len(data), 3):
            pixels.append(Pixel(*data[start_idx:start_idx + 3]))
        self.grid = [
            pixels[row * self.width:(row + 1) * self.width]
            for row in range(self.height)
        ]
        self.raw = data
        self.image = PIL.Image.frombytes('RGB', size, data)

    def __getitem__(self, xy: tuple[int, int]):
        """Get a pixel by coordinates."""
        x, y = xy
        return self.grid[y][x]

    def show(self):
        """Display the image."""
        self.image.show()

    def save(self, path: str):
        """Save the image to a given file."""
        self.image.save(path)
