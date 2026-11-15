# cathedral-witness

Cryptographic verification layer for any AI agent memory system.

Cathedral Witness lets agents prove their memory hasn't been tampered with — regardless of which memory provider they use. It works with Anthropic native memory, OpenAI memory, or any custom store.

Cathedral acts as a neutral witness: it **never sees your memory contents**, only a hash. You register a hash at a known-good point and verify against it at any time.

## Install

```bash
pip install cathedral-witness
```

## Quickstart

```python
from cathedral_witness import WitnessClient

client = WitnessClient(api_key="cathedral_your_key_here")

# Register a witness for your current memory state
receipt = client.register(
    memory        = my_memory_state,   # str, dict, list — any serialisable form
    label         = "session-start",
    source_system = "anthropic",       # or "openai", "gemini", "custom"
)

# Later: verify nothing changed
result = client.verify(receipt.witness_id, current_memory_state)

if result.intact:
    print("Memory verified — no unauthorised changes")
else:
    print(f"Memory modified: {result.security_note}")
```

## Why

Most AI memory providers are black boxes. You can't tell whether your agent's memories were modified between sessions — by a bug, a misconfigured pipeline, or a targeted attack.

The [arXiv survey on memory poisoning attacks](https://arxiv.org/abs/2602.14341) (Feb 2026) documents this as a real and growing threat surface. Silent memory modification is undetectable without an external reference point.

Cathedral Witness is that reference point. It's a lightweight notary — independent of your memory provider, with optional BCH blockchain anchoring for external verifiability.

## How it works

1. **Hash** — `WitnessClient.hash()` produces a canonical SHA-256 of any memory state. The same content always produces the same hash regardless of key ordering or whitespace.

2. **Register** — `client.register()` stores the hash + timestamp in Cathedral. Returns a `WitnessReceipt` with a `witness_id`.

3. **Verify** — `client.verify(witness_id, current_memory)` hashes your current state and compares it against the registered hash. Returns `VerifyResult.intact` (bool) and a full audit trail.

4. **Anchor** (optional) — set `anchor=True` to write the hash to the BCH blockchain for external, trustless verification.

## Works with any memory system

| Provider | Approach |
|---|---|
| Anthropic native memory | Hash the injected `[Memory]` block from your system prompt |
| OpenAI memory | `hash_memory_list(memories, content_key="content")` — order-independent |
| Custom / Cathedral | Pass your memory dict or string directly |

See `examples/` for provider-specific patterns.

## API key

Get a free Cathedral API key at [cathedral-ai.com](https://cathedral-ai.com). Free tier: 50 memories per agent, unlimited witness registrations.

## Endpoints used

| Method | Path | Description |
|---|---|---|
| `POST` | `/witness` | Register a memory hash |
| `GET` | `/witness/{id}` | Retrieve a witness record (public) |
| `POST` | `/witness/{id}/verify` | Verify current state against witness |
| `GET` | `/witness` | List your witness records |

## License

MIT
