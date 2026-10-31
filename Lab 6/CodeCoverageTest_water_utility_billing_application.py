"""Line coverage tests for the Water Utility Billing application."""

import pytest

from water_utility_billing import calculate_water_bill, check_meter_tampering


def test_bill_applies_usage_tiers_and_skips_nonpositive_blocks():
    """Zero/negative blocks add no charge; 50 is lower tier, 51 and 100 upper tier."""
    result = calculate_water_bill(
        [{"is_active": True, "usage_blocks": [0, -4, 50, 51, 100]}], 10
    )
    assert result == {"total_billed": 462.5, "status": "NORMAL"}


def test_residential_over_100_flags_and_stops_processing_that_account():
    """Residential >100 adds 4.5x, flags, and breaks before later blocks."""
    result = calculate_water_bill(
        [{"is_active": True, "usage_blocks": [101, 30]}], 10
    )
    assert result == {"total_billed": 464.5, "status": "NORMAL"}


def test_commercial_over_100_flags_but_continues_through_later_blocks():
    """Commercial >100 adds 3.5x without breaking; the following 50 is still billed."""
    result = calculate_water_bill(
        [{"is_active": True, "is_commercial": True, "usage_blocks": [101, 50]}], 10
    )
    assert result == {"total_billed": 438.5, "status": "NORMAL"}


def test_inactive_accounts_are_ignored_and_missing_active_flag_defaults_false():
    """Inactive accounts, including one with no is_active field, add nothing."""
    result = calculate_water_bill(
        [{"is_active": False, "usage_blocks": [20]}, {"usage_blocks": [40]}], 8
    )
    assert result == {"total_billed": 0.0, "status": "NO_ACTIVITY"}


def test_leak_waiver_subtracts_50_only_when_account_total_exceeds_200():
    """A qualifying high bill is reduced by 50; an exact 200 bill receives no reduction."""
    result = calculate_water_bill(
        [
            {"is_active": True, "usage_blocks": [101], "has_leak_waiver": True},
            {"is_active": True, "usage_blocks": [80], "has_leak_waiver": True},
        ],
        0,
    )
    # First: 101*4.5 - 50 = 404.5; second: 80*2.5 = exactly 200, without deduction.
    assert result == {"total_billed": 604.5, "status": "NORMAL"}


def test_more_than_five_flagged_blocks_sets_excessive_flags_status():
    """Six nonpositive blocks flag an account six times and exceed the status limit."""
    result = calculate_water_bill(
        [{"is_active": True, "usage_blocks": [-1, 0, -2, 0, -3, 0]}], 1
    )
    assert result == {"total_billed": 1.0, "status": "EXCESSIVE_FLAGS"}


def test_five_flags_remain_normal_and_zero_total_selects_no_activity():
    """Exactly five flags do not exceed the cutoff; zero total selects NO_ACTIVITY."""
    exactly_five = calculate_water_bill(
        [{"is_active": True, "usage_blocks": [-1, 0, -2, 0, -3]}], 0
    )
    zero_total = calculate_water_bill([], 0)
    assert exactly_five == {"total_billed": 0.0, "status": "NO_ACTIVITY"}
    assert zero_total == {"total_billed": 0.0, "status": "NO_ACTIVITY"}


@pytest.mark.parametrize(
    "accounts, base_fee",
    [(({},), 1), ([], -0.01)],
)
def test_invalid_accounts_or_negative_base_fee_raise_value_error(accounts, base_fee):
    """The implemented validation rejects non-list accounts and a negative fee."""
    with pytest.raises(ValueError, match="Invalid accounts list or base fee"):
        calculate_water_bill(accounts, base_fee)


def test_empty_meter_matrix_returns_no_data():
    """An empty readings matrix has its dedicated NO_DATA result."""
    assert check_meter_tampering([]) == "NO_DATA"


def test_meter_without_two_consecutive_negative_deltas_is_clear():
    """No readings, a negative streak reset by a nonnegative delta, and separate meters clear."""
    assert check_meter_tampering([[], [-1, 0, -2], [-3]]) == "CLEAR"


def test_two_consecutive_negative_deltas_trigger_tamper_suspected():
    """Two adjacent negative deltas in one meter return TAMPER_SUSPECTED."""
    assert check_meter_tampering([[1, -1, -0.01, 4]]) == "TAMPER_SUSPECTED"
