def months_to_str(n):
    """
    Converts the given number of months to a string representation in years and months.

    Args:
        n (int): The number of months.

    Returns:
        str: The string representation of the number of months in years and months.
    """

    years = n // 12
    months = n % 12

    if years == 0:
        year_str = ""
        if months == 1:
            month_str = "1 month"
        else:
            month_str = f"{months} months"
    elif years == 1:
        year_str = "1 year"
        if months == 0:
            month_str = ""
        elif months == 1:
            month_str = "1 month"
        else:
            month_str = f"{months} months"
    else:
        year_str = f"{years} years"
        if months == 0:
            month_str = ""
        elif months == 1:
            month_str = "1 month"
        else:
            month_str = f"{months} months"
    return f"{year_str} {month_str}"
