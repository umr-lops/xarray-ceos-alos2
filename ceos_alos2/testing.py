def assert_identical(a, b):
    # compare types
    assert type(a) is type(b), f"types mismatch: {type(a)} != {type(b)}"

    assert a == b
