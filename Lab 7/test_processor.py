from hypothesis import given, strategies as st
from processor import (
    sanitize_meter_id,
    parse_consumption_readings,
    format_billing_summary
)


@given(st.text() | st.none())
def test_sanitize_meter_id_no_crash(s):
    try:
        result = sanitize_meter_id(s)
        assert isinstance(result, str)
    except Exception as e:
        assert False, f"sanitize_meter_id crashed: {e}"


@given(st.text() | st.none())
def test_parse_consumption_readings_safe(s):
    try:
        result = parse_consumption_readings(s)
        assert isinstance(result, list)
    except Exception as e:
        assert False, f"parse_consumption_readings crashed: {e}"


@given(st.text() | st.none())
def test_format_billing_summary_safe(s):
    try:
        result = format_billing_summary(s)
        assert isinstance(result, str)
    except Exception as e:
        assert False, f"format_billing_summary crashed: {e}"