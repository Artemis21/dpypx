"""Utility for obeying ratelimits."""
from __future__ import annotations

import asyncio
import json
import logging
from collections import defaultdict
from typing import Optional


logger = logging.getLogger('dpypx')


class RateLimitEndpoint:
    """Ratelimiter for a specific endpoint."""

    def __init__(self):
        """Initialise fields to defaults."""
        self.ratelimited = True    # Not all endpoints are ratelimited.
        self.remaining = 1
        self.limit = None
        self.reset = None
        self.cooldown_reset = None

    def update(self, headers: dict[str, int]):
        """Update the ratelimiter based on the latest headers."""
        if 'Cooldown-Reset' in headers:
            self.remaining = 0
            self.cooldown_reset = int(headers['Cooldown-Reset'])
            return
        if 'Requests-Remaining' not in headers:
            self.ratelimited = False
            return
        self.remaining = int(headers['Requests-Remaining'])
        self.limit = int(headers['Requests-Limit'])
        self.reset = int(headers.get('Requests-Reset', self.reset))

    async def pause(self):
        """Pause before sending another request if necessary."""
        if self.cooldown_reset:
            logger.warning(f'Cooldown: Sleeping for {self.cooldown_reset}s.')
            await asyncio.sleep(self.cooldown_reset)
            self.cooldown_reset = None
            return
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

    def load(self, data: dict[str, int]):
        """Load stored ratelimit data."""
        self.remaining = data['remaining']
        self.limit = data['limit']
        self.reset = data['reset']
        self.cooldown_reset = data.get('cooldown_reset', 0)

    def dump(self) -> dict[str, int]:
        """Dump ratelimit data for storing."""
        return {
            'remaining': self.remaining,
            'limit': self.limit,
            'reset': self.reset,
            'cooldown_reset': self.cooldown_reset
        }


class RateLimiter:
    """Ratelimiters for all the endpoints."""

    def __init__(self, save_file: Optional[str] = None):
        """Load existing stored data."""
        self.ratelimits = defaultdict(RateLimitEndpoint)
        self.save_file = save_file
        self.save_data = None
        if save_file:
            self.load()

    def load(self):
        """Load save data."""
        try:
            with open(self.save_file) as f:
                self.save_data = json.load(f)
                for endpoint, data in self.save_data.items():
                    self.ratelimits[endpoint].load(data)
            logger.info(f'Loaded ratelimit save from {self.save_file}.')
        except FileNotFoundError:
            logger.warning(f'Could not find save data from {self.save_file}.')
            self.save_data = {}

    def save(self):
        """Save ratelimit data."""
        with open(self.save_file, 'w') as f:
            json.dump(self.save_data, f)

    def update(self, endpoint: str, headers: dict[str, int]):
        """Update the ratelimits for an endpoint with the latest headers."""
        limiter = self.ratelimits[endpoint]
        limiter.update(headers)
        if self.save_file:
            self.save_data[endpoint] = limiter.dump()
            self.save()

    async def pause(self, endpoint: str):
        """Pause before sending another request for an endpoint."""
        await self.ratelimits[endpoint].pause()
