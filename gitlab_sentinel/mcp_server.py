"""
GitLab Sentinel Model Context Protocol (MCP) Server
Exposes Sentinel's DevSecOps, Self-Healing, and GreenOps capabilities as standardized
MCP tools for GitLab Duo Chat and autonomous AI agents.
"""

from typing import Dict, Any, List
import json
from gitlab_sentinel.scanner import ASTSecurityScanner
from gitlab_sentinel.remediator import SentinelRemediator
from gitlab_sentinel.greenops import GreenOpsOptimizer
from gitlab_sentinel.flaky_detector import FlakyTestDetector

class SentinelMCPServer:
    """
    Standard Model Context Protocol (MCP) compliant tool provider for GitLab Duo.
    """

    def __init__(self):
        self.scanner = ASTSecurityScanner()
        self.remediator = SentinelRemediator()
        self.greenops = GreenOpsOptimizer()
        self.flaky_detector = FlakyTestDetector()

    def list_tools(self) -> List[Dict[str, Any]]:
        """Returns JSON-schema tool definitions for MCP clients."""
        return [
            {
                "name": "sentinel_scan_code",
                "description": "Scans code for critical AST security vulnerabilities (CWE-78, CWE-89, CWE-94, CWE-798).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string", "description": "Python source code to audit"}
                    },
                    "required": ["code"]
                }
            },
            {
                "name": "sentinel_remediate_finding",
                "description": "Applies surgical, zero-regression remediation for detected vulnerabilities.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string", "description": "Vulnerable code snippet"},
                        "cwe": {"type": "string", "description": "CWE identifier (e.g., 'CWE-78', 'CWE-89')"}
                    },
                    "required": ["code", "cwe"]
                }
            },
            {
                "name": "sentinel_calculate_greenops",
                "description": "Calculates compute minutes, cloud dollars, and kg of CO2 saved by cancelling redundant CI runs.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "changed_files": {"type": "array", "items": {"type": "string"}},
                        "cancelled_pipelines": {"type": "integer", "description": "Number of superseded runs"}
                    },
                    "required": ["changed_files"]
                }
            },
            {
                "name": "sentinel_quarantine_flaky_test",
                "description": "Detects and quarantines intermittent flaky tests with @pytest.mark.quarantine.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_content": {"type": "string"},
                        "test_name": {"type": "string"}
                    },
                    "required": ["file_content", "test_name"]
                }
            }
        ]

    def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Executes an MCP tool call and returns structured results."""
        if name == "sentinel_scan_code":
            findings = self.scanner.scan_code(arguments["code"])
            return {
                "count": len(findings),
                "findings": [
                    {
                        "cwe": f.cwe,
                        "severity": f.severity,
                        "line": f.line_number,
                        "description": f.description
                    }
                    for f in findings
                ]
            }

        elif name == "sentinel_remediate_finding":
            code = arguments["code"]
            cwe = arguments["cwe"]
            findings = self.scanner.scan_code(code)
            target_finding = next((f for f in findings if f.cwe == cwe), None)
            
            if target_finding:
                fixed_code = self.remediator.apply_heuristic_fix(code, target_finding)
                return {"success": True, "remediated_code": fixed_code}
            return {"success": False, "error": f"No finding matching {cwe} located in source."}

        elif name == "sentinel_calculate_greenops":
            files = arguments.get("changed_files", [])
            cancelled = arguments.get("cancelled_pipelines", 1)
            eval_result = self.greenops.evaluate_merge_request_pipeline(files, active_pipeline_queue_len=cancelled + 1)
            savings = eval_result["savings"]
            return {
                "action": eval_result["action"],
                "cpu_minutes_saved": savings.cpu_minutes_saved,
                "cost_saved_usd": savings.cost_saved_usd,
                "carbon_saved_kg_co2": savings.carbon_saved_kg_co2,
                "stages_skipped": savings.stages_skipped
            }

        elif name == "sentinel_quarantine_flaky_test":
            content = arguments["file_content"]
            tname = arguments["test_name"]
            patched = self.flaky_detector.generate_quarantine_patch(content, tname)
            return {"success": True, "patched_content": patched}

        else:
            return {"error": f"Unknown tool: {name}"}
