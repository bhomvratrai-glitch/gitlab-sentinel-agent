import pytest
from gitlab_sentinel.mcp_server import SentinelMCPServer

def test_mcp_list_tools():
    server = SentinelMCPServer()
    tools = server.list_tools()
    assert len(tools) == 4
    tool_names = [t["name"] for t in tools]
    assert "sentinel_scan_code" in tool_names
    assert "sentinel_remediate_finding" in tool_names
    assert "sentinel_calculate_greenops" in tool_names
    assert "sentinel_quarantine_flaky_test" in tool_names

def test_mcp_call_scan_tool():
    server = SentinelMCPServer()
    res = server.call_tool("sentinel_scan_code", {
        "code": "import os\nos.system('echo test')"
    })
    assert res["count"] == 1
    assert res["findings"][0]["cwe"] == "CWE-78"

def test_mcp_call_greenops_tool():
    server = SentinelMCPServer()
    res = server.call_tool("sentinel_calculate_greenops", {
        "changed_files": ["README.md"],
        "cancelled_pipelines": 2
    })
    assert res["cpu_minutes_saved"] > 0
    assert res["cost_saved_usd"] > 0
    assert res["carbon_saved_kg_co2"] > 0

def test_mcp_call_quarantine_tool():
    server = SentinelMCPServer()
    code = "def test_intermittent():\n    pass"
    res = server.call_tool("sentinel_quarantine_flaky_test", {
        "file_content": code,
        "test_name": "test_intermittent"
    })
    assert res["success"] is True
    assert "@pytest.mark.quarantine" in res["patched_content"]
