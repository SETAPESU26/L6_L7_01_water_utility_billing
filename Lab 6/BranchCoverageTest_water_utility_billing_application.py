"""Branch coverage tests for every decision in the Water Utility Billing application."""

import pytest

from water_utility_billing import calculate_water_bill, check_meter_tampering


def test_validation_short_circuit_and_both_invalid_cases():
    """Covers a valid list, invalid non-list (left side true), and negative fee (right side true)."""
    assert calculate_water_bill([], 0) == {"total_billed": 0.0, "status": "NO_ACTIVITY"}
    with pytest.raises(ValueError):
        calculate_water_bill({}, 0)
    with pytest.raises(ValueError):
        calculate_water_bill([], -1)


def test_account_activity_and_default_branches():
    """Covers inactive and active accounts, plus default values for all optional account keys."""
    result = calculate_water_bill(
        [
            {"is_active": False, "usage_blocks": [10]},
            {"is_active": True, "usage_blocks": [1]},
            {"usage_blocks": [10]},
        ],
        2,
    )
    assert result == {"total_billed": 3.5, "status": "NORMAL"}


def test_usage_boundaries_and_nonpositive_true_false_paths():
    """Covers <=0 true/false, >100 false, >50 true at 51, and >50 false at 50."""
    result = calculate_water_bill(
        [{"is_active": True, "usage_blocks": [-1, 0, 50, 51, 100]}], 0
    )
    assert result == {"total_billed": 452.5, "status": "NORMAL"}


def test_over_100_residential_break_and_commercial_continuation():
    """Covers >100, noncommercial true/break, and commercial true/no-break paths."""
    result = calculate_water_bill(
        [
            {"is_active": True, "usage_blocks": [101, 100]},
            {"is_active": True, "is_commercial": True, "usage_blocks": [101, 50]},
        ],
        10,
    )
    # Residential: 10 + 101*4.5; commercial: 10 + 101*3.5 + 50*1.5.
    assert result == {"total_billed": 903.0, "status": "NORMAL"}


def test_waiver_true_and_false_with_strict_200_boundary():
    """Covers waiver absent/false/true and acct_total >200 true and false at exactly 200."""
    result = calculate_water_bill(
        [
            {"is_active": True, "usage_blocks": [100]},
            {"is_active": True, "usage_blocks": [101], "has_leak_waiver": True},
            {"is_active": True, "usage_blocks": [80], "has_leak_waiver": True},
        ],
        0,
    )
    assert result == {"total_billed": 854.5, "status": "NORMAL"}


def test_flag_status_boundary_and_zero_total_status():
    """Covers flags >5 false at five/true at six and total_billed ==0 true/false."""
    five = calculate_water_bill(
        [{"is_active": True, "usage_blocks": [-1, -1, -1, -1, -1]}], 1
    )
    six = calculate_water_bill(
        [{"is_active": True, "usage_blocks": [-1, -1, -1, -1, -1, -1]}], 1
    )
    zero = calculate_water_bill([], 0)
    assert five["status"] == "NORMAL"
    assert six["status"] == "EXCESSIVE_FLAGS"
    assert zero["status"] == "NO_ACTIVITY"


def test_meter_matrix_empty_and_nonempty_paths():
    """Covers the no-data condition true and false, then the no-tamper return."""
    assert check_meter_tampering([]) == "NO_DATA"
    assert check_meter_tampering([[]]) == "CLEAR"


def test_meter_negative_delta_count_threshold_and_reset():
    """Covers negative true/false, count >=2 false/true, and reset after nonnegative delta."""
    assert check_meter_tampering([[0, -1, 2, -3]]) == "CLEAR"
    assert check_meter_tampering([[-1, -2]]) == "TAMPER_SUSPECTED"


def test_invalid_fee_type_preserves_native_type_error():
    """A fee incomparable with zero follows the application's native TypeError behavior."""
    with pytest.raises(TypeError):
        calculate_water_bill([], "not-a-number")
