#!/usr/bin/env python
"""
Diagnostic script to find why first screen doesn't show
Run this to see the startup sequence
"""

import sys
import os

# Add verbose logging
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

print("="*70)
print("DISCONNECTOME STARTUP DIAGNOSTIC")
print("="*70)
print()

# Check 1: Files exist
print("[1] Checking files...")
required_files = ['app.py', 'lib/constants.py', 'screens/start_screen.py']
for f in required_files:
    if os.path.exists(f):
        print(f"  ✓ {f} exists")
    else:
        print(f"  ✗ {f} MISSING!")

print()

# Check 2: Data folder
print("[2] Checking data folder...")
if os.path.exists('data'):
    print(f"  ✓ data/ exists")
    if os.path.exists('data/controls'):
        count = len(os.listdir('data/controls'))
        print(f"  ✓ data/controls/ exists ({count} items)")
    else:
        print(f"  ✗ data/controls/ missing")
    
    if os.path.exists('data/template'):
        print(f"  ✓ data/template/ exists")
    else:
        print(f"  ✗ data/template/ missing")
else:
    print(f"  ℹ data/ does not exist (will use system location)")

print()

# Check 3: Parse app.py to see what happens in __init__
print("[3] Analyzing app.py initialization...")
try:
    with open('app.py', 'r') as f:
        content = f.read()
    
    # Look for show_start_form call
    if 'self.show_start_form()' in content:
        # Find where it's called
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if 'self.show_start_form()' in line and '__init__' in '\n'.join(lines[max(0,i-50):i]):
                print(f"  ✓ show_start_form() called at line {i}")
                print(f"    Context: {line.strip()}")
                break
    else:
        print(f"  ✗ show_start_form() NOT called in __init__!")
        print(f"    This is likely the problem!")
    
    # Look for check_data_installation call
    if 'self.check_data_installation()' in content or 'check_data_installation' in content:
        print(f"  ✓ check_data_installation found")
        
        # Check if it's blocking
        if 'DataDownloadPrompt' in content:
            print(f"  ⚠ Uses blocking DataDownloadPrompt - might block UI")
    
    # Look for after() calls
    import re
    after_calls = re.findall(r'self\.after\((\d+),\s*self\.(\w+)\)', content)
    if after_calls:
        print(f"  ℹ Found {len(after_calls)} after() calls:")
        for delay, method in after_calls[:5]:  # Show first 5
            print(f"    - after({delay}ms) -> {method}()")

except Exception as e:
    print(f"  ✗ Error analyzing: {e}")

print()

# Check 4: Try importing
print("[4] Testing imports...")
try:
    # Test basic imports
    import tkinter as tk
    print("  ✓ tkinter imported")
    
    import customtkinter as ctk
    print("  ✓ customtkinter imported")
    
    from pathlib import Path
    print("  ✓ pathlib imported")
    
    # Try importing app components
    sys.path.insert(0, '.')
    
    try:
        from lib.constants import DATA_DIR, CONTROLS_DIR
        print(f"  ✓ constants imported")
        print(f"    DATA_DIR: {DATA_DIR}")
        print(f"    CONTROLS_DIR: {CONTROLS_DIR}")
    except Exception as e:
        print(f"  ✗ constants import failed: {e}")
    
    try:
        from screens.start_screen import StartRunForm
        print(f"  ✓ StartRunForm imported")
    except Exception as e:
        print(f"  ✗ StartRunForm import failed: {e}")

except ImportError as e:
    print(f"  ✗ Import failed: {e}")

print()

# Check 5: Look for common issues
print("[5] Checking for common issues...")

with open('app.py', 'r') as f:
    app_content = f.read()

issues_found = []

# Issue 1: show_start_form not called
if 'self.show_start_form()' not in app_content:
    issues_found.append("show_start_form() not called in __init__")

# Issue 2: Blocking data check before UI
if 'DataDownloadPrompt(self' in app_content:
    # Check if it's called before show_start_form
    init_section = app_content[app_content.find('def __init__'):app_content.find('def __init__') + 5000]
    prompt_pos = init_section.find('DataDownloadPrompt')
    show_pos = init_section.find('show_start_form')
    
    if prompt_pos > 0 and (show_pos < 0 or prompt_pos < show_pos):
        issues_found.append("Blocking data prompt called before show_start_form()")

# Issue 3: Exception in __init__
if 'try:' in app_content and '__init__' in app_content:
    # Check for exception handling that might swallow errors
    pass  # This is fine

if issues_found:
    print("  ⚠ Potential issues found:")
    for issue in issues_found:
        print(f"    - {issue}")
else:
    print("  ✓ No obvious issues found")

print()

# Check 6: Recommendation
print("[6] Recommendations:")
print()

if 'self.show_start_form()' not in app_content:
    print("  ❌ CRITICAL: show_start_form() is not being called!")
    print("     FIX: Add this line in __init__ after logger setup:")
    print("          self.show_start_form()")
    print()

# Check the order
init_section = app_content[app_content.find('def __init__'):app_content.find('def __init__') + 5000]
if 'check_data_installation' in init_section and 'show_start_form' in init_section:
    check_pos = init_section.find('check_data_installation')
    show_pos = init_section.find('show_start_form')
    
    if check_pos > 0 and show_pos > 0:
        if check_pos < show_pos:
            print("  ⚠ Data check happens before showing UI")
            print("     RECOMMENDATION: Swap the order:")
            print("       1. self.show_start_form()  # Show UI first")
            print("       2. self.after(500, self.check_data_installation)  # Check data after")
        else:
            print("  ✓ UI shows before data check - good!")
    print()

print("="*70)
print("DIAGNOSTIC COMPLETE")
print("="*70)
print()
print("Next steps:")
print("  1. Review the output above")
print("  2. Check for ✗ marks indicating problems")
print("  3. Apply recommended fixes")
print("  4. Run: python app.py")
print()
