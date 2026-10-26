import pytest
from gitlab_sentinel.ci_runner import SandboxedCIRunner

def test_runner_echo_success(tmp_path):
    runner = SandboxedCIRunner(timeout_seconds=5)
    res = runner.run_tests(cwd=str(tmp_path), command=["python3", "-c", "print('hello from CI')"])
    assert res.success is True
    assert res.exit_code == 0
    assert "hello from CI" in res.stdout
    assert res.duration_seconds >= 0

def test_runner_failure(tmp_path):
    runner = SandboxedCIRunner(timeout_seconds=5)
    res = runner.run_tests(cwd=str(tmp_path), command=["python3", "-c", "import sys; sys.exit(42)"])
    assert res.success is False
    assert res.exit_code == 42

def test_failure_trace_parsing():
    runner = SandboxedCIRunner()
    sample_output = """
============================= test session starts ==============================
FAILED tests/test_math.py::test_division - ZeroDivisionError: division by zero
============================== 1 failed in 0.05s ===============================
"""
    traces = runner._parse_pytest_failures(sample_output)
    assert len(traces) == 1
    assert traces[0].file_path == "tests/test_math.py"
    assert traces[0].error_type == "ZeroDivisionError"
    assert "division by zero" in traces[0].message
