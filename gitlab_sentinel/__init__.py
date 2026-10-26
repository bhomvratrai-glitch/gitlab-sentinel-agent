"""
GitLab Sentinel Agent: Autonomous DevSecOps & Closed-Loop CI/CD Self-Healing Engine.
"""

from .scanner import ASTSecurityScanner, VulnerabilityFinding
from .ci_runner import SandboxedCIRunner, ExecutionResult
from .remediator import SentinelRemediator
from .gitlab_client import GitLabClient

__version__ = "1.0.0"
__all__ = [
    "ASTSecurityScanner",
    "VulnerabilityFinding",
    "SandboxedCIRunner",
    "ExecutionResult",
    "SentinelRemediator",
    "GitLabClient"
]
