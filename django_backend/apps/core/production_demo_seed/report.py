"""Reporting helpers for seed command output."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SeedRunReport:
    """Structured seed run summary."""

    profile: str
    dry_run: bool
    applied: bool = False
    counts: dict[str, int] = field(default_factory=dict)
    reused: dict[str, int] = field(default_factory=dict)
    lifecycle_paths: list[str] = field(default_factory=list)
    omitted_states: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def bump(self, key: str, amount: int = 1) -> None:
        self.counts[key] = self.counts.get(key, 0) + amount

    def reuse(self, key: str, amount: int = 1) -> None:
        self.reused[key] = self.reused.get(key, 0) + amount

    def as_dict(self) -> dict:
        return {
            "profile": self.profile,
            "dry_run": self.dry_run,
            "applied": self.applied,
            "counts": dict(sorted(self.counts.items())),
            "reused": dict(sorted(self.reused.items())),
            "lifecycle_paths": self.lifecycle_paths,
            "omitted_states": self.omitted_states,
            "warnings": self.warnings,
        }
