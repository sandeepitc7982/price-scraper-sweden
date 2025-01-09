from datetime import datetime, timedelta, timezone


def today_dashed_str():
    return datetime.today().strftime("%Y-%m-%d")


def current_timestamp_dashed_str_with_timezone():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S %Z")


def today_dashed_str_with_key():
    return f"date={today_dashed_str()}"


def yesterday_dashed_str():
    return (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d")


def yesterday_timestamp_dashed_str_with_timezone():
    return (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S %Z")


def yesterday_dashed_str_with_key():
    return f"date={yesterday_dashed_str()}"
