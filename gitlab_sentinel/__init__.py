"""
GitLab Sentinel Agent: Autonomous DevSecOps & Closed-Loop CI/CD Self-Healing Engine.
"""

from .scanner import ASTSecurityScanner, VulnerabilityFinding
from .ci_runner import SandboxedCIRunner, ExecutionResult
from .remediator import SentinelRemediator
from .gitlab_client import GitLabClient
from .greenops import GreenOpsOptimizer, OptimizationResult
from .flaky_detector import FlakyTestDetector, FlakyTestReport
from .mcp_server import SentinelMCPServer
from .orchestrator import SentinelOrchestrator, PipelineExecutionReport

__version__ = "1.2.0"
__all__ = [
    "ASTSecurityScanner",
    "VulnerabilityFinding",
    "SandboxedCIRunner",
    "ExecutionResult",
    "SentinelRemediator",
    "GitLabClient",
    "GreenOpsOptimizer",
    "OptimizationResult",
    "FlakyTestDetector",
    "FlakyTestReport",
    "SentinelMCPServer",
    "SentinelOrchestrator",
    "PipelineExecutionReport"
]


