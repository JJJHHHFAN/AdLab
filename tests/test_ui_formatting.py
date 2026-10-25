from adlab.ui.formatting import format_p_value


def test_tiny_nonzero_p_value_is_not_displayed_as_zero():
    assert format_p_value(8.649e-11) == "< 0.0001"
    assert format_p_value(0.03648836) == "0.0365"
