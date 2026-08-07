#!/usr/bin/env python3
"""
Wrapper script to start backend from root directory
"""
import sys
import os
import subprocess

# Run uvicorn from backend directory
subprocess.run([
    sys.executable, '-m', 'uvicorn', 
    'backend.main:app',
    '--host', '0.0.0.0',
    '--port', '8000'
])