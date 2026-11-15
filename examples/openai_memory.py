"""
Example: witnessing OpenAI memory.

OpenAI's memory API returns a list of memory objects. This example shows
how to hash a list of memories in a stable, order-independent way and
register a witness.
"""

from cathedral_witness import WitnessClient, hash_memory_list

client = WitnessClient(api_key="cathedral_your_key_here")

# ---------------------------------------------------------------------------
# Simulated OpenAI memory API response
# (real call: client.beta.memory.list() or equivalent)
# ---------------------------------------------------------------------------

memories = [
    {"id": "mem_1", "content": "User is building an AI memory framework called Cathedral"},
    {"id": "mem_2", "content": "User prefers Python over JavaScript"},
    {"id": "mem_3", "content": "User is based in Taunton, UK"},
]

# hash_memory_list() is order-independent — stable even if OpenAI returns
# memories in a different order next time.
memory_hash = hash_memory_list(memories, content_key="content")

receipt = client.register(
    memory        = memory_hash,
    pre_hashed    = True,
    label         = "openai-memory-baseline",
    source_system = "openai",
)

print(f"Witness registered: {receipt.witness_id}")

# ---------------------------------------------------------------------------
# Later: re-fetch memories and verify
# ---------------------------------------------------------------------------

current_memories = [
    {"id": "mem_1", "content": "User is building an AI memory framework called Cathedral"},
    {"id": "mem_2", "content": "User prefers Python over JavaScript"},
    {"id": "mem_3", "content": "User is based in Taunton, UK"},
    # {"id": "mem_4", "content": "Injected by attacker"},  # uncomment to simulate poisoning
]

current_hash = hash_memory_list(current_memories, content_key="content")
result = client.verify(receipt.witness_id, current_hash, pre_hashed=True)

print(f"Verdict: {result.verdict}")  # "intact" or "modified"
