import os
import requests
from typing import Dict, Any, List, Optional

GITLAB_DEFAULT_URL = "https://gitlab.com/api/v4"

class GitLabClient:
    """
    Zero-dependency GitLab API v4 Client for automated MR code review and pipeline healing.
    """
    def __init__(
        self,
        token: Optional[str] = None,
        base_url: str = GITLAB_DEFAULT_URL,
        session: Optional[requests.Session] = None
    ):
        self.token = token or os.getenv("GITLAB_TOKEN", os.getenv("CI_JOB_TOKEN", ""))
        self.base_url = base_url.rstrip("/")
        self.session = session or requests.Session()

    def _headers(self) -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "GitLab-Sentinel-Agent/1.0"
        }
        if self.token:
            headers["PRIVATE-TOKEN"] = self.token
        return headers

    def get_merge_request(self, project_id: str, mr_iid: int) -> Dict[str, Any]:
        url = f"{self.base_url}/projects/{project_id}/merge_requests/{mr_iid}"
        resp = self.session.get(url, headers=self._headers(), timeout=20)
        resp.raise_for_status()
        return resp.json()

    def get_mr_diffs(self, project_id: str, mr_iid: int) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/projects/{project_id}/merge_requests/{mr_iid}/diffs"
        resp = self.session.get(url, headers=self._headers(), timeout=20)
        resp.raise_for_status()
        return resp.json()

    def post_mr_note(self, project_id: str, mr_iid: int, body: str) -> Dict[str, Any]:
        """
        Posts a markdown note or summary report to a Merge Request.
        """
        url = f"{self.base_url}/projects/{project_id}/merge_requests/{mr_iid}/notes"
        resp = self.session.post(url, headers=self._headers(), json={"body": body}, timeout=20)
        resp.raise_for_status()
        return resp.json()

    def post_mr_discussion_suggestion(
        self,
        project_id: str,
        mr_iid: int,
        file_path: str,
        new_line: int,
        comment: str,
        suggested_code: str,
        base_sha: str,
        start_sha: str,
        head_sha: str
    ) -> Dict[str, Any]:
        """
        Posts an inline GitLab Merge Request code suggestion.
        """
        body = f"{comment}\n\n```suggestion:-0+0\n{suggested_code}\n```"
        position = {
            "position_type": "text",
            "base_sha": base_sha,
            "start_sha": start_sha,
            "head_sha": head_sha,
            "new_path": file_path,
            "new_line": new_line
        }
        url = f"{self.base_url}/projects/{project_id}/merge_requests/{mr_iid}/discussions"
        resp = self.session.post(
            url,
            headers=self._headers(),
            json={"body": body, "position": position},
            timeout=20
        )
        resp.raise_for_status()
        return resp.json()

    def create_remediation_branch(
        self,
        project_id: str,
        branch_name: str,
        ref_branch: str = "main"
    ) -> Dict[str, Any]:
        url = f"{self.base_url}/projects/{project_id}/repository/branches"
        payload = {"branch": branch_name, "ref": ref_branch}
        resp = self.session.post(url, headers=self._headers(), json=payload, timeout=20)
        resp.raise_for_status()
        return resp.json()

    def create_merge_request(
        self,
        project_id: str,
        source_branch: str,
        target_branch: str,
        title: str,
        description: str
    ) -> Dict[str, Any]:
        url = f"{self.base_url}/projects/{project_id}/merge_requests"
        payload = {
            "source_branch": source_branch,
            "target_branch": target_branch,
            "title": title,
            "description": description,
            "remove_source_branch": True
        }
        resp = self.session.post(url, headers=self._headers(), json=payload, timeout=20)
        resp.raise_for_status()
        return resp.json()
