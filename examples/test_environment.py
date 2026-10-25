#!/usr/bin/env python3
"""
Test and demonstration of the UPI Environment Simulator

Shows how to:
1. Create accounts and VPAs
2. Process transactions with risk assessment
3. Apply different threshold configurations
4. View transaction history and statistics
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from environment import (
    UPIEnvironment,
    ThresholdConfig,
    create_conservative_thresholds,
    create_aggressive_thresholds
)
from datetime import datetime
import pytest


def print_section(title: str):
    """Print a section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)


def setup_environment():
    """Test basic environment setup and operations"""
    print_section("1. Basic Environment Setup")

    # Create environment with default thresholds
    env = UPIEnvironment()
    print(f"Created UPI Environment")
    print(f"Default thresholds: {env.threshold_config.to_dict()}")

    # Create accounts
    print("\nCreating accounts...")
    acc1 = env.create_account("ACC001", initial_balance=50000.0)
    acc2 = env.create_account("ACC002", initial_balance=30000.0)
    acc3 = env.create_account("ACC003", initial_balance=100000.0)
    print(f"Created 3 accounts")

    # Create VPAs
    print("\nCreating VPAs...")
    vpa1 = env.create_vpa("alice@paytm", "ACC001", "Alice Kumar")
    vpa2 = env.create_vpa("bob@phonepe", "ACC002", "Bob Singh")
    vpa3 = env.create_vpa("merchant@ybl", "ACC003", "Shop Merchant", vpa_type="merchant")
    print(f"Created 3 VPAs:")
    print(f"  - {vpa1.vpa_id} ({vpa1.name})")
    print(f"  - {vpa2.vpa_id} ({vpa2.name})")
    print(f"  - {vpa3.vpa_id} ({vpa3.name})")

    return env


@pytest.fixture
def env():
    return setup_environment()


def test_basic_environment():
    env = setup_environment()
    assert len(env.accounts) == len(env.vpas) == 3
    assert sum(a.balance for a in env.accounts.values()) == 180000


def test_transaction_processing(env):
    """Test transaction processing with different risk levels"""
    print_section("2. Transaction Processing")

    # Test 1: Low risk transaction (ALLOW)
    print("\nTest 1: Low risk transaction - Small amount")
    result = env.process_transaction({
        "from_vpa": "alice@paytm",
        "to_vpa": "bob@phonepe",
        "amount": 500.0,
        "timestamp": datetime.now().isoformat()
    })
    print(f"Transaction ID: {result['transaction_id']}")
    print(f"Risk Score: {result['risk_score']:.3f}")
    print(f"Decision: {result['decision']}")
    print(f"Status: {result['status']}")
    print(f"Details: {result['details']}")

    # Test 2: Medium risk transaction (FLAG)
    print("\n\nTest 2: Medium risk transaction - Large amount")
    result = env.process_transaction({
        "from_vpa": "alice@paytm",
        "to_vpa": "merchant@ybl",
        "amount": 25000.0,
        "timestamp": datetime.now().isoformat()
    })
    print(f"Transaction ID: {result['transaction_id']}")
    risk_score_str = f"{result['risk_score']:.3f}" if result['risk_score'] is not None else "N/A"
    print(f"Risk Score: {risk_score_str}")
    print(f"Decision: {result['decision']}")
    print(f"Status: {result['status']}")
    print(f"Details: {result['details']}")

    # Test 3: High risk transaction (BLOCK) - should fail due to insufficient balance
    print("\n\nTest 3: Insufficient balance")
    result = env.process_transaction({
        "from_vpa": "bob@phonepe",
        "to_vpa": "merchant@ybl",
        "amount": 50000.0,
        "timestamp": datetime.now().isoformat()
    })
    print(f"Transaction ID: {result['transaction_id']}")
    risk_score_str = f"{result['risk_score']:.3f}" if result['risk_score'] is not None else "N/A"
    print(f"Risk Score: {risk_score_str}")
    print(f"Decision: {result['decision']}")
    print(f"Status: {result['status']}")
    print(f"Details: {result['details']}")

    # Check balances
    print("\n\nAccount Balances:")
    print(f"  alice@paytm: ₹{env.get_account_balance('alice@paytm'):,.2f}")
    print(f"  bob@phonepe: ₹{env.get_account_balance('bob@phonepe'):,.2f}")
    print(f"  merchant@ybl: ₹{env.get_account_balance('merchant@ybl'):,.2f}")
    assert env.get_account_balance("alice@paytm") == 24500
    assert env.get_account_balance("bob@phonepe") == 30500
    assert sum(a.balance for a in env.accounts.values()) == 180000


