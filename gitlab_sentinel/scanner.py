import ast
import re
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class VulnerabilityFinding:
    cwe: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    description: str
    line_number: int
    code_snippet: str
    recommended_fix: str

class ASTSecurityScanner:
    """
    Static AST security auditor designed for GitLab CI/CD DevSecOps automation.
    Detects critical vulnerabilities prior to deployment.
    """
    def __init__(self):
        self.secret_patterns = [
            re.compile(r"(?i)(api[_-]?key|secret|token|password|auth[_-]?key)"),
        ]

    def scan_code(self, source_code: str, filename: str = "code.py") -> List[VulnerabilityFinding]:
        findings: List[VulnerabilityFinding] = []
        try:
            tree = ast.parse(source_code, filename=filename)
        except SyntaxError as e:
            findings.append(VulnerabilityFinding(
                cwe="CWE-1107",
                severity="CRITICAL",
                description=f"Syntax Error preventing AST parsing: {e.msg}",
                line_number=e.lineno or 1,
                code_snippet=e.text or "",
                recommended_fix="Correct syntax errors before committing."
            ))
            return findings

        lines = source_code.splitlines()

        for node in ast.walk(tree):
            # 1. Code Injection: eval, exec
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id in ("eval", "exec"):
                    lineno = getattr(node, "lineno", 1)
                    snippet = lines[lineno - 1] if 0 < lineno <= len(lines) else ""
                    findings.append(VulnerabilityFinding(
                        cwe="CWE-94",
                        severity="CRITICAL",
                        description=f"Dangerous dynamic code execution via `{node.func.id}()`.",
                        line_number=lineno,
                        code_snippet=snippet.strip(),
                        recommended_fix="Replace dynamic evaluation with ast.literal_eval() or static deserialization."
                    ))

            # 2. Command Injection: os.system, subprocess with shell=True
            if isinstance(node, ast.Call):
                func = node.func
                # os.system, os.popen
                if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name) and func.value.id == "os":
                    if func.attr in ("system", "popen"):
                        lineno = getattr(node, "lineno", 1)
                        snippet = lines[lineno - 1] if 0 < lineno <= len(lines) else ""
                        findings.append(VulnerabilityFinding(
                            cwe="CWE-78",
                            severity="CRITICAL",
                            description=f"Unsanitized OS command execution via `os.{func.attr}()`.",
                            line_number=lineno,
                            code_snippet=snippet.strip(),
                            recommended_fix="Use subprocess.run(['cmd', arg], shell=False) with parameterized arguments."
                        ))

                # subprocess.run(..., shell=True)
                if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name) and func.value.id in ("subprocess", "commands"):
                    for kw in node.keywords:
                        if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                            lineno = getattr(node, "lineno", 1)
                            snippet = lines[lineno - 1] if 0 < lineno <= len(lines) else ""
                            findings.append(VulnerabilityFinding(
                                cwe="CWE-78",
                                severity="HIGH",
                                description="Subprocess invoked with `shell=True`, vulnerable to shell metacharacter injection.",
                                line_number=lineno,
                                code_snippet=snippet.strip(),
                                recommended_fix="Set `shell=False` and pass command and arguments as a list of strings."
                            ))

            # 3. SQL Injection: string formatting inside execute()
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "execute":
                if node.args:
                    arg = node.args[0]
                    # Check for BinOp % or + or JoinedStr (f-string)
                    is_sql_injection = False
                    if isinstance(arg, ast.JoinedStr):
                        is_sql_injection = True
                    elif isinstance(arg, ast.BinOp) and isinstance(arg.op, (ast.Add, ast.Mod)):
                        is_sql_injection = True

                    if is_sql_injection:
                        lineno = getattr(node, "lineno", 1)
                        snippet = lines[lineno - 1] if 0 < lineno <= len(lines) else ""
                        findings.append(VulnerabilityFinding(
                            cwe="CWE-89",
                            severity="CRITICAL",
                            description="SQL query constructed via dynamic string formatting inside `.execute()`.",
                            line_number=lineno,
                            code_snippet=snippet.strip(),
                            recommended_fix="Use parameterized queries: cursor.execute('SELECT * FROM t WHERE col = ?', (val,))."
                        ))

            # 4. Hardcoded Credentials
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        for pattern in self.secret_patterns:
                            if pattern.search(target.id):
                                if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                                    val = node.value.value.strip()
                                    if len(val) >= 8 and not val.startswith(("${", "os.getenv", "ENV")):
                                        lineno = getattr(node, "lineno", 1)
                                        snippet = lines[lineno - 1] if 0 < lineno <= len(lines) else ""
                                        findings.append(VulnerabilityFinding(
                                            cwe="CWE-798",
                                            severity="HIGH",
                                            description=f"Potential hardcoded credential assigned to `{target.id}`.",
                                            line_number=lineno,
                                            code_snippet=snippet.strip(),
                                            recommended_fix="Load secrets from GitLab CI/CD Variables or environment variables via os.getenv()."
                                        ))

        return findings
