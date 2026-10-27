"""
GitLab Sentinel GreenOps & Compute Optimization Engine
Calculates redundant CI/CD compute waste, identifies non-affecting commit builds,
and tracks energy/carbon savings (targeting GitLab Environmental Impact Prize).
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Set
import os

# Average AWS/GCP cloud runner carbon intensity & cost constants
# Standard 2 vCPU 8GB Linux runner: ~0.08 kWh per hour, 0.385 kg CO2e / kWh (US-East grid average), $0.016 / min
KWH_PER_CPU_HOUR = 0.04
KG_CO2_PER_KWH = 0.385
RUNNER_COST_PER_MINUTE_USD = 0.016

@dataclass
class OptimizationResult:
    redundant_pipelines_cancelled: int
    cpu_minutes_saved: float
    cost_saved_usd: float
    carbon_saved_kg_co2: float
    stages_skipped: List[str]
    is_documentation_only: bool

class GreenOpsOptimizer:
    """
    Analyzes GitLab CI commit diffs and pipeline queues to eliminate
    unnecessary runner execution and compute waste.
    """
    
    DOCS_EXTENSIONS = {'.md', '.txt', '.png', '.jpg', '.jpeg', '.svg', '.drawio', '.pdf', '.gif'}
    CI_CONFIG_FILES = {'.gitlab-ci.yml', '.gitlab-ci.yaml', 'Dockerfile', 'docker-compose.yml'}

    def analyze_commit_changes(self, changed_files: List[str]) -> Dict[str, Any]:
        """
        Determines whether a commit modifies application code, docs only,
        or CI configuration.
        """
        if not changed_files:
            return {"type": "empty", "should_skip_heavy_stages": True}

        docs_only = all(
            any(f.endswith(ext) for ext in self.DOCS_EXTENSIONS)
            for f in changed_files
        )
        
        ci_modified = any(
            os.path.basename(f) in self.CI_CONFIG_FILES
            for f in changed_files
        )

        python_or_app_code = any(
            f.endswith(('.py', '.js', '.ts', '.go', '.rs', '.java', '.cpp'))
            for f in changed_files
        )

        return {
            "docs_only": docs_only,
            "ci_modified": ci_modified,
            "code_modified": python_or_app_code,
            "should_skip_heavy_stages": docs_only and not ci_modified
        }

    def calculate_savings(
        self,
        cancelled_pipelines: int,
        average_runtime_minutes: float = 12.5,
        skipped_heavy_stages_count: int = 0
    ) -> OptimizationResult:
        """
        Calculates hard dollar and carbon emission savings from cancelled/optimized CI runs.
        """
        # Base minutes saved from cancelling superseded or redundant pipelines
        total_minutes_saved = (cancelled_pipelines * average_runtime_minutes) + (skipped_heavy_stages_count * 8.0)
        
        # Calculate cloud cost saved
        cost_saved = total_minutes_saved * RUNNER_COST_PER_MINUTE_USD
        
        # Calculate carbon savings in kg CO2e
        # (Total minutes / 60) * KWH_PER_CPU_HOUR (assuming 2 vCPU) * KG_CO2_PER_KWH
        cpu_hours = (total_minutes_saved / 60.0) * 2.0
        kwh_consumed = cpu_hours * KWH_PER_CPU_HOUR
        carbon_saved = kwh_consumed * KG_CO2_PER_KWH

        skipped_stages = []
        if skipped_heavy_stages_count > 0:
            skipped_stages = ["docker-build", "sast-deep-scan", "e2e-integration-matrix"]

        return OptimizationResult(
            redundant_pipelines_cancelled=cancelled_pipelines,
            cpu_minutes_saved=round(total_minutes_saved, 2),
            cost_saved_usd=round(cost_saved, 2),
            carbon_saved_kg_co2=round(carbon_saved, 4),
            stages_skipped=skipped_stages,
            is_documentation_only=False
        )

    def evaluate_merge_request_pipeline(
        self,
        changed_files: List[str],
        active_pipeline_queue_len: int = 1
    ) -> Dict[str, Any]:
        """
        Full evaluation for a GitLab MR webhook trigger.
        Auto-cancels older pipelines if a new commit supersedes them.
        """
        analysis = self.analyze_commit_changes(changed_files)
        
        # If there are older running pipelines for the same MR branch, cancel all but the newest
        cancelled_count = max(0, active_pipeline_queue_len - 1)
        
        skipped_heavy = 1 if analysis["should_skip_heavy_stages"] else 0
        savings = self.calculate_savings(
            cancelled_pipelines=cancelled_count,
            skipped_heavy_stages_count=skipped_heavy
        )

        return {
            "analysis": analysis,
            "action": "AUTO_CANCEL_AND_SKIP" if (cancelled_count > 0 or analysis["should_skip_heavy_stages"]) else "RUN_STANDARD",
            "savings": savings
        }
