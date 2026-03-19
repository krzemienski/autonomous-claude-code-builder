"""Validation engine orchestrating gates across the build."""

from pathlib import Path
from typing import Any

from .evidence import EvidenceCollector
from .gates import GateCriterion, GateResult, GateRunner, ValidationGate


class ValidationEngine:
    """
    Orchestrates validation across the entire build.

    Manages per-task gates, per-phase gates, evidence directories,
    and PASS/FAIL tracking.
    """

    def __init__(self, project_dir: Path, streaming: Any = None) -> None:
        """Initialize validation engine with project directory and optional streaming handler."""
        self.project_dir = project_dir
        self.evidence_dir = project_dir / "evidence"
        self.collector = EvidenceCollector(self.evidence_dir)
        self.runner = GateRunner(self.collector, streaming)
        self._results: list[GateResult] = []

    async def validate_task(
        self, task: dict[str, Any], implementation_result: str = "",
    ) -> GateResult:
        """Validate a task implementation against its gate criteria."""
        task_id = task.get("task_id", "unknown")
        gate_id = task.get("gate_id", f"VG-{task_id}")
        criteria = []

        for criterion_spec in task.get("criteria", []):
            criteria.append(GateCriterion(
                description=criterion_spec.get("description", ""),
                check_command=criterion_spec.get("check_command", "true"),
                evidence_name=criterion_spec.get("evidence_name", f"{gate_id}-check"),
            ))

        gate = ValidationGate(gate_id=gate_id, task_id=task_id, criteria=criteria)
        result = await self.runner.run_gate(gate)
        self._results.append(result)
        return result

    async def validate_phase(self, phase: dict[str, Any]) -> GateResult:
        """Validate an entire phase with cumulative checks."""
        phase_id = phase.get("phase_id", "unknown")
        gates = []

        for gate_spec in phase.get("gates", []):
            criteria = [
                GateCriterion(
                    description=c.get("description", ""),
                    check_command=c.get("check_command", "true"),
                    evidence_name=c.get("evidence_name", "check"),
                )
                for c in gate_spec.get("criteria", [])
            ]
            gates.append(ValidationGate(
                gate_id=gate_spec.get("gate_id", f"PG-{phase_id}"),
                task_id=phase_id,
                criteria=criteria,
            ))

        result = await self.runner.run_phase_gate(gates) if gates else GateResult(
            gate_id=f"PG-{phase_id}", status="PASS",
        )
        self._results.append(result)
        return result

    def get_all_results(self) -> list[GateResult]:
        """Return all gate results."""
        return list(self._results)

    def get_phase_summary(self) -> dict[str, Any]:
        """Return summary of all phases."""
        total = len(self._results)
        passed = sum(1 for r in self._results if r.status == "PASS")
        return {
            "total_gates": total,
            "passed": passed,
            "failed": total - passed,
            "all_pass": passed == total,
        }
