"""Pure-Python Douyin web ``a_bogus`` query signature.

The construction matches the public 2024–2026 webmssdk family: SM3 of the
unsigned query, body and UA, a packed environment vector, RC4, then a
custom alphabet.  Douyin rotates the exact mix over time; a rejected
request should be retried with a fresh browser Cookie rather than a
padded or replayed token.
"""

from __future__ import annotations

import hashlib
import random
import struct
import time
from typing import Mapping
from urllib.parse import urlencode


ALPHABET = "Dkdpgh4ZKsQB80/Mfvw36XI1R25-WUAlEi7NLboqYTOPuzmFjJnryx9HVGcaStCe="
UA_KEY = bytes((0x00, 0x01, 0x0E))


def _sm3(data: bytes) -> bytes:
    return hashlib.new("sm3", data).digest()


def _rc4(key: bytes, data: bytes) -> bytes:
    box = list(range(256))
    j = 0
    for i in range(256):
        j = (j + box[i] + key[i % len(key)]) % 256
        box[i], box[j] = box[j], box[i]
    i = j = 0
    out = bytearray(len(data))
    for n, byte in enumerate(data):
        i = (i + 1) % 256
        j = (j + box[i]) % 256
        box[i], box[j] = box[j], box[i]
        out[n] = byte ^ box[(box[i] + box[j]) % 256]
    return bytes(out)


def _encode(data: bytes, alphabet: str = ALPHABET) -> str:
    chars = []
    for i in range(0, len(data), 3):
        block = data[i:i + 3]
        n = block[0] << 16
        if len(block) > 1:
            n |= block[1] << 8
        if len(block) > 2:
            n |= block[2]
        chars.append(alphabet[(n >> 18) & 63])
        chars.append(alphabet[(n >> 12) & 63])
        chars.append(alphabet[(n >> 6) & 63] if len(block) > 1 else "=")
        chars.append(alphabet[n & 63] if len(block) > 2 else "=")
    return "".join(chars).rstrip("=")


def _ua_digest(user_agent: str) -> bytes:
    encoded = _rc4(UA_KEY, user_agent.encode("utf-8"))
    return _sm3(encoded)


def _pack_env(*, timestamp: int, params_hash: bytes, body_hash: bytes,
              ua_hash: bytes) -> bytes:
    salt = random.randint(0, 0xFFFFFFFF)
    vector = bytearray(40)
    vector[0:4] = struct.pack(">I", timestamp)
    vector[4:8] = struct.pack(">I", salt)
    vector[8:24] = params_hash[:16]
    vector[24:32] = body_hash[:8]
    vector[32:40] = ua_hash[:8]
    checksum = 0
    for value in vector:
        checksum ^= value
    return bytes(vector) + bytes((checksum & 0xFF,))


def encode_a_bogus(*, query: str, user_agent: str, body: str | bytes = "",
                   timestamp: int | None = None) -> str:
    """Return a fresh ``a_bogus`` for an unsigned Douyin web query string."""
    if not user_agent:
        raise ValueError("a_bogus 需要完整 User-Agent")
    if isinstance(body, bytes):
        body_bytes = body
    else:
        body_bytes = str(body or "").encode("utf-8")
    now = int(timestamp if timestamp is not None else time.time())
    params_hash = _sm3(query.encode("utf-8"))
    body_hash = _sm3(body_bytes)
    ua_hash = _ua_digest(user_agent)
    payload = _pack_env(
        timestamp=now, params_hash=params_hash, body_hash=body_hash, ua_hash=ua_hash,
    )
    key = bytes((random.randint(0, 255), random.randint(0, 255)))
    cipher = key + _rc4(key, payload)
    return _encode(cipher)


def query_string(values: Mapping[str, object]) -> str:
    pairs = [(str(key), "" if value is None else str(value)) for key, value in values.items()]
    return urlencode(pairs, safe="=/-_.~")


__all__ = ["encode_a_bogus", "query_string"]
