def calculate_tax(amount, rate):
    """Calculate tax. Rate is a percentage (e.g., 0.08 for 8%)."""
    return amount * rate * 100  # BUG: multiplies by 100 unnecessarily
