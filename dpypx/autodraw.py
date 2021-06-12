"""Tool for automatically drawing images."""
from __future__ import annotations

import asyncio
import logging
from typing import Iterator, Optional

from PIL import Image

from .canvas import Canvas, Pixel
from .client import Client
from .errors import EndpointDisabledError


logger = logging.getLogger('dpypx')


class AutoDrawer:
    """Tool for automatically drawing images."""

    @classmethod
    def load_image(
            cls, client: Client, xy: tuple[int, int],
            image: Image.Image, scale: float = 1) -> AutoDrawer:
        """Draw from the pixels of an image."""
        image = image.convert(mode="RGBA")
        width = round(image.width * scale)
        height = round(image.height * scale)
        # Since the image is only loaded once we can afford to use a high
        # quality filter.
        resized = image.resize((width, height), Image.LANCZOS)
        data = list(resized.getdata())
        grid = [
            [
                (Pixel(*pixel[:3]), pixel[3] > 127)
                for pixel in data[start:start + width]
            ]
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
                row.append((Pixel.from_hex(lines.pop(0)), True))
            grid.append(row)
        return cls(client, x, y, grid)

    def __init__(
            self, client: Client, x: int, y: int, grid: list[list[Pixel]]):
        """Store the plan."""
        self.client = client
        self.grid = grid
        self.canvas: Optional[Canvas] = None
        # Top left coords.
        self.x0 = x
        self.y0 = y
        # Bottom right coords.
        self.x1 = x + len(self.grid[0])
        self.y1 = y + len(self.grid)

    async def update_canvas(self):
        """Update our cache of the canvas, if possible."""
        try:
            self.canvas = await self.client.get_canvas()
        except EndpointDisabledError:
            logger.warning('Unable to get canvas (endpoint disabled).')

    def _iter_coords(
            self, top_to_bottom: bool = False) -> Iterator[tuple[int, int]]:
        """Iterate over the coordinates of the image."""
        if top_to_bottom:
            for x in range(self.x0, self.x1):
                for y in range(self.y0, self.y1):
                    yield x, y
        else:
            for y in range(self.y0, self.y1):
                for x in range(self.x0, self.x1):
                    yield x, y

    async def check_pixel(self, x: int, y: int) -> bool:
        """Draw a pixel if not already drawn.

        Returns True if the pixel was not already drawn.
        """
        colour, opaque = self.grid[y - self.y0][x - self.x0]
	if not opaque:
            logger.debug(f"Skipping transparent pixel at {x}, {y}.")
            return False
        if self.canvas and self.canvas[x, y] == colour:
            logger.debug(f'Skipping already correct pixel at {x}, {y}.')
            return False
        await self.client.put_pixel(x, y, colour)
        return True

    async def draw(self, top_to_bottom: bool = False):
        """Draw the pixels of the image, attempting each pixel max. once."""
        await self.update_canvas()
        for x, y in self._iter_coords(top_to_bottom):
            if await self.check_pixel(x, y):
                await self.update_canvas()

    async def draw_and_fix(
            self,
            forever: bool = True,
            top_to_bottom: bool = False):
        """Draw the pixels of the image, prioritise fixing existing ones."""
        work_to_do = True
        while work_to_do:
            await self.update_canvas()
            work_to_do = False
            for x, y in self._iter_coords(top_to_bottom):
                if await self.check_pixel(x, y):
                    work_to_do = True
                    await self.update_canvas()
                    break
            if forever and not work_to_do:
                logger.info('Entire image is correct, waiting 1s to loop.')
                await asyncio.sleep(1)
                work_to_do = True
