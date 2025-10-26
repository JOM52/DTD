#!/usr/bin/env python3
"""
Bascule entre mode DEV et PRODUCTION
Usage: python toggle_dev_mode.py [dev|prod]
"""

import sys

def toggle_mode(mode):
    with open('ta_config.py', 'r') as f:
        content = f.read()
    
    if mode == 'dev':
        content = content.replace('"DEV_MODE": False', '"DEV_MODE": True')
        content = content.replace('"DEBUG_MODE": False', '"DEBUG_MODE": True')
        content = content.replace('"WATCHDOG_ENABLED": True', '"WATCHDOG_ENABLED": False')
        print("✓ Mode DEV activé (watchdog désactivé)")
    
    elif mode == 'prod':
        content = content.replace('"DEV_MODE": True', '"DEV_MODE": False')
        content = content.replace('"DEBUG_MODE": True', '"DEBUG_MODE": False')
        content = content.replace('"WATCHDOG_ENABLED": False', '"WATCHDOG_ENABLED": True')
        print("✓ Mode PRODUCTION activé (watchdog activé)")
    
    with open('ta_config.py', 'w') as f:
        f.write(content)

if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ['dev', 'prod']:
        print("Usage: python toggle_dev_mode.py [dev|prod]")
        sys.exit(1)
    
    toggle_mode(sys.argv[1])