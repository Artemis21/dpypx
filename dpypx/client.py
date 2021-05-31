"""HTTP client to the pixel API."""
from __future__ import annotations

import logging
from typing import Union, Optional

import aiohttp

from .canvas import Canvas, Pixel
from .colours import Colour, parse_colour
from .errors import (
    HttpClientError, MethodNotAllowedError, RatelimitedError, ServerError
)
from . import ratelimits


logger = logging.getLogger('dpypx')


class Client:
    """HTTP client to the pixel API."""

    def __init__(
            self,
            token: str,
            base_url: str = 'https://pixels.pythondiscord.com/',
            *,
            # Param exists for backwards compatibility, no longer needed.
            ratelimit_save_file: Optional[str] = None):
        """Store the token and set up the client."""
        self.base_url = base_url
        self.headers = {
            'Authorization': 'Bearer ' + token,
            'User-Agent': 'Artemis dpypx (Python/aiohttp)'
        }
        self.client = None
        self.ratelimits = ratelimits.RateLimiter(self)

    async def get_client(self) -> aiohttp.ClientSession:
        """Get or create the client session."""
        if (not self.client) or self.client.closed:
            self.client = aiohttp.ClientSession(headers=self.headers)
        return self.client

    async def send_request(
            self,
            method: str,
            endpoint: str,
            data: Optional[dict] = None,
            params: Optional[dict] = None) -> Union[dict, bytes, None]:
        """Make a basic HTTP request to the API."""
        logger.debug(
            f'Request: {method} {endpoint} data={data!r} params={params!r}.'
        )
        client = await self.get_client()
        request = client.request(
            method, self.base_url + endpoint, json=data, params=params
        )
        async with request as response:
            if 500 > response.status >= 400:
                if response.status == 405:
                    class_ = MethodNotAllowedError
                elif response.status == 429:
                    class_ = RatelimitedError
                else:
                    class_ = HttpClientError
                if method == 'HEAD':
                    detail = 'No body (HEAD request).'
                else:
                    data = await response.json()
                    detail = data.get('message', data.get(
                        'detail', 'No error message.'
                    ))
                raise class_(response.status, detail)
            if response.status >= 500:
                raise ServerError()
            self.ratelimits.update(endpoint, response.headers)
            if method == 'HEAD':
                return
            elif response.headers['Content-Type'] == 'application/json':
                return await response.json()
            else:
                return await response.read()

    async def request(
            self,
            method: str,
            endpoint: str,
            *,
            data: Optional[dict] = None,
            params: Optional[dict] = None,
            ratelimit_after: bool = False) -> Union[dict, bytes, None]:
        """Make a call to an endpoint, respecting ratelimiting."""
        retry = True
        while retry:
            # Always check before sending a request, even if we *want* to wait
            # after, sending a request and getting ratelimited is undesirable.
            await self.ratelimits.pause(endpoint)
            try:
                resp = await self.send_request(method, endpoint, data, params)
            except RatelimitedError:
                retry = True
            else:
                retry = False
            if ratelimit_after:
                await self.ratelimits.pause(endpoint)
        return resp

    async def put_pixel(
            self, x: int, y: int, colour: Union[int, str, Colour]) -> str:
        """Draw a pixel and return a message."""
        # Wait for ratelimits *after* making request, not before. This makes
        # sense because we don't know how the canvas may have changed by the
        # time we have finished waiting, whereas for GET endpoints, we want to
        # return the information as soon as it is given.
        data = await self.request('POST', 'set_pixel', data={
            'x': x,
            'y': y,
            'rgb': parse_colour(colour)
        }, ratelimit_after=True)
        logger.info('Success: {message}'.format(**data))
        return data['message']

    async def get_canvas_size(self) -> tuple[int, int]:
        """Get the size of the canvas."""
        data = await self.request('GET', 'get_size')
        return data['width'], data['height']

    async def get_canvas(self) -> Canvas:
        """Request the entire canvas."""
        data = await self.request('GET', 'get_pixels')
        size = await self.get_canvas_size()
        return Canvas(size, data)

    async def get_pixel(self, x: int, y: int) -> Pixel:
        """Get a specific pixel of the canvas."""
        data = await self.request('GET', 'get_pixel', params={'x': x, 'y': y})
        return Pixel.from_hex(data['rgb'])

    async def swap_pixels(
            self, xy0: tuple[int, int], xy1: tuple[int, int]) -> str:
        """Swap two pixels on the canvas."""
        data = await self.request('POST', 'swap_pixel', data={
            'origin': {
                'x': xy0[0],
                'y': xy0[1]
            },
            'dest': {
                'x': xy1[0],
                'y': xy1[1]
            }
        }, ratelimit_after=True)
        logger.info('Success: {message}'.format(**data))
        return data['message']

    async def close(self):
        """Close the underlying session."""
        await self.client.close()
