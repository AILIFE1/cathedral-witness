"""
Canonical memory hashing utilities.

The hash_memory() function produces a stable SHA-256 from any memory
representation. The same memory state must always produce the same hash,
regardless of key ordering or whitespace, so normalisation is applied before hashing.
"""

import hashlib
import json
from typing import Any


def hash_memory(memory: Any) -> str:
    """
    Hash any memory state to a canonical SHA-256 hex string.

    Accepts:
    - str  — stripped and encoded directly
    - dict — JSON-normalised (sorted keys, compact separators)
    - list — JSON-normalised
    - anything else — str() coerced

    The hash is over the *content* only, not metadata like timestamps.
    """
    if isinstance(memory, str):
        normalised = memory.strip()
    elif isinstance(memory, (dict, list)):
        normalised = json.dumps(memory, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    else:
        normalised = str(memory)
    return hashlib.sha256(normalised.encode("utf-8")).hexdigest()


def hash_memory_list(memories: list[dict], content_key: str = "content") -> str:
    """
    Hash an ordered list of memory objects by their content fields.

    Extracts the `content_key` field from each item, sorts by content for
    stability (order-independent), and hashes the resulting canonical form.

    Use this when your memory provider returns a list of memory objects and
    you want a hash that is stable regardless of return order.
    """
    contents = sorted(
        str(m.get(content_key, m)) for m in memories
    )
    canonical = json.dumps(contents, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
