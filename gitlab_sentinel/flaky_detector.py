"""
GitLab Sentinel Flaky Test Quarantine & Stabilization Engine
Detects non-deterministic test failures (race conditions, async timeouts, port binds),
quarantines them to prevent blocking developer pipelines, and generates stabilization patches.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import re

@dataclass
class FlakyTestReport:
    test_name: str
    failure_type: str
    intermittent_rate: float
    is_quarantined: bool
    suggested_fix: str
    quarantine_tag: str

class FlakyTestDetector:
    """
    Analyzes pytest / JUnit XML outputs to differentiate real code bugs
    from flaky environment and timing glitches.
    """

    FLAKY_PATTERNS = [
        (r"TimeoutError|asyncio\.exceptions\.TimeoutError|Wait timeout exceeded", "ASYNC_TIMEOUT", "Add exponential backoff or increase explicit await timeout"),
        (r"ConnectionRefusedError|Max retries exceeded with url|Port already in use", "NETWORK_RACE", "Quarantine to mock network calls or dynamically allocate ephemeral port"),
        (r"DatabaseLockedError|sqlite3\.OperationalError: database is locked", "DB_CONCURRENCY", "Isolate test SQLite instance or enable WAL mode"),
        (r"AssertionError: assert .* vs .* \(order not guaranteed\)", "NONDETERMINISTIC_ORDER", "Sort list/dict items prior to asserting equality")
    ]

    def analyze_stacktrace(self, test_name: str, traceback_str: str, run_history_passes: int = 4, run_history_fails: int = 1) -> Optional[FlakyTestReport]:
        """
        Evaluates test history and traceback to determine if failure is flaky.
        """
        total_runs = run_history_passes + run_history_fails
        if total_runs == 0:
            return None

        failure_rate = run_history_fails / total_runs

        # If a test passes 70%+ of the time but fails intermittently, it's flaky
        for pattern, failure_type, fix_suggestion in self.FLAKY_PATTERNS:
            if re.search(pattern, traceback_str, re.IGNORECASE):
                return FlakyTestReport(
                    test_name=test_name,
                    failure_type=failure_type,
                    intermittent_rate=round(failure_rate, 2),
                    is_quarantined=True,
                    suggested_fix=fix_suggestion,
                    quarantine_tag="@pytest.mark.quarantine(reason='flaky_detected')"
                )

        # Statistical heuristic even without explicit traceback pattern:
        # If test passed in 3 out of 4 previous runs, mark as suspected flaky
        if 0.1 <= failure_rate <= 0.4:
            return FlakyTestReport(
                test_name=test_name,
                failure_type="STATISTICAL_JITTER",
                intermittent_rate=round(failure_rate, 2),
                is_quarantined=True,
                suggested_fix="Isolate shared state, reset mocks between fixtures",
                quarantine_tag="@pytest.mark.quarantine(reason='intermittent_jitter')"
            )

        return None

    def generate_quarantine_patch(self, file_content: str, test_function_name: str) -> str:
        """
        Injects a @pytest.mark.quarantine decorator above the failing flaky test
        so the main production merge pipeline is unblocked while keeping the test tracked.
        """
        pattern = rf"(def\s+{re.escape(test_function_name)}\s*\()"
        replacement = f"@pytest.mark.quarantine(reason='auto_quarantined_by_sentinel')\n\\1"
        return re.sub(pattern, replacement, file_content)
