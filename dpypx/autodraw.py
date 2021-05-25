"""Tool for automatically drawing images."""
from __future__ import annotations

import logging

from PIL import Image

from .canvas import Pixel
from .client import Client


logger = logging.getLogger('dpypx')


class AutoDrawer:
    """Tool for automatically drawing images."""

    @classmethod
    def load_image(
            cls, client: Client, xy: tuple[int, int],
            image: Image.Image, scale: float = 1) -> AutoDrawer:
        """Draw from the pixels of an image."""
        if image.mode == 'RGBA':
            new_image = Image.new('RGB', image.size)
            new_image.paste(image, mask=image)
            image = new_image
        width = round(image.width * scale)
        height = round(image.height * scale)
        data = list(image.resize((width, height)).getdata())
        grid = [
            [Pixel(*pixel) for pixel in data[start:start + width]]
            for start in range(0, len(data), width)
        ]
        return cls(client, *xy, grid)

    @classmethod
    def load(cls, client: Client, data: str) -> AutoDrawer:
        """Draw from a string that specifies the pixels.

        `data` should be a multi-line string. The first two lines are the x
        and y coordinates of the top left of the image to draw. The second two
        are the width and height of the image. The rest of the lines are the
        pixels of the image, as hex codes (horizontal scanlines, left-to-right
        top-to-bottom).
        """
        lines = data.split('\n')
        x = int(lines.pop(0))
        y = int(lines.pop(0))
        width = int(lines.pop(0))
        height = int(lines.pop(0))
        grid = []
        for _ in range(height):
            row = []
            for _ in range(width):
                row.append(Pixel.from_hex(lines.pop(0)))
            grid.append(row)
        return cls(client, x, y, grid)

    def __init__(
            self, client: Client, x: int, y: int, grid: list[list[Pixel]]):
        """Store the plan."""
        self.client = client
        self.grid = grid
        # Top left coords.
        self.x0 = x
        self.y0 = y
        # Bottom right coords.
        self.x1 = x + len(self.grid[0])
        self.y1 = y + len(self.grid)

    async def draw(self):
        """Draw the pixels of the image."""
        canvas = await self.client.get_canvas()
        for x in range(self.x0, self.x1):
            for y in range(self.y0, self.y1):
                dx = x - self.x0
                dy = y - self.y0
                colour = self.grid[dy][dx]
                if canvas[x, y] == colour:
                    logger.debug(
                        f'Skipping already correct pixel at {x}, {y}.'
                    )
                    continue
                await self.client.put_pixel(x, y, colour)
                canvas = await self.client.get_canvas()
