#!/usr/bin/env python3
"""
Verify that all required packages are installed and importable.
Run this after setup.sh to confirm the environment is ready.
"""

import sys
from typing import Tuple, List

CORE_PACKAGES = [
    "numpy",
    "scipy", 
    "pandas",
    "streamlit",
    "PySide6",
    "fastapi",
    "psutil"
]

OPTIONAL_PACKAGES = [
    "torch",
    "torchvision",
    "torchaudio"
]

COLORS = {
    "GREEN": "\033[92m",
    "RED": "\033[91m",
    "YELLOW": "\033[93m",
    "BLUE": "\033[94m",
    "RESET": "\033[0m"
}


def check_package(package_name: str) -> Tuple[bool, str]:
    """Check if a package can be imported."""
    try:
        __import__(package_name)
        return True, None
    except ImportError as e:
        return False, str(e)


def verify_installation() -> bool:
    """Verify all core packages are installed."""
    print(f"\n{COLORS['BLUE']}{'='*60}{COLORS['RESET']}")
    print(f"{COLORS['BLUE']}  Verifying Installation{COLORS['RESET']}")
    print(f"{COLORS['BLUE']}{'='*60}{COLORS['RESET']}\n")
    
    all_ok = True
    failed_packages: List[str] = []
    
    # Check core packages
    print(f"{COLORS['BLUE']}Core Packages:{COLORS['RESET']}")
    for package in CORE_PACKAGES:
        success, error = check_package(package)
        status = f"{COLORS['GREEN']}✓{COLORS['RESET']}" if success else f"{COLORS['RED']}✗{COLORS['RESET']}"
        print(f"  {status} {package}")
        if not success:
            all_ok = False
            failed_packages.append(package)
    
    print()
    
    # Check optional packages
    print(f"{COLORS['BLUE']}Optional Packages (for deep learning):{COLORS['RESET']}")
    optional_available = 0
    for package in OPTIONAL_PACKAGES:
        success, error = check_package(package)
        status = f"{COLORS['GREEN']}✓{COLORS['RESET']}" if success else f"{COLORS['YELLOW']}○{COLORS['RESET']}"
        note = "" if success else " (optional - not needed for demo)"
        print(f"  {status} {package}{note}")
        if success:
            optional_available += 1
    
    print()
    
    if all_ok:
        print(f"{COLORS['GREEN']}✓ All required packages installed!{COLORS['RESET']}")
        print(f"{COLORS['BLUE']}Optional packages: {optional_available}/3 available{COLORS['RESET']}\n")
        return True
    else:
        print(f"{COLORS['RED']}✗ Missing packages: {', '.join(failed_packages)}{COLORS['RESET']}")
        print(f"{COLORS['YELLOW']}Run: pip install -r requirements.txt{COLORS['RESET']}\n")
        return False


def main():
    """Main entry point."""
    success = verify_installation()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
