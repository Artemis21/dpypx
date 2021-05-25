"""Utility for obeying ratelimits."""
import asyncio


class RateLimiter:
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
            return
        await asyncio.sleep(self.reset)
