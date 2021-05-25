"""HTTP client to the pixel API."""
from collections import defaultdict
from typing import Union, Optional

import aiohttp

from .canvas import Canvas, Pixel
from .colours import Colour, parse_colour
from .ratelimits import RateLimiter


class Client:
    """HTTP client to the pixel API."""

    def __init__(
            self,
            token: str,
            base_url: str = 'https://pixels.pythondiscord.com/'):
        """Store the token and set up the client."""
        self.base_url = base_url
        self.headers = {'Authorization': 'Bearer ' + token}
        self.client = None
        # Cache canvas size, assuming it won't change.
        self.canvas_size = None
        self.ratelimits = defaultdict(RateLimiter)

    async def get_client(self) -> aiohttp.ClientSession:
        """Get or create the client session."""
        if (not self.client) or self.client.closed:
            self.client = aiohttp.ClientSession(headers=self.headers)
        return self.client

    async def request(
            self,
            method: str,
            endpoint: str,
            *,
            data: Optional[dict] = None,
            params: Optional[dict] = None,
            parse_json: bool = True) -> aiohttp.ClientResponse:
        """Make a call to an endpoint, respecting ratelimiting."""
        await self.ratelimits[endpoint].pause()
        client = await self.get_client()
        request = client.request(
            method, self.base_url + endpoint, json=data, params=params
        )
        async with request as response:
            self.ratelimits[endpoint].update(response.headers)
            if parse_json:
                return await response.json()
            else:
                return await response.read()

    async def put_pixel(
            self, x: int, y: int, colour: Union[int, str, Colour]) -> str:
        """Draw a pixel and return a message."""
        data = await self.request('POST', 'set_pixel', data={
            'x': x,
            'y': y,
            'rgb': parse_colour(colour)
        })
        return data['message']

    async def get_canvas_size(self) -> tuple[int, int]:
        """Get the size of the canvas (with caching)."""
        if self.canvas_size:
            return self.canvas_size
        data = await self.request('GET', 'get_size')
        return data['width'], data['height']

    async def get_canvas(self) -> Canvas:
        """Request the entire canvas."""
        data = await self.request('GET', 'get_pixels', parse_json=False)
        size = await self.get_canvas_size()
        return Canvas(size, data)

    async def get_pixel(self, x: int, y: int) -> Pixel:
        """Get a specific pixel of the canvas."""
        data = await self.request('GET', 'get_pixel', params={'x': x, 'y': y})
        raw = data['rgb']
        return Pixel(*(int(raw[i:i + 2], 16) for i in range(0, 6, 2)))

    async def close(self):
        """Close the underlying session."""
        await self.client.close()
