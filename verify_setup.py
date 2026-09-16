#!/usr/bin/env python3
"""
Quick Start Guide for Target Laptop
Run this after transferring the project to verify everything is ready.
"""
import sys
import subprocess
from pathlib import Path

def check_requirement(name, command, expected_in_output=None):
    """Check if a requirement is met."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            if expected_in_output and expected_in_output not in result.stdout:
                print(f"⚠️  {name}: Found but unexpected output")
                return False
            print(f"✅ {name}: OK")
            return True
        else:
            print(f"❌ {name}: Not found")
            return False
    except Exception as e:
        print(f"❌ {name}: Error - {e}")
        return False

def main():
    print("="*60)
    print("UPI FRAUD STRESS LAB - QUICK START VERIFICATION")
    print("="*60)
    print()

    checks = []

    # Check Python
    checks.append(check_requirement(
        "Python 3.9+",
        "python3 --version",
        "Python 3"
    ))

    # Check dataset
    dataset_path = Path("data/raw/creditcard.csv")
    if dataset_path.exists():
        size_mb = dataset_path.stat().st_size / (1024 * 1024)
        print(f"✅ Dataset: OK ({size_mb:.1f} MB)")
        checks.append(True)
    else:
        print(f"❌ Dataset: Not found at {dataset_path}")
        checks.append(False)

    # Check virtual environment
    venv_path = Path("venv")
    if venv_path.exists():
        print(f"✅ Virtual environment: OK")
        checks.append(True)
    else:
        print(f"⚠️  Virtual environment: Not created yet")
        print(f"   Run: python3 -m venv venv")
        checks.append(False)

    # Check source files
    src_files = list(Path("src").rglob("*.py"))
    if len(src_files) >= 20:
        print(f"✅ Source files: OK ({len(src_files)} files)")
        checks.append(True)
    else:
        print(f"❌ Source files: Incomplete ({len(src_files)} files)")
        checks.append(False)

    print()
    print("="*60)

    if all(checks):
        print("✅ ALL CHECKS PASSED")
        print()
        print("Next steps:")
        print("1. Activate virtual environment:")
        print("   source venv/bin/activate")
        print()
        print("2. Install dependencies:")
        print("   pip install -r requirements.txt")
        print()
        print("3. Train the model:")
        print("   python src/detectors/train.py")
        print()
        print("4. Run demo:")
        print("   python demo.py")
    else:
        print("⚠️  SOME CHECKS FAILED")
        print()
        print("Please ensure:")
        print("- Project was fully transferred")
        print("- Dataset file is present")
        print("- Python 3.9+ is installed")

    print("="*60)

if __name__ == "__main__":
    main()
