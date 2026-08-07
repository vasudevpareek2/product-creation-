#!/usr/bin/env python3
"""
Wrapper script to start backend from root directory
"""
import sys
import os

# Change to backend directory
os.chdir('backend')

# Execute the real start script
exec(open('start_backend.py').read())