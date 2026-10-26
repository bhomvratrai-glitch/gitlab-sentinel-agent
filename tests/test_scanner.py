import pytest
from gitlab_sentinel.scanner import ASTSecurityScanner

def test_detect_command_injection():
    scanner = ASTSecurityScanner()
    code = """
import os
def run_cmd(user_input):
    os.system(f"echo {user_input}")
"""
    findings = scanner.scan_code(code)
    assert len(findings) == 1
    assert findings[0].cwe == "CWE-78"
    assert findings[0].severity == "CRITICAL"
    assert findings[0].line_number == 4

def test_detect_subprocess_shell_true():
    scanner = ASTSecurityScanner()
    code = """
import subprocess
def exec_cmd(arg):
    subprocess.run(["ls", arg], shell=True)
"""
    findings = scanner.scan_code(code)
    assert len(findings) == 1
    assert findings[0].cwe == "CWE-78"
    assert findings[0].severity == "HIGH"

def test_detect_code_injection():
    scanner = ASTSecurityScanner()
    code = """
def load_data(payload):
    return eval(payload)
"""
    findings = scanner.scan_code(code)
    assert len(findings) == 1
    assert findings[0].cwe == "CWE-94"
    assert findings[0].severity == "CRITICAL"

def test_detect_hardcoded_secrets():
    scanner = ASTSecurityScanner()
    code = """
api_key = "ghp_mocktoken1234567890abcdef"
"""
    findings = scanner.scan_code(code)
    assert len(findings) == 1
    assert findings[0].cwe == "CWE-798"
    assert findings[0].severity == "HIGH"

def test_syntax_error_handling():
    scanner = ASTSecurityScanner()
    code = "def broken_syntax(:"
    findings = scanner.scan_code(code)
    assert len(findings) == 1
    assert findings[0].cwe == "CWE-1107"
