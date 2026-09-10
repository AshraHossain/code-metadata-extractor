"""Test file fixture — mirrors sample_module to exercise coverage inference."""


def test_simple_function():
    from tests.fixtures.sample_module import simple_function
    assert simple_function(1, 2) == 3


def test_no_docstring():
    from tests.fixtures.sample_module import no_docstring
    assert no_docstring(3, 4) == 12
