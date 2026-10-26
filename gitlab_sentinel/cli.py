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

    target_path = os.path.abspath(args.path)

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

if __name__ == "__main__":
    main()
