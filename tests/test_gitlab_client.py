import pytest
from unittest.mock import patch, MagicMock
from gitlab_sentinel.gitlab_client import GitLabClient

@patch("requests.Session.get")
def test_get_merge_request(mock_get):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"id": 100, "iid": 42, "title": "Feat: Add Payment API"}
    mock_resp.raise_for_status = MagicMock()
    mock_get.return_value = mock_resp

    client = GitLabClient(token="mock_token")
    mr = client.get_merge_request("gitlab-org/project", 42)

    assert mr["title"] == "Feat: Add Payment API"
    assert mock_get.called

@patch("requests.Session.post")
def test_post_mr_discussion_suggestion(mock_post):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"id": "disc_123"}
    mock_resp.raise_for_status = MagicMock()
    mock_post.return_value = mock_resp

    client = GitLabClient(token="mock_token")
    res = client.post_mr_discussion_suggestion(
        project_id="12345",
        mr_iid=5,
        file_path="src/main.py",
        new_line=10,
        comment="Insecure shell execution",
        suggested_code="subprocess.run(['ls'])",
        base_sha="sha_base",
        start_sha="sha_start",
        head_sha="sha_head"
    )

    assert res["id"] == "disc_123"
    assert mock_post.called

@patch("requests.Session.post")
def test_create_merge_request(mock_post):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"iid": 99, "web_url": "https://gitlab.com/project/-/merge_requests/99"}
    mock_resp.raise_for_status = MagicMock()
    mock_post.return_value = mock_resp

    client = GitLabClient(token="mock_token")
    res = client.create_merge_request(
        project_id="12345",
        source_branch="sentinel/fix-cwe-78",
        target_branch="main",
        title="[Sentinel] Automated DevSecOps Security Remediation",
        description="Fixes CWE-78 command injection detected in CI pipeline."
    )

    assert res["iid"] == 99
    assert "https://gitlab.com" in res["web_url"]
