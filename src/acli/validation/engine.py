"""
Validation Engine
==================

Orchestrates validation across the entire build.
"""

from pathlib import Path
from typing import Any

from ..core.streaming import StreamingHandler
from .evidence import EvidenceCollector
from .gates import GateResult, GateRunner, ValidationGate


class ValidationEngine:
    """
    Orchestrates validation across the entire build.

    Manages:
    - Per-task validation gates
    - Per-phase cumulative gates
    - Evidence directory management
    - PASS/FAIL tracking with streaming events
    """

    def __init__(
        self,
        project_dir: Path,
        streaming: StreamingHandler | None = None,
    ) -> None:
        self.project_dir = project_dir
        self._evidence_dir = project_dir / ".acli" / "evidence"
        self._collector = EvidenceCollector(self._evidence_dir)
        self._runner = GateRunner(self._collector, streaming)
        self._results: list[GateResult] = []

    async def validate_task(
        self, task: dict[str, Any], implementation_result: str
    ) -> GateResult:
        """Validate a completed task against its criteria."""
        gate = ValidationGate(
            gate_id=task.get("task_id", "unknown"),
            task_id=task.get("task_id", "unknown"),
            criteria=[],
            blocking=True,
        )
        result = await self._runner.run_gate(gate)
        self._results.append(result)
        return result

    async def validate_phase(self, phase: dict[str, Any]) -> GateResult:
        """Validate an entire phase."""
        gates = phase.get("gates", [])
        validation_gates = [
            ValidationGate(
                gate_id=g.get("gate_id", "unknown"),
                task_id=g.get("task_id", "unknown"),
                criteria=[],
                blocking=True,
            )
            for g in gates
        ]
        if not validation_gates:
            result = GateResult(
                gate_id=phase.get("phase_id", "unknown"),
                status="PASS",
            )
            self._results.append(result)
            return result

        result = await self._runner.run_phase_gate(validation_gates)
        self._results.append(result)
        return result

    def get_all_results(self) -> list[GateResult]:
        """Get all validation results collected so far."""
        return list(self._results)

    def get_phase_summary(self) -> dict[str, Any]:
        """Get summary of all phases validated."""
        total = len(self._results)
        passed = sum(1 for r in self._results if r.status == "PASS")
        failed = total - passed
        return {
            "total_gates": total,
            "passed": passed,
            "failed": failed,
            "all_pass": failed == 0,
        }
