import requests
import sys

URL_BASE = "http://app:5000"

def test_path(path, expected_status, method="GET", data=None, allow_redirects=False):
    try:
        if method == "GET":
            resp = requests.get(URL_BASE + path, allow_redirects=allow_redirects)
        elif method == "POST":
            resp = requests.post(URL_BASE + path, data=data, allow_redirects=allow_redirects)
        else:
            return False
        
        status = resp.status_code
        if status == expected_status:
            print(f"OK: {method} {path} -> {status}")
            return True
        else:
            print(f"FAIL: {method} {path} -> {status} (expected {expected_status})", file=sys.stderr)
            return False
    except Exception as e:
        print(f"ERROR: {method} {path} -> {e}", file=sys.stderr)
        return False

def main():
    failed = 0
    
    # GET
    tests = [
        ("/", 200),
        ("/files", 200),
        ("/upload", 200),
        ("/notexist", 404),
        ("/to_files", 200),
        ("/success/test", 200),
    ]
    
    for path, expected in tests:
        if not test_path(path, expected):
            failed += 1
    
    # POST /login (успешный)
    if test_path("/login", 302, "POST", {"name": "admin", "password": "password"}):
        pass
    else:
        failed += 1
    
    # POST /login (неуспешный)
    if test_path("/login", 401, "POST", {"name": "wrong", "password": "wrong"}):
        pass
    else:
        failed += 1
    
    if failed == 0:
        print("All integration tests passed")
        sys.exit(0)
    else:
        print(f"{failed} integration test(s) failed")
        sys.exit(1)

if __name__ == "__main__":
    main()