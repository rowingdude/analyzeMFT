#!/usr/bin/env python3
"""
Local webhook server to receive GitHub Actions notifications
This allows real-time monitoring of GitHub Actions from your local machine
"""

import json
import hmac
import hashlib
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
import subprocess
import os

class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        """Handle webhook POST requests from GitHub"""
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        
        # Verify webhook signature if secret is configured
        if 'X-Hub-Signature-256' in self.headers:
            if not self.verify_signature(body):
                self.send_response(401)
                self.end_headers()
                return
        
        try:
            data = json.loads(body)
            self.process_webhook(data)
            
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'OK')
        except Exception as e:
            print(f"Error processing webhook: {e}")
            self.send_response(500)
            self.end_headers()
    
    def verify_signature(self, body):
        """Verify GitHub webhook signature"""
        secret = os.environ.get('GITHUB_WEBHOOK_SECRET', '')
        if not secret:
            return True  # No secret configured, skip verification
        
        signature = self.headers.get('X-Hub-Signature-256', '')
        if not signature.startswith('sha256='):
            return False
        
        expected = 'sha256=' + hmac.new(
            secret.encode(),
            body,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected, signature)
    
    def process_webhook(self, data):
        """Process the webhook data"""
        event = self.headers.get('X-GitHub-Event', 'unknown')
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Received {event} event")
        
        if event == 'workflow_run':
            self.handle_workflow_run(data)
        elif event == 'check_run':
            self.handle_check_run(data)
        elif event == 'check_suite':
            self.handle_check_suite(data)
    
    def handle_workflow_run(self, data):
        """Handle workflow run events"""
        action = data.get('action')
        workflow_run = data.get('workflow_run', {})
        
        name = workflow_run.get('name', 'Unknown')
        status = workflow_run.get('status')
        conclusion = workflow_run.get('conclusion')
        run_id = workflow_run.get('id')
        html_url = workflow_run.get('html_url')
        
        print(f"Workflow: {name}")
        print(f"Status: {status}")
        print(f"Conclusion: {conclusion}")
        print(f"Run ID: {run_id}")
        print(f"URL: {html_url}")
        
        if status == 'completed' and conclusion == 'failure':
            print("\n⚠️  WORKFLOW FAILED!")
            self.fetch_error_details(run_id)
    
    def handle_check_run(self, data):
        """Handle check run events"""
        check_run = data.get('check_run', {})
        name = check_run.get('name')
        status = check_run.get('status')
        conclusion = check_run.get('conclusion')
        
        print(f"Check: {name} - {status} ({conclusion})")
        
        if conclusion == 'failure':
            output = check_run.get('output', {})
            if output.get('annotations'):
                print("\nAnnotations:")
                for ann in output['annotations'][:5]:  # Show first 5
                    print(f"  - {ann.get('path')}:{ann.get('start_line')}")
                    print(f"    {ann.get('message')}")
    
    def handle_check_suite(self, data):
        """Handle check suite events"""
        check_suite = data.get('check_suite', {})
        status = check_suite.get('status')
        conclusion = check_suite.get('conclusion')
        
        print(f"Check Suite: {status} ({conclusion})")
    
    def fetch_error_details(self, run_id):
        """Fetch detailed error information using GitHub CLI"""
        try:
            # Try to get failed logs
            result = subprocess.run(
                ["gh", "run", "view", str(run_id), "--log-failed"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 and result.stdout:
                lines = result.stdout.split('\n')
                failures = [l for l in lines if 'FAILED' in l or 'ERROR' in l]
                
                if failures:
                    print("\nTest Failures:")
                    for failure in failures[:10]:  # Show first 10
                        print(f"  {failure.strip()}")
        except Exception as e:
            print(f"Could not fetch error details: {e}")
    
    def log_message(self, format, *args):
        """Suppress default logging"""
        pass

def start_webhook_server(port=8080):
    """Start the webhook server"""
    print(f"Starting webhook server on port {port}")
    print(f"Configure GitHub webhook to: http://YOUR_PUBLIC_IP:{port}/webhook")
    print("\nFor local testing with ngrok:")
    print(f"  1. Install ngrok: https://ngrok.com/download")
    print(f"  2. Run: ngrok http {port}")
    print(f"  3. Use the ngrok URL as your webhook endpoint")
    print("\nPress Ctrl+C to stop\n")
    
    server = HTTPServer(('', port), WebhookHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()

if __name__ == "__main__":
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    start_webhook_server(port)