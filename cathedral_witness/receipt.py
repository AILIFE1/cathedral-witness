from dataclasses import dataclass
from typing import Optional


@dataclass
class WitnessReceipt:
    witness_id: str
    hash: str
    label: str
    source_system: str
    registered_at: str
    bch_anchor: Optional[str]
    verify_url: str

    def __str__(self) -> str:
        anchor = f" | BCH: {self.bch_anchor[:16]}..." if self.bch_anchor else ""
        return f"WitnessReceipt({self.witness_id[:12]}... | {self.label} | {self.registered_at[:10]}{anchor})"


@dataclass
class VerifyResult:
    witness_id: str
    label: str
    source_system: str
    registered_at: str
    verified_at: str
    elapsed_days: Optional[int]
    match: bool
    verdict: str          # "intact" or "modified"
    registered_hash: str
    current_hash: str
    bch_anchor: Optional[str]
    security_note: str

    @property
    def intact(self) -> bool:
        return self.match

    def __str__(self) -> str:
        icon = "OK" if self.match else "MODIFIED"
        return f"VerifyResult[{icon}] {self.label} ({self.elapsed_days}d ago)"
