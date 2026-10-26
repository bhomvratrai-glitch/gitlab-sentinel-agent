import pytest
import re
from gitlab_sentinel.remediator import SentinelRemediator
from gitlab_sentinel.scanner import VulnerabilityFinding
from gitlab_sentinel.ci_runner import ExecutionResult

def test_remediate_eval():
    remediator = SentinelRemediator()
    code = "val = eval(data)"
    finding = VulnerabilityFinding(
        cwe="CWE-94",
        severity="CRITICAL",
        description="Dynamic code eval",
        line_number=1,
        code_snippet=code,
        recommended_fix="Use ast.literal_eval"
    )
    healed = remediator.remediate_security_finding(code, finding)
    assert "ast.literal_eval(" in healed
    assert not re.search(r"(?<!literal_)eval\(", healed)

def test_remediate_shell_true():
    remediator = SentinelRemediator()
    code = "subprocess.run(['ls'], shell=True)"
    finding = VulnerabilityFinding(
        cwe="CWE-78",
        severity="HIGH",
        description="Shell true",
        line_number=1,
        code_snippet=code,
        recommended_fix="Set shell=False"
    )
    healed = remediator.remediate_security_finding(code, finding)
    assert "shell=False" in healed

def test_generate_mr_audit_report():
    remediator = SentinelRemediator()
    findings = [
        VulnerabilityFinding(
            cwe="CWE-78",
            severity="CRITICAL",
            description="OS injection",
            line_number=12,
            code_snippet="os.system()",
            recommended_fix="Use subprocess.run"
        )
    ]
    test_res = ExecutionResult(
        success=True,
        exit_code=0,
        stdout="passed",
        stderr="",
        duration_seconds=0.45
    )
    report = remediator.generate_mr_audit_report(findings, test_res, healed_count=1)
    assert "GitLab Sentinel DevSecOps Pipeline Audit" in report
    assert "CWE-78" in report
    assert "0.45s" in report
