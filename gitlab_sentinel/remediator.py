import re
from typing import List, Dict, Any, Optional
from .scanner import VulnerabilityFinding
from .ci_runner import ExecutionResult, FailureTrace

class SentinelRemediator:
    """
    Autonomous remediation engine that generates surgical fixes for AST security findings
    and CI pipeline test failures.
    """
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key

    def remediate_security_finding(self, code: str, finding: VulnerabilityFinding) -> str:
        """
        Applies a surgical fix to source code based on AST vulnerability classification.
        """
        lines = code.splitlines()
        idx = finding.line_number - 1

        if idx < 0 or idx >= len(lines):
            return code

        line = lines[idx]

        # Fix CWE-78: Command Injection via os.system / subprocess shell=True
        if finding.cwe == "CWE-78":
            if "os.system(" in line:
                # Replace os.system(f"echo {var}") with subprocess.run(['echo', var], check=True)
                match = re.search(r"os\.system\((.*?)\)", line)
                if match:
                    arg = match.group(1).strip()
                    lines[idx] = line.replace(
                        f"os.system({arg})",
                        f"subprocess.run({arg}.split(), shell=False, check=True)"
                    )
            elif "shell=True" in line:
                lines[idx] = line.replace("shell=True", "shell=False")

        # Fix CWE-89: SQL Injection via string formatting
        elif finding.cwe == "CWE-89":
            # Replace cursor.execute(f"SELECT ... WHERE id = {val}") with parameterized
            if "execute(" in line and "f\"" in line:
                lines[idx] = re.sub(
                    r'execute\(f"(.*?)WHERE\s+([A-Za-z0-9_]+)\s*=\s*\{([A-Za-z0-9_]+)\}"\)',
                    r'execute("\1WHERE \2 = ?", (\3,))',
                    line
                )

        # Fix CWE-94: Code Injection via eval()
        elif finding.cwe == "CWE-94":
            if "eval(" in line:
                lines[idx] = line.replace("eval(", "ast.literal_eval(")

        # Fix CWE-798: Hardcoded Credentials
        elif finding.cwe == "CWE-798":
            match = re.search(r'([A-Za-z0-9_]+)\s*=\s*["\']([^"\']+)["\']', line)
            if match:
                var_name = match.group(1)
                lines[idx] = f'{var_name} = os.getenv("{var_name.upper()}", "")'

        return "\n".join(lines)

    def generate_mr_audit_report(
        self,
        findings: List[VulnerabilityFinding],
        test_result: ExecutionResult,
        healed_count: int = 0
    ) -> str:
        """
        Generates a rich GitLab Merge Request comment summarizing DevSecOps checks.
        """
        status_emoji = "✅" if not findings and test_result.success else "⚠️"
        
        md = [
            f"## {status_emoji} GitLab Sentinel DevSecOps Pipeline Audit",
            "",
            f"**Pipeline Verdict:** {'PASSED' if not findings and test_result.success else 'ACTION REQUIRED'}",
            f"- **Security Findings:** {len(findings)} detected ({healed_count} auto-remediated)",
            f"- **Unit Tests:** {'Passed' if test_result.success else 'Failed'} ({test_result.duration_seconds}s)",
            ""
        ]

        if findings:
            md.extend([
                "### 🛡️ Static Security Analysis (AST)",
                "| Line | Severity | CWE | Description | Recommendation |",
                "| :--- | :--- | :--- | :--- | :--- |"
            ])
            for f in findings:
                md.append(f"| L{f.line_number} | **{f.severity}** | `{f.cwe}` | {f.description} | {f.recommended_fix} |")
            md.append("")

        if not test_result.success and test_result.failures:
            md.extend([
                "### ❌ Pipeline Test Failures",
                "```text"
            ])
            for fail in test_result.failures:
                md.append(f"FAILED {fail.file_path} -> {fail.error_type}: {fail.message}")
            md.extend([
                "```",
                ""
            ])

        md.extend([
            "---",
            "*Report autonomously synthesized by **GitLab Sentinel Agent** for GitLab Transcend 2026.*"
        ])

        return "\n".join(md)
