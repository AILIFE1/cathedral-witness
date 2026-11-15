"""
Example: generic memory witnessing pattern.

Use this template for any memory system not covered by the specific examples.
The only requirement: you can serialise your memory state into a string, dict,
or list that produces the same value when the memory hasn't changed.
"""

from cathedral_witness import WitnessClient

client = WitnessClient(api_key="cathedral_your_key_here")

# Your memory state — any serialisable form
memory_state = {
    "agent_name": "my-agent",
    "beliefs": [
        "The user wants fast, concise responses",
        "The current project is a memory verification layer",
    ],
    "goals": ["ship v0.1 by end of week"],
}

# Register at a known-good point
receipt = client.register(
    memory        = memory_state,
    label         = "post-onboarding-baseline",
    source_system = "custom",
    anchor        = True,  # BCH blockchain anchor for external verifiability
)

print(receipt)

# Verify later
result = client.verify(receipt.witness_id, memory_state)
assert result.intact, f"Memory tampered! {result.security_note}"
print("Memory verified intact.")
