from doorkeeper import demo_function


def test_demo_function():
    """
    Test ``doorkeeper.demo_function()`` functionality.
    """
    assert demo_function() == 1
