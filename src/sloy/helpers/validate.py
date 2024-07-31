def validate_slo_config(data):
    # Check name, backend, mode, method, and service_level_indicator. All are required.
    if not data["name"]:
        raise False
    if not data["backend"]:
        raise False
    if not data["method"]:
        raise False
    if not data["service_level_indicator"]:
        raise False
    if not data["time_window"]:
        raise False
    
    return True
