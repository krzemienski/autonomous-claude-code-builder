"""
Validation Engine
==================

Iron Rule enforcement, evidence collection, and platform-specific validators.
"""

from .engine import ValidationEngine
from .evidence import EvidenceCollector
from .gates import GateCriterion, GateResult, GateRunner, ValidationGate
from .mock_detector import mock_detection_hook, scan_content_for_mocks, scan_file_path_for_test

__all__ = [
    "ValidationEngine",
    "EvidenceCollector",
    "GateCriterion",
    "GateResult",
    "GateRunner",
    "ValidationGate",
    "mock_detection_hook",
    "scan_content_for_mocks",
    "scan_file_path_for_test",
]
