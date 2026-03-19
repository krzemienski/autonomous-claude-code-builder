"""Validation gates — criteria-based pass/fail with evidence."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from ..core.streaming import StreamingHandler
from .evidence import EvidenceCollector


@dataclass
class GateCriterion:
    """Single criterion within a validation gate."""

    description: str
    check_command: str  # Shell command that exits 0 on pass
    evidence_name: str


@dataclass
class ValidationGate:
    """A validation gate with multiple criteria."""

    gate_id: str
    task_id: str
    criteria: list[GateCriterion]
    blocking: bool = True


@dataclass
class GateResult:
    """Result of running a validation gate."""

    gate_id: str
    status: str  # "PASS" or "FAIL"
    criteria_results: list[dict[str, Any]]
    timestamp: datetime = field(default_factory=datetime.now)


class GateRunner:
    """Executes validation gates with real commands."""

    def __init__(
        self,
        evidence_collector: EvidenceCollector,
        streaming: StreamingHandler,
    ) -> None:
        self.collector = evidence_collector
        self.streaming = streaming

    async def run_gate(self, gate: ValidationGate) -> GateResult:
        """Execute all criteria in a gate and return result."""
        await self.streaming.handle_gate_start(
            gate.gate_id,
            f"{len(gate.criteria)} criteria",
        )

        results: list[dict[str, Any]] = []
        all_pass = True

        for criterion in gate.criteria:
            path, exit_code = self.collector.save_command_output(
                criterion.evidence_name, criterion.check_command,
            )
            passed = exit_code == 0
            if not passed:
                all_pass = False
            results.append({
                "description": criterion.description,
                "passed": passed,
                "exit_code": exit_code,
                "evidence_path": str(path),
            })

        status = "PASS" if all_pass else "FAIL"
        gate_result = GateResult(
            gate_id=gate.gate_id,
            status=status,
            criteria_results=results,
        )

        await self.streaming.handle_gate_result(
            gate.gate_id, status, str(self.collector.evidence_dir),
        )

        return gate_result

    async def run_phase_gate(self, gates: list[ValidationGate]) -> GateResult:
        """Run all gates and return composite result."""
        all_results: list[dict[str, Any]] = []
        all_pass = True

        for gate in gates:
            result = await self.run_gate(gate)
            all_results.extend(result.criteria_results)
            if result.status != "PASS":
                all_pass = False

        return GateResult(
            gate_id="phase_composite",
            status="PASS" if all_pass else "FAIL",
            criteria_results=all_results,
        )
