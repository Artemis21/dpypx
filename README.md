# DPYPX

A simple wrapper around [Python Discord Pixels](https://pixels.pythondiscord.com).

Requires Python 3.9+ (3.x where x >= 9).

Requires `pillow` and `aiohttp` from pip.

## Example

```python
import dpypx

# Create a client with your token.
client = dpypx.Client('my-auth-token')

# Download and save the canvas.
canvas = await client.get_canvas()
canvas.save('canvas.png')

# Draw a pixel.
await client.put_pixel(50, 10, 'cyan')
await client.put_pixel(1, 5, dpypx.Colour.BLURPLE)
await client.put_pixel(100, 4, '93FF00')
await client.put_pixel(44, 0, 0xFF0000)
```
