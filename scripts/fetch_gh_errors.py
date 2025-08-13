#!/usr/bin/env python3
"""
GitHub Actions Error Fetcher
Fetches and parses errors from GitHub Actions runs in real-time
"""

import json
import subprocess
import sys
import time
import re
from datetime import datetime
from pathlib import Path

class GitHubActionMonitor:
    def __init__(self, repo=None):
        self.repo = repo or self._get_current_repo()
        
    def _get_current_repo(self):
        """Get the current repo from git remote"""
        try:
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                capture_output=True, text=True, check=True
            )
            url = result.stdout.strip()
            # Extract owner/repo from URL
            match = re.search(r'github\.com[:/]([^/]+)/([^.]+)', url)
            if match:
                return f"{match.group(1)}/{match.group(2)}"
        except:
            pass
        return None
    
    def check_gh_cli(self):
        """Check if GitHub CLI is installed and authenticated"""
        try:
            subprocess.run(["gh", "auth", "status"], check=True, capture_output=True)
            return True
        except:
            print("GitHub CLI not authenticated. Run: gh auth login")
            return False
    
    def get_latest_run(self):
        """Get the latest workflow run"""
        cmd = ["gh", "run", "list", "--limit", "1", "--json", 
               "databaseId,status,conclusion,name,createdAt,headBranch"]
        if self.repo:
            cmd.extend(["--repo", self.repo])
            
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            runs = json.loads(result.stdout)
            return runs[0] if runs else None
        return None
    
    def get_run_jobs(self, run_id):
        """Get all jobs for a run"""
        cmd = ["gh", "run", "view", str(run_id), "--json", "jobs"]
        if self.repo:
            cmd.extend(["--repo", self.repo])
            
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return data.get('jobs', [])
        return []
    
    def get_job_logs(self, run_id, job_name=None):
        """Get logs for a specific job or all failed jobs"""
        cmd = ["gh", "run", "view", str(run_id), "--log-failed"]
        if self.repo:
            cmd.extend(["--repo", self.repo])
            
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.stdout if result.returncode == 0 else ""
    
    def parse_test_failures(self, logs):
        """Parse test failures from logs"""
        failures = []
        current_failure = None
        
        lines = logs.split('\n')
        for i, line in enumerate(lines):
            # Look for pytest failure markers
            if 'FAILED' in line and '::' in line:
                test_name = re.search(r'FAILED\s+([^\s]+)', line)
                if test_name:
                    current_failure = {
                        'test': test_name.group(1),
                        'line': i,
                        'error': [],
                        'traceback': []
                    }
                    failures.append(current_failure)
            
            # Capture assertion errors
            elif current_failure and 'AssertionError' in line:
                current_failure['error'].append(line.strip())
            
            # Capture traceback
            elif current_failure and line.strip().startswith('>'):
                current_failure['traceback'].append(line.strip())
            
            # Look for syntax errors
            elif 'SyntaxError' in line:
                failures.append({
                    'test': 'Syntax Error',
                    'line': i,
                    'error': [line.strip()],
                    'traceback': lines[max(0, i-3):min(len(lines), i+3)]
                })
        
        return failures
    
    def monitor_run(self, run_id=None, interval=10):
        """Monitor a run until completion"""
        if not run_id:
            run = self.get_latest_run()
            if not run:
                print("No runs found")
                return
            run_id = run['databaseId']
        
        print(f"Monitoring run {run_id}...")
        
        while True:
            cmd = ["gh", "run", "view", str(run_id), "--json", "status,conclusion"]
            if self.repo:
                cmd.extend(["--repo", self.repo])
                
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                data = json.loads(result.stdout)
                status = data.get('status')
                conclusion = data.get('conclusion')
                
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Status: {status}")
                
                if status == 'completed':
                    print(f"Run completed with: {conclusion}")
                    
                    if conclusion == 'failure':
                        print("\nFetching failure details...")
                        logs = self.get_job_logs(run_id)
                        failures = self.parse_test_failures(logs)
                        
                        if failures:
                            print(f"\nFound {len(failures)} test failures:")
                            for f in failures:
                                print(f"\n❌ {f['test']}")
                                if f['error']:
                                    print("  Error:", ' '.join(f['error']))
                                if f['traceback']:
                                    print("  Traceback:")
                                    for line in f['traceback'][:5]:
                                        print(f"    {line}")
                    break
                
                time.sleep(interval)
            else:
                print("Failed to get run status")
                break
    
    def get_errors_json(self, run_id=None):
        """Get errors in JSON format for programmatic access"""
        if not run_id:
            run = self.get_latest_run()
            if not run:
                return {'error': 'No runs found'}
            run_id = run['databaseId']
        
        logs = self.get_job_logs(run_id)
        failures = self.parse_test_failures(logs)
        
        jobs = self.get_run_jobs(run_id)
        failed_jobs = [j for j in jobs if j.get('conclusion') == 'failure']
        
        return {
            'run_id': run_id,
            'failed_jobs': failed_jobs,
            'test_failures': failures,
            'total_failures': len(failures)
        }

def main():
    """Main entry point"""
    monitor = GitHubActionMonitor()
    
    if not monitor.check_gh_cli():
        sys.exit(1)
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'monitor':
            monitor.monitor_run()
        elif command == 'errors':
            errors = monitor.get_errors_json()
            print(json.dumps(errors, indent=2))
        elif command == 'latest':
            run = monitor.get_latest_run()
            if run:
                print(f"Latest run: {run['name']} ({run['status']})")
                print(f"ID: {run['databaseId']}")
                print(f"Branch: {run['headBranch']}")
        else:
            print(f"Unknown command: {command}")
    else:
        print("GitHub Actions Error Fetcher")
        print("\nUsage:")
        print("  python fetch_gh_errors.py monitor  # Monitor latest run")
        print("  python fetch_gh_errors.py errors   # Get errors as JSON")
        print("  python fetch_gh_errors.py latest   # Show latest run info")

if __name__ == "__main__":
    main()