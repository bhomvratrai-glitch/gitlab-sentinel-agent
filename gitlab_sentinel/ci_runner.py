import subprocess
import time
import os
import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict

@dataclass
class FailureTrace:
    file_path: str
    line_number: int
    error_type: str
    message: str
    full_trace: str

@dataclass
class ExecutionResult:
    success: bool
    exit_code: int
    stdout: str
    stderr: str
    duration_seconds: float
    failures: List[FailureTrace] = field(default_factory=list)

class SandboxedCIRunner:
    """
    Hermetic test runner simulating a GitLab CI job environment.
    Executes unit test suites, isolates environments, and extracts stack traces.
    """
    def __init__(self, timeout_seconds: int = 30):
        self.timeout_seconds = timeout_seconds

    def run_tests(self, cwd: str, command: Optional[List[str]] = None) -> ExecutionResult:
        cmd = command or ["python3", "-m", "pytest", "-v"]
        start_time = time.time()

        env = os.environ.copy()
        env["GITLAB_CI"] = "true"
        env["CI"] = "true"
        env["PYTHONDONTWRITEBYTECODE"] = "1"

        try:
            proc = subprocess.run(
                cmd,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                env=env
            )
            duration = time.time() - start_time
            stdout = proc.stdout
            stderr = proc.stderr
            exit_code = proc.returncode
            success = (exit_code == 0)

            failures = self._parse_pytest_failures(stdout + "\n" + stderr)

            return ExecutionResult(
                success=success,
                exit_code=exit_code,
                stdout=stdout,
                stderr=stderr,
                duration_seconds=round(duration, 3),
                failures=failures
            )
        except subprocess.TimeoutExpired as e:
            duration = time.time() - start_time
            return ExecutionResult(
                success=False,
                exit_code=124,
                stdout=e.stdout or "",
                stderr=f"CI Job timed out after {self.timeout_seconds} seconds.",
                duration_seconds=round(duration, 3),
                failures=[FailureTrace(
                    file_path="timeout",
                    line_number=0,
                    error_type="TimeoutExpired",
                    message=f"Job exceeded {self.timeout_seconds}s execution limit",
                    full_trace=""
                )]
            )

    def _parse_pytest_failures(self, output: str) -> List[FailureTrace]:
        failures: List[FailureTrace] = []
        # Match standard pytest failure lines: FAILED tests/test_foo.py::test_bar - AssertionError: ...
        pattern = re.compile(r"FAILED\s+([^\s:]+)::([^\s\-]+)\s*-\s*([A-Za-z0-9_]+Error|[A-Za-z0-9_]+Exception):\s*(.*)")
        for line in output.splitlines():
            match = pattern.search(line)
            if match:
                file_path = match.group(1)
                test_name = match.group(2)
                err_type = match.group(3)
                msg = match.group(4)
                failures.append(FailureTrace(
                    file_path=file_path,
                    line_number=1,
                    error_type=err_type,
                    message=f"{test_name}: {msg}",
                    full_trace=line
                ))
        return failures
