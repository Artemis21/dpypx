"""Utility for obeying ratelimits."""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Optional

from . import client
from .errors import MethodNotAllowedError


logger = logging.getLogger('dpypx')


@dataclass
class RateLimitEndpoint:
    """Ratelimiter for a specific endpoint."""

    client: client.Client
    endpoint: str
    # We don't care about Requests-Period, we just dynamically wait based on
    # Requests-Reset.
    ratelimited: Optional[bool] = None
    limit: Optional[int] = None
    remaining: Optional[int] = None
    reset: Optional[float] = None
    cooldown_reset: Optional[int] = None

    def update(self, headers: dict[str, int]):
        """Update the ratelimiter based on the latest headers."""
        if 'Cooldown-Reset' in headers:
            self.remaining = 0
            self.cooldown_reset = int(headers['Cooldown-Reset'])
            return
        if 'Requests-Remaining' not in headers:
            self.ratelimited = False
            return
        self.ratelimited = True
        self.remaining = int(headers['Requests-Remaining'])
        self.limit = int(headers['Requests-Limit'])
        self.reset = float(headers['Requests-Reset'])

    async def pause(self):
        """Pause before sending another request if necessary."""
        if self.cooldown_reset:
            logger.error(f'Cooldown: Sleeping for {self.cooldown_reset}s.')
            await asyncio.sleep(self.cooldown_reset)
            self.cooldown_reset = None
            return
        if self.ratelimited is None:
            await self.check_limits()
        if not self.ratelimited:
            return
        if self.remaining:
            logger.debug(
                f'Not sleeping, {self.remaining} remaining requests.'
            )
            return
        if self.reset:
            logger.warning(f'Sleeping for {self.reset}s.')
            await asyncio.sleep(self.reset)
            self.remaining = self.limit

    async def check_limits(self):
        """Check the ratelimits with a HEAD request."""
        try:
            # Client.send_request will call self.update.
            await self.client.send_request('HEAD', self.endpoint)
        except MethodNotAllowedError:
            self.ratelimited = False


class RateLimiter:
    """Ratelimiters for all the endpoints."""

    def __init__(self, client: client.Client):
        """Set up the ratelimiter."""
        self.client = client
        self.ratelimits = {}

    def __getitem__(self, endpoint: str) -> RateLimitEndpoint:
        """Get the ratelimiter for a specific endpoint."""
        if endpoint not in self.ratelimits:
            self.ratelimits[endpoint] = RateLimitEndpoint(
                self.client, endpoint
            )
        return self.ratelimits[endpoint]

    def update(self, endpoint: str, headers: dict[str, int]):
        """Update the ratelimits for an endpoint with the latest headers."""
        self[endpoint].update(headers)

    async def pause(self, endpoint: str):
        """Pause before sending another request for an endpoint."""
        await self[endpoint].pause()
