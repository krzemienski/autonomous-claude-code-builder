"""Validation engine — Iron Rule enforcement, evidence collection, platform validators."""

from .mock_detector import mock_detection_hook, scan_content_for_mocks, scan_file_path_for_test

__all__ = ["mock_detection_hook", "scan_content_for_mocks", "scan_file_path_for_test"]
