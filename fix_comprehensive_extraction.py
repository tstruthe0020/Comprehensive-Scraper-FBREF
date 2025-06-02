#!/usr/bin/env python3
import os
import sys
from pathlib import Path

def fix_comprehensive_extraction_bug():
    """Fix the bug in the comprehensive extraction implementation"""
    server_path = Path(__file__).parent / "backend" / "server.py"
    
    # Read the server.py file
    with open(server_path, 'r') as f:
        server_code = f.read()
    
    # Fix the bug
    fixed_code = server_code.replace(
        "await db.matches.insert_one(match_data.dict())",
        "await db.matches.insert_one(match_data)"
    )
    
    # Write the fixed code back to the file
    with open(server_path, 'w') as f:
        f.write(fixed_code)
    
    print("Fixed the comprehensive extraction bug!")
    print("Changed 'await db.matches.insert_one(match_data.dict())' to 'await db.matches.insert_one(match_data)'")

if __name__ == "__main__":
    fix_comprehensive_extraction_bug()