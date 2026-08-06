"""
Direct test of the capture script
"""
import subprocess
import sys
import os

# Get the backend directory
backend_dir = os.path.dirname(os.path.abspath(__file__))
script_path = os.path.join(backend_dir, "capture_token_script.py")

print(f"Testing capture script at: {script_path}")
print(f"Script exists: {os.path.exists(script_path)}")

if os.path.exists(script_path):
    print("Running capture script...")
    process = subprocess.Popen(
        [sys.executable, script_path, "https://admin.thrillophilia.com", "1"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    stdout, stderr = process.communicate()
    
    print(f"Return code: {process.returncode}")
    print(f"Stdout: {stdout}")
    print(f"Stderr: {stderr}")
else:
    print("Script not found!")