"""Validation gate definitions and runner."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from .evidence import EvidenceCollector


@dataclass
class GateCriterion:
    """A single criterion within a validation gate."""
    description: str
    check_command: str  # Shell command that exits 0 on pass
    evidence_name: str


@dataclass
class ValidationGate:
    """A validation gate with blocking semantics."""
    gate_id: str
    task_id: str
    criteria: list[GateCriterion] = field(default_factory=list)
    blocking: bool = True


@dataclass
class GateResult:
    """Result of running a validation gate."""
    gate_id: str
    status: str  # "PASS" or "FAIL"
    criteria_results: list[dict[str, Any]] = field(default_factory=list)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


class GateRunner:
    """Executes validation gates with evidence collection."""

    def __init__(self, evidence_collector: EvidenceCollector, streaming: Any = None) -> None:
        """Initialize gate runner with evidence collector and optional streaming handler."""
        self.collector = evidence_collector
        self.streaming = streaming

    async def run_gate(self, gate: ValidationGate) -> GateResult:
        """Run a single validation gate, checking all criteria."""
        results = []
        all_pass = True

        for criterion in gate.criteria:
            path, exit_code = self.collector.save_command_output(
                criterion.evidence_name, criterion.check_command,
            )
            passed = exit_code == 0
            if not passed:
                all_pass = False
            results.append({
                "criterion": criterion.description,
                "passed": passed,
                "evidence_path": str(path),
                "exit_code": exit_code,
            })

        return GateResult(
            gate_id=gate.gate_id,
            status="PASS" if all_pass else "FAIL",
            criteria_results=results,
        )

    async def run_phase_gate(self, phase_gates: list[ValidationGate]) -> GateResult:
        """Run multiple gates as a phase gate. All must pass."""
        all_results = []
        all_pass = True

        for gate in phase_gates:
            result = await self.run_gate(gate)
            all_results.extend(result.criteria_results)
            if result.status != "PASS":
                all_pass = False

        return GateResult(
            gate_id=f"phase_{phase_gates[0].gate_id}" if phase_gates else "phase_unknown",
            status="PASS" if all_pass else "FAIL",
            criteria_results=all_results,
        )
