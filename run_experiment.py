#!/usr/bin/env python3
"""
Experiment runner for UPI Fraud Stress Lab.

Runs S1-S4 scenarios and generates results.
"""
import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

print("UPI Fraud Stress Lab - Experiment Runner")
print()
print("NOTE: Experiment runner requires:")
print("  1. Dataset prepared")
print("  2. Trained detector model")
print("  3. All components integrated")
print()
print("Waiting for agent completion...")
print()
print("Usage:")
print("  python run_experiment.py --scenario S1")
print("  python run_experiment.py --scenario S4")
print("  python run_experiment.py --all")
print()
