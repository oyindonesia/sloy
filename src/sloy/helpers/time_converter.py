def convert_to_seconds(time_window: str):
    """ Convert time window to seconds """
    # Check if time window is in the correct format
    if not time_window[:-1].isdigit():
        raise ValueError()

    if time_window.endswith("s"):
        return int(time_window[:-1])
    elif time_window.endswith("m"):
        return int(time_window[:-1]) * 60
    elif time_window.endswith("h"):
        return int(time_window[:-1]) * 60 * 60
    elif time_window.endswith("d"):
        return int(time_window[:-1]) * 60 * 60 * 24
    elif time_window.endswith("w"):
        return int(time_window[:-1]) * 60 * 60 * 24 * 7
