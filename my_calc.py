def multiply(x, y):
    if x > 10:  # BUG: should be >= 10
        return x * y * 1.1
    return x * y
