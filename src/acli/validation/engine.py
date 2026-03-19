"""Validation engine — orchestrates gates and evidence collection."""

from pathlib import Path
from typing import Any

from ..core.streaming import StreamingHandler
from .evidence import EvidenceCollector
from .gates import GateCriterion, GateResult, GateRunner, ValidationGate


class ValidationEngine:
    """Top-level validation orchestrator."""

    def __init__(self, project_dir: Path, streaming: StreamingHandler) -> None:
        self.project_dir = project_dir
        self.evidence_dir = project_dir / ".acli" / "evidence"
        self.collector = EvidenceCollector(self.evidence_dir)
        self.runner = GateRunner(self.collector, streaming)
        self._results: list[GateResult] = []

    async def validate_task(
        self,
        task: dict[str, Any],
        implementation_result: str,
    ) -> GateResult:
        """Create and run a validation gate for a task."""
        task_id = task.get("id", "unknown")
        criteria: list[GateCriterion] = []

        for i, check in enumerate(task.get("validation_checks", [])):
            criteria.append(GateCriterion(
                description=check.get("description", f"Check {i}"),
                check_command=check.get("command", "true"),
                evidence_name=f"{task_id}-check-{i}",
            ))

        if not criteria:
            # Default: just verify implementation_result is non-empty
            criteria.append(GateCriterion(
                description="Implementation produced output",
                check_command=f"test -n '{implementation_result[:20]}'",
                evidence_name=f"{task_id}-default",
            ))

        gate = ValidationGate(
            gate_id=f"gate-{task_id}",
            task_id=task_id,
            criteria=criteria,
        )
        result = await self.runner.run_gate(gate)
        self._results.append(result)
        return result

    async def validate_phase(self, phase: dict[str, Any]) -> GateResult:
        """Run cumulative validation for a phase."""
        phase_id = phase.get("id", "unknown")
        gates: list[ValidationGate] = []

        for task in phase.get("tasks", []):
            criteria = [
                GateCriterion(
                    description=f"Phase {phase_id} task check",
                    check_command=task.get("check_command", "true"),
                    evidence_name=f"phase-{phase_id}-{task.get('id', 'x')}",
                )
            ]
            gates.append(ValidationGate(
                gate_id=f"phase-{phase_id}-gate",
                task_id=task.get("id", "x"),
                criteria=criteria,
            ))

        result = await self.runner.run_phase_gate(gates)
        self._results.append(result)
        return result

    def get_all_results(self) -> list[GateResult]:
        """Return all stored gate results."""
        return list(self._results)

    def get_phase_summary(self) -> dict[str, Any]:
        """Summary with pass/fail counts."""
        passed = sum(1 for r in self._results if r.status == "PASS")
        failed = sum(1 for r in self._results if r.status == "FAIL")
        return {
            "total": len(self._results),
            "passed": passed,
            "failed": failed,
            "pass_rate": passed / max(len(self._results), 1),
        }
