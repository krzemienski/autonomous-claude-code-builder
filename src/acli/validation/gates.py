"""
Validation Gates
=================

Phase-gated validation with evidence collection.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .evidence import EvidenceCollector


@dataclass
class GateCriterion:
    """A single validation criterion."""

    description: str
    check_command: str  # Shell command that exits 0 on pass
    evidence_name: str


@dataclass
class ValidationGate:
    """A validation gate with multiple criteria."""

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
    timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class GateRunner:
    """Executes validation gates with evidence collection and review."""

    def __init__(
        self,
        evidence_collector: EvidenceCollector,
        streaming: Any = None,
    ) -> None:
        self.evidence = evidence_collector
        self.streaming = streaming

    async def run_gate(self, gate: ValidationGate) -> GateResult:
        """Run all criteria in a validation gate."""
        results: list[dict[str, Any]] = []
        all_passed = True

        if self.streaming:
            await self.streaming.handle_gate_start(
                gate.gate_id,
                f"{len(gate.criteria)} criteria",
            )

        for criterion in gate.criteria:
            path, exit_code = self.evidence.save_command_output(
                criterion.evidence_name,
                criterion.check_command,
            )
            passed = exit_code == 0
            if not passed:
                all_passed = False

            results.append({
                "criterion": criterion.description,
                "passed": passed,
                "evidence_path": str(path),
                "exit_code": exit_code,
            })

        status = "PASS" if all_passed else "FAIL"
        result = GateResult(
            gate_id=gate.gate_id,
            status=status,
            criteria_results=results,
        )

        if self.streaming:
            evidence_path = results[0]["evidence_path"] if results else ""
            await self.streaming.handle_gate_result(
                gate.gate_id, status, evidence_path
            )

        return result

    async def run_phase_gate(
        self, phase_gates: list[ValidationGate]
    ) -> GateResult:
        """Run all gates in a phase, stopping on first failure if blocking."""
        all_results: list[dict[str, Any]] = []
        overall_pass = True

        for gate in phase_gates:
            result = await self.run_gate(gate)
            all_results.extend(result.criteria_results)
            if result.status == "FAIL":
                overall_pass = False
                if gate.blocking:
                    break

        return GateResult(
            gate_id=f"phase-{phase_gates[0].gate_id}" if phase_gates else "phase",
            status="PASS" if overall_pass else "FAIL",
            criteria_results=all_results,
        )