def test_threshold_configurations(env):
    """Test different threshold configurations"""
    print_section("3. Threshold Configuration Testing")

    # Reset environment for clean test
    env.reset_statistics()

    # Test with conservative thresholds
    print("\nTest with CONSERVATIVE thresholds (flag: 0.30, block: 0.60)")
    env.update_thresholds(flag_threshold=0.30, block_threshold=0.60)

    result = env.process_transaction({
        "from_vpa": "bob@phonepe",
        "to_vpa": "alice@paytm",
        "amount": 5000.0,
        "timestamp": datetime.now().isoformat()
    })
    print(f"Small transaction - Risk: {result['risk_score']:.3f}, Decision: {result['decision']}")

    # Reset and test with aggressive thresholds
    print("\n\nTest with AGGRESSIVE thresholds (flag: 0.50, block: 0.80)")
    env.update_thresholds(flag_threshold=0.50, block_threshold=0.80)

    result = env.process_transaction({
        "from_vpa": "bob@phonepe",
        "to_vpa": "merchant@ybl",
        "amount": 5000.0,
        "timestamp": datetime.now().isoformat()
    })
    print(f"Same transaction - Risk: {result['risk_score']:.3f}, Decision: {result['decision']}")
    assert env.threshold_config.flag_threshold == 0.5
    assert sum(a.balance for a in env.accounts.values()) == 180000


def test_sequential_transactions(env):
    """Test sequential transaction processing"""
    print_section("4. Sequential Transaction Processing")

    env.reset_statistics()
    env.update_thresholds(flag_threshold=0.40, block_threshold=0.70)

    transactions = [
        {"from_vpa": "alice@paytm", "to_vpa": "bob@phonepe", "amount": 1000.0},
        {"from_vpa": "alice@paytm", "to_vpa": "merchant@ybl", "amount": 2000.0},
        {"from_vpa": "bob@phonepe", "to_vpa": "merchant@ybl", "amount": 500.0},
        {"from_vpa": "alice@paytm", "to_vpa": "bob@phonepe", "amount": 3000.0},
        {"from_vpa": "bob@phonepe", "to_vpa": "alice@paytm", "amount": 1500.0},
    ]

    print("\nProcessing sequence of transactions...")
    for i, txn in enumerate(transactions, 1):
        txn["timestamp"] = datetime.now().isoformat()
        result = env.process_transaction(txn)
        risk_str = f"{result['risk_score']:.3f}" if result['risk_score'] is not None else "N/A"
        print(f"  {i}. {txn['from_vpa']} → {txn['to_vpa']}: ₹{txn['amount']:,.0f} "
              f"[{result['decision']}] (risk: {risk_str})")
    assert env.stats["total_transactions"] >= 5
    assert sum(a.balance for a in env.accounts.values()) == 180000


def test_statistics_and_history(env):
    """Test statistics and transaction history"""
    print_section("5. Statistics and History")

    # Get overall statistics
    stats = env.get_statistics()
    assert stats["total_balance"] == 180000
    print("\nEnvironment Statistics:")
    print(f"  Total Transactions: {stats['total_transactions']}")
    print(f"  Allowed: {stats['allowed']}")
    print(f"  Flagged: {stats['flagged']}")
    print(f"  Blocked: {stats['blocked']}")
    print(f"  Failed: {stats['failed']}")
    print(f"  Total Accounts: {stats['accounts']}")
    print(f"  Total VPAs: {stats['vpas']}")
    print(f"  Total Balance in System: ₹{stats['total_balance']:,.2f}")

    # Get transaction history for specific VPA
    print("\n\nTransaction History for alice@paytm (last 5):")
    history = env.get_transaction_history(vpa_id="alice@paytm", limit=5)
    for txn in history:
        direction = "→" if txn['from_vpa'] == "alice@paytm" else "←"
        other_vpa = txn['to_vpa'] if direction == "→" else txn['from_vpa']
        risk_str = f"{txn['risk_score']:.3f}" if txn['risk_score'] is not None else "N/A"
        print(f"  {direction} {other_vpa}: ₹{txn['amount']:,.2f} "
              f"[{txn['status']}] (risk: {risk_str})")


def main():
    """Main test function"""
    print("\n" + "="*60)
    print("  UPI ENVIRONMENT SIMULATOR - TEST & DEMONSTRATION")
    print("="*60)

    try:
        # Run all tests
        env = setup_environment()
        test_transaction_processing(env)
        test_threshold_configurations(env)
        test_sequential_transactions(env)
        test_statistics_and_history(env)

        print_section("SUCCESS")
        print("\nAll tests completed successfully!")
        print("\nKey Features Demonstrated:")
        print("  ✓ Account and VPA management")
        print("  ✓ Transaction processing with risk assessment")
        print("  ✓ Configurable decision thresholds (ALLOW/FLAG/BLOCK)")
        print("  ✓ Sequential transaction support")
        print("  ✓ Transaction history and statistics")
        print("\nThe UPI Environment is ready for integration with fraud detectors!")

    except Exception as e:
        print(f"\n\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
