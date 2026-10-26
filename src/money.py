"""Decimal arithmetic at the existing float API boundary.

Do not round detector inputs or impose a new integer-only amount contract.
Decimal(str(x)) preserves the declared decimal value. Cent-valued prototype
inputs consequently accumulate as exact minor units, rather than binary sums.
"""
from decimal import Decimal


def decimal_money(value):
    return Decimal(str(value))


def add_money(left, right):
    return float(decimal_money(left) + decimal_money(right))


def subtract_money(left, right):
    return float(decimal_money(left) - decimal_money(right))


def at_least(left, right):
    return decimal_money(left) >= decimal_money(right)
