"""Container for all the pixels on a canvas."""
import PIL.Image


class Canvas:
    """Container for all the pixels on a canvas."""

    def __init__(self, size: tuple[int, int], data: bytes):
        """Parse the raw canvas data."""
        self.width, self.height = size
        pixels = []
        for start_idx in range(0, len(data), 3):
            pixels.append(tuple(data[start_idx:start_idx + 3]))
        self.grid = [
            pixels[row * self.width:(row + 1) * self.width]
            for row in range(self.height)
        ]
        self.raw = data
        self.image = PIL.Image.frombytes('RGB', size, data)

    def show(self):
        """Display the image."""
        self.image.show()

    def save(self, path: str):
        """Save the image to a given file."""
        self.image.save(path)
