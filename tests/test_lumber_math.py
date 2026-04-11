import pytest
from src.lumber_estimator.core.dimensions import parse_fraction, calculate_bf, calculate_sqft, format_fraction

def test_parse_fraction():
    assert parse_fraction("54 1/4") == 54.25
    assert parse_fraction("1/2") == 0.5
    assert parse_fraction("10") == 10.0
    assert parse_fraction(12.5) == 12.5
    assert parse_fraction("") == 0.0
    assert parse_fraction(None) == 0.0

def test_calculate_bf():
    # 12" x 12" x 1" (4/4) = 1 BF
    assert calculate_bf(12, 12, "4/4") == 1.0
    # 12" x 12" x 2" (8/4) = 2 BF
    assert calculate_bf(12, 12, "8/4") == 2.0
    # 6" x 12" x 1" (4/4) = 0.5 BF
    assert calculate_bf(6, 12, "4/4") == 0.5
    # Default thickness 4/4
    assert calculate_bf(12, 12, "unknown") == 1.0

def test_calculate_sqft():
    # 12" x 12" = 1 SQFT
    assert calculate_sqft(12, 12) == 1.0
    # 24" x 24" = 4 SQFT
    assert calculate_sqft(24, 24) == 4.0

def test_format_fraction():
    assert format_fraction(1.25) == "1 1/4"
    assert format_fraction(0.5) == "1/2"
    assert format_fraction(10) == "10"
    assert format_fraction(0) == "0"
    # Rounding to 1/64
    assert format_fraction(1.0 / 3.0) == "21/64" # 0.333 -> 21.3/64 -> 21/64
