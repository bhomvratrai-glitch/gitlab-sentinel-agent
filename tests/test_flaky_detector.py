import pytest
from gitlab_sentinel.flaky_detector import FlakyTestDetector

def test_detect_async_timeout_flakiness():
    detector = FlakyTestDetector()
    traceback = """
    File "tests/test_worker.py", line 42, in test_async_fetch
        raise asyncio.exceptions.TimeoutError("Wait timeout exceeded")
    """
    report = detector.analyze_stacktrace("test_async_fetch", traceback, run_history_passes=9, run_history_fails=1)
    assert report is not None
    assert report.failure_type == "ASYNC_TIMEOUT"
    assert report.is_quarantined is True
    assert "backoff" in report.suggested_fix.lower()

def test_detect_network_race_flakiness():
    detector = FlakyTestDetector()
    traceback = "ConnectionRefusedError: [Errno 61] Connection refused on localhost:8080"
    report = detector.analyze_stacktrace("test_network_api", traceback, run_history_passes=3, run_history_fails=1)
    assert report is not None
    assert report.failure_type == "NETWORK_RACE"
    assert report.is_quarantined is True

def test_generate_quarantine_patch():
    detector = FlakyTestDetector()
    code = """
def test_flaky_payment():
    assert True
"""
    patched = detector.generate_quarantine_patch(code, "test_flaky_payment")
    assert "@pytest.mark.quarantine" in patched
    assert "def test_flaky_payment():" in patched
