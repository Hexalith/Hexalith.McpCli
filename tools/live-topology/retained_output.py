"""Bound reads of completed subprocess output before decoding or redaction."""

import os
from typing import BinaryIO

OUTPUT_LIMIT = 4 * 1024 * 1024


def read_capped(stream: BinaryIO, limit: int) -> tuple[bytes | None, int]:
    size = os.fstat(stream.fileno()).st_size
    if size <= limit:
        stream.seek(0)
        content = stream.read(limit + 1)
        if len(content) <= limit:
            return content, 0
        size = max(len(content), os.fstat(stream.fileno()).st_size)
    return None, size
