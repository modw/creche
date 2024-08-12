def months_to_str(n):
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
