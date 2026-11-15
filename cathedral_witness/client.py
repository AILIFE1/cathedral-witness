"""
WitnessClient — register and verify memory state hashes with Cathedral.

Cathedral acts as a neutral third-party witness. It never receives memory
contents — only hashes. This means it works with any memory provider.
"""

import json
import urllib.error
import urllib.request
from typing import Any, Optional

from .hash import hash_memory, hash_memory_list
from .receipt import VerifyResult, WitnessReceipt

DEFAULT_BASE = "https://cathedral-ai.com"


class WitnessClient:
    """
    Client for Cathedral's witness endpoints.

    Usage::

        from cathedral_witness import WitnessClient

        client = WitnessClient(api_key="cathedral_...")

        # Register a witness for your current memory state
        receipt = client.register(my_memories, label="session-start", source_system="anthropic")

        # ... later, after the session ...

        result = client.verify(receipt.witness_id, my_current_memories)
        if result.intact:
            print("Memory unchanged")
        else:
            print("Memory has been modified")
    """

    def __init__(self, api_key: str, base_url: str = DEFAULT_BASE, timeout: int = 10):
        self.api_key  = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout  = timeout
        self._headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type":  "application/json",
            "User-Agent":    "cathedral-witness/0.1.0",
        }

    # ------------------------------------------------------------------
    # Hashing helpers (delegated to hash module, exposed here for convenience)
    # ------------------------------------------------------------------

    def hash(self, memory: Any) -> str:
        """Hash any memory state to a canonical SHA-256 hex string."""
        return hash_memory(memory)

    def hash_list(self, memories: list[dict], content_key: str = "content") -> str:
        """Hash an ordered list of memory objects, stable regardless of return order."""
        return hash_memory_list(memories, content_key=content_key)

    # ------------------------------------------------------------------
    # Core API
    # ------------------------------------------------------------------

    def register(
        self,
        memory: Any,
        label:         str  = "",
        source_system: str  = "unknown",
        metadata:      Optional[dict] = None,
        anchor:        bool = False,
        pre_hashed:    bool = False,
    ) -> WitnessReceipt:
        """
        Register a witness for the current state of any memory corpus.

        Parameters
        ----------
        memory        : The memory to witness. Can be a string, dict, list, or any
                        JSON-serialisable object. If pre_hashed=True, pass the hex hash directly.
        label         : Human-readable label for this witness (e.g. "session-start").
        source_system : Memory provider name: "anthropic", "openai", "gemini", "custom".
        metadata      : Optional dict of extra metadata stored alongside the witness (not hashed).
        anchor        : If True, Cathedral will anchor the hash on the BCH blockchain.
        pre_hashed    : If True, `memory` is treated as an already-computed hex hash string.
        """
        h = memory if pre_hashed else hash_memory(memory)
        payload = {
            "hash":          h,
            "label":         label,
            "source_system": source_system,
            "anchor":        anchor,
        }
        if metadata:
            payload["metadata"] = metadata

        data = self._post("/witness", payload)
        return WitnessReceipt(
            witness_id    = data["witness_id"],
            hash          = data["hash"],
            label         = data["label"],
            source_system = data["source_system"],
            registered_at = data["registered_at"],
            bch_anchor    = data.get("bch_anchor"),
            verify_url    = data.get("verify_url", f"{self.base_url}/witness/{data['witness_id']}"),
        )

    def verify(
        self,
        witness_id: str,
        current_memory: Any,
        pre_hashed: bool = False,
    ) -> VerifyResult:
        """
        Verify the current state of your memory against a registered witness.

        Parameters
        ----------
        witness_id      : The witness_id from a prior WitnessReceipt.
        current_memory  : Current memory state to compare. Same type rules as register().
        pre_hashed      : If True, current_memory is treated as an already-computed hex hash.

        Returns a VerifyResult with .intact (bool) and .verdict ("intact" | "modified").
        """
        h = current_memory if pre_hashed else hash_memory(current_memory)
        data = self._post(f"/witness/{witness_id}/verify", {"hash": h})
        return VerifyResult(
            witness_id      = data["witness_id"],
            label           = data["label"],
            source_system   = data["source_system"],
            registered_at   = data["registered_at"],
            verified_at     = data["verified_at"],
            elapsed_days    = data.get("elapsed_days"),
            match           = data["match"],
            verdict         = data["verdict"],
            registered_hash = data["registered_hash"],
            current_hash    = data["current_hash"],
            bch_anchor      = data.get("bch_anchor"),
            security_note   = data.get("security_note", ""),
        )

    def get(self, witness_id: str) -> dict:
        """Retrieve a witness record by ID. No auth required (public endpoint)."""
        return self._get(f"/witness/{witness_id}", auth=False)

    def list(self, source_system: Optional[str] = None, limit: int = 50) -> list[WitnessReceipt]:
        """List your registered witness records."""
        params = f"?limit={limit}"
        if source_system:
            params += f"&source_system={source_system}"
        data = self._get(f"/witness{params}")
        return [
            WitnessReceipt(
                witness_id    = r["witness_id"],
                hash          = r["hash"],
                label         = r["label"],
                source_system = r["source_system"],
                registered_at = r["registered_at"],
                bch_anchor    = r.get("bch_anchor"),
                verify_url    = f"{self.base_url}/witness/{r['witness_id']}",
            )
            for r in data.get("records", [])
        ]

    # ------------------------------------------------------------------
    # HTTP internals
    # ------------------------------------------------------------------

    def _post(self, path: str, payload: dict) -> dict:
        url  = self.base_url + path
        body = json.dumps(payload).encode("utf-8")
        req  = urllib.request.Request(url, data=body, headers=self._headers, method="POST")
        return self._send(req)

    def _get(self, path: str, auth: bool = True) -> dict:
        url     = self.base_url + path
        headers = self._headers if auth else {k: v for k, v in self._headers.items() if k != "Authorization"}
        req     = urllib.request.Request(url, headers=headers, method="GET")
        return self._send(req)

    def _send(self, req: urllib.request.Request) -> dict:
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            try:
                detail = json.loads(body).get("detail", body)
            except Exception:
                detail = body
            raise WitnessError(e.code, detail) from None
        except urllib.error.URLError as e:
            raise WitnessError(0, str(e.reason)) from None


class WitnessError(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail      = detail
        super().__init__(f"HTTP {status_code}: {detail}")
