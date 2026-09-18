"""PNG home-screen icon for the Emergency Card (white cross on red).

Served by Flask so it deploys as code. Binary icons cannot go through pa_sync
(CRLF would corrupt them), and a generated PNG works on both Android Chrome
and iOS Add to Home Screen, which will not use an SVG.
"""
from __future__ import annotations

import struct
import zlib
from functools import lru_cache

# First-aid red, distinct enough from the Dr. Health gradient icon that a
# paramedic reaching for the home screen hits the card, not the chat app.
_RED = (198, 40, 40, 255)
_WHITE = (255, 255, 255, 255)


def _chunk(tag: bytes, data: bytes) -> bytes:
    crc = zlib.crc32(tag + data) & 0xFFFFFFFF
    return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', crc)


def _png(width: int, rows) -> bytes:
    raw = b''.join(b'\x00' + row for row in rows)
    return (
        b'\x89PNG\r\n\x1a\n'
        + _chunk(b'IHDR', struct.pack('>IIBBBBB', width, width, 8, 6, 0, 0, 0))
        + _chunk(b'IDAT', zlib.compress(raw, 9))
        + _chunk(b'IEND', b'')
    )


@lru_cache(maxsize=8)
def emergency_icon_png(size: int) -> bytes:
    """Square RGBA PNG. `size` is 180 (iOS), 192 or 512 (Android / maskable)."""
    size = int(size)
    if size < 48 or size > 1024:
        raise ValueError('icon size out of range')
    half = (size - 1) / 2.0
    # Keep the cross inside the maskable safe zone (~80% of the square).
    arm = size * 0.28
    bar = max(size * 0.12, 4)
    ring_outer = size * 0.42
    ring_inner = size * 0.34
    rows = []
    for y in range(size):
        dy = y - half
        pixels = bytearray()
        for x in range(size):
            dx = x - half
            r2 = dx * dx + dy * dy
            on_cross = (abs(dx) <= bar / 2 and abs(dy) <= arm) or (
                abs(dy) <= bar / 2 and abs(dx) <= arm
            )
            on_ring = ring_inner * ring_inner <= r2 <= ring_outer * ring_outer
            colour = _WHITE if (on_cross or on_ring) else _RED
            pixels.extend(colour)
        rows.append(bytes(pixels))
    return _png(size, rows)


ALLOWED_SIZES = (180, 192, 512)
