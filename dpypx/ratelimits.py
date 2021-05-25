"""Utility for obeying ratelimits."""
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

    def update(self, headers: dict[str, int]):
        """Update the ratelimiter based on the latest headers."""
        if 'Requests-Remaining' not in headers:
            self.ratelimited = False
            return
        self.remaining = headers['Requests-Remaining']
        self.limit = headers['Requests-Limit']
        self.reset = headers['Requests-Reset']

    async def pause(self):
        """Pause before sending another request if necessary."""
        if self.remaining or not self.ratelimited:
            logger.debug(
                f'Not sleeping, {self.remaining} remaining requests.'
            )
            return
        logger.warning(f'Sleeping for {self.reset}s.')
        await asyncio.sleep(self.reset)

    def load(self, data: dict[str, int]):
        """Load stored ratelimit data."""
        self.remaining = data['remaining']
        self.limit = data['limit']
        self.reset = data['reset']

    def dump(self) -> dict[str, int]:
        """Dump ratelimit data for storing."""
        return {
            'remaining': self.remaining,
            'limit': self.limit,
            'reset': self.reset
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
