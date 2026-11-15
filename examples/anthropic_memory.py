"""
Example: witnessing Anthropic native memory.

Anthropic injects an agent's persistent memory into the system prompt at session
start. The agent can't query it programmatically — but it can read the injected
context and hash it.

This example shows the pattern:
  1. At session start: hash the injected memory block, register a witness
  2. At session end (or anytime): re-hash and verify

In production you'd call this from your agent's session setup / teardown hooks.
"""

from cathedral_witness import WitnessClient, hash_memory

# Your Cathedral API key
client = WitnessClient(api_key="cathedral_your_key_here")

# ---------------------------------------------------------------------------
# Step 1: Session start — register a witness
# ---------------------------------------------------------------------------

# Anthropic injects memory into your system prompt. Extract it however you can
# (e.g. parse the [Memory] block from your system message).
injected_memory_block = """
[Memory]
- User prefers concise responses
- Working on Cathedral, an AI memory framework
- Last session: added A2A 1.0 support
"""

receipt = client.register(
    memory        = injected_memory_block,
    label         = "session-start-anthropic",
    source_system = "anthropic",
    metadata      = {"session_id": "abc123"},
)

print(f"Witness registered: {receipt.witness_id}")
print(f"Hash: {receipt.hash[:16]}...")
print(f"Verify later at: {receipt.verify_url}")

# ---------------------------------------------------------------------------
# Step 2: Later in the session — verify memory hasn't been tampered with
# ---------------------------------------------------------------------------

# Re-read your memory block (from context, tool call, wherever you have it)
current_memory_block = injected_memory_block  # unchanged in this example

result = client.verify(receipt.witness_id, current_memory_block)

if result.intact:
    print(f"Memory intact — no changes since {result.registered_at[:10]}")
else:
    print(f"WARNING: Memory has been modified!")
    print(f"  Registered: {result.registered_hash[:16]}...")
    print(f"  Current:    {result.current_hash[:16]}...")
    print(f"  {result.security_note}")
