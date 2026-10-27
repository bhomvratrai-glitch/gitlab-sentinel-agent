import sys
import os
import argparse
from .scanner import ASTSecurityScanner
from .ci_runner import SandboxedCIRunner
from .remediator import SentinelRemediator

def main():
    parser = argparse.ArgumentParser(
        description="GitLab Sentinel: Autonomous DevSecOps & CI/CD Self-Healing Agent."
    )
    subparsers = parser.add_subparsers(dest="command", help="Sentinel command")

    scan_p = subparsers.add_parser("scan", help="Run static AST security audit")
    scan_p.add_argument("path", nargs="?", default=".", help="Target directory or file")

    test_p = subparsers.add_parser("test", help="Execute hermetic CI test runner")
    test_p.add_argument("path", nargs="?", default=".", help="Target test directory")

    heal_p = subparsers.add_parser("heal", help="Autonomously remediate security and CI failures")
    heal_p.add_argument("path", nargs="?", default=".", help="Target project path")

    green_p = subparsers.add_parser("greenops", help="Calculate CI compute waste & carbon savings")
    green_p.add_argument("--files", nargs="*", default=["README.md"], help="List of changed files")
    green_p.add_argument("--cancelled", type=int, default=2, help="Number of redundant pipelines cancelled")

    mcp_p = subparsers.add_parser("mcp", help="Run Model Context Protocol server for GitLab Duo")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    print("\n" + "=" * 60)
    print("🦊 GitLab Sentinel Agent — DevSecOps Autonomous Engine")
    print("=" * 60 + "\n")

    scanner = ASTSecurityScanner()
    runner = SandboxedCIRunner()
    remediator = SentinelRemediator()

    target_path = os.path.abspath(getattr(args, "path", "."))


    if args.command == "scan":
        print(f"🔍 Scanning target: {target_path}...\n")
        total_findings = 0
        if os.path.isfile(target_path):
            files = [target_path]
        else:
            files = [os.path.join(root, f) for root, _, filenames in os.walk(target_path) for f in filenames if f.endswith(".py")]

        for fpath in files:
            with open(fpath, "r", encoding="utf-8") as f:
                code = f.read()
            findings = scanner.scan_code(code, filename=os.path.basename(fpath))
            if findings:
                total_findings += len(findings)
                print(f"📄 {os.path.relpath(fpath, target_path)}:")
                for finding in findings:
                    print(f"  [{finding.severity}] {finding.cwe} at L{finding.line_number}: {finding.description}")
                    print(f"    Fix: {finding.recommended_fix}")

        print(f"\nAudit complete. Total findings: {total_findings}")
        sys.exit(1 if total_findings > 0 else 0)

    elif args.command == "test":
        print(f"🧪 Running sandboxed CI test runner in {target_path}...\n")
        res = runner.run_tests(cwd=target_path)
        print(res.stdout)
        if not res.success:
            print(f"\n❌ Test run FAILED ({res.duration_seconds}s). Exit code: {res.exit_code}")
            sys.exit(res.exit_code)
        else:
            print(f"\n✅ All tests PASSED ({res.duration_seconds}s).")
            sys.exit(0)

    elif args.command == "heal":
        print(f"⚡ Running Autonomous Closed-Loop Self-Healing on {target_path}...\n")
        files = [os.path.join(root, f) for root, _, filenames in os.walk(target_path) for f in filenames if f.endswith(".py")]
        healed_count = 0

        for fpath in files:
            with open(fpath, "r", encoding="utf-8") as f:
                code = f.read()
            findings = scanner.scan_code(code, filename=os.path.basename(fpath))
            new_code = code
            for finding in findings:
                new_code = remediator.remediate_security_finding(new_code, finding)
                healed_count += 1

            if new_code != code:
                with open(fpath, "w", encoding="utf-8") as f:
                    f.write(new_code)
                print(f"🛠️  Surgically healed {len(findings)} vulnerability(s) in {os.path.relpath(fpath, target_path)}")

        print(f"\nRemediation complete. Healed {healed_count} security flaw(s).")
        print("Re-running verification tests...")
        res = runner.run_tests(cwd=target_path)
        print(f"Verification Result: {'✅ PASSED' if res.success else '❌ FAILED'}")

    elif args.command == "greenops":
        from .greenops import GreenOpsOptimizer
        optimizer = GreenOpsOptimizer()
        res = optimizer.evaluate_merge_request_pipeline(args.files, active_pipeline_queue_len=args.cancelled + 1)
        savings = res["savings"]
        print(f"🌱 GitLab Sentinel GreenOps Optimization Report:")
        print(f"  • Recommended Action: {res['action']}")
        print(f"  • Redundant Pipelines Cancelled: {savings.redundant_pipelines_cancelled}")
        print(f"  • Runner Compute Time Saved: {savings.cpu_minutes_saved} minutes")
        print(f"  • Cloud Cost Saved: ${savings.cost_saved_usd} USD")
        print(f"  • Carbon Abated: {savings.carbon_saved_kg_co2} kg CO2e")
        if savings.stages_skipped:
            print(f"  • Heavy Stages Safely Skipped: {', '.join(savings.stages_skipped)}")

    elif args.command == "mcp":
        from .mcp_server import SentinelMCPServer
        server = SentinelMCPServer()
        print("🔌 GitLab Sentinel Model Context Protocol (MCP) Server Active")
        print(f"Available Tools for GitLab Duo / Claude / Gemini:")
        for t in server.list_tools():
            print(f"  - {t['name']}: {t['description']}")


if __name__ == "__main__":
    main()
