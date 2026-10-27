import pytest
from gitlab_sentinel.greenops import GreenOpsOptimizer

def test_analyze_docs_only_commit():
    optimizer = GreenOpsOptimizer()
    analysis = optimizer.analyze_commit_changes(["README.md", "docs/architecture.png"])
    assert analysis["docs_only"] is True
    assert analysis["should_skip_heavy_stages"] is True
    assert analysis["code_modified"] is False

def test_analyze_code_commit():
    optimizer = GreenOpsOptimizer()
    analysis = optimizer.analyze_commit_changes(["gitlab_sentinel/scanner.py", "tests/test_scanner.py"])
    assert analysis["docs_only"] is False
    assert analysis["should_skip_heavy_stages"] is False
    assert analysis["code_modified"] is True

def test_calculate_savings_cancellation():
    optimizer = GreenOpsOptimizer()
    savings = optimizer.calculate_savings(cancelled_pipelines=2, average_runtime_minutes=10.0)
    assert savings.redundant_pipelines_cancelled == 2
    assert savings.cpu_minutes_saved == 20.0
    assert savings.cost_saved_usd > 0
    assert savings.carbon_saved_kg_co2 > 0

def test_evaluate_mr_pipeline():
    optimizer = GreenOpsOptimizer()
    eval_res = optimizer.evaluate_merge_request_pipeline(
        changed_files=["docs/index.html", "README.md"],
        active_pipeline_queue_len=3
    )
    assert eval_res["action"] == "AUTO_CANCEL_AND_SKIP"
    assert eval_res["savings"].redundant_pipelines_cancelled == 2
