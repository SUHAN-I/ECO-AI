from main_logic import add_numbers

def test_addition_works():
    # This is an "assertion" — it checks if the result is 5
    assert add_numbers(2, 3) == 5

def test_addition_fails():
    # This will fail if the math is wrong
    assert add_numbers(1, 1) == 2
