import os
import yaml
import time
from datetime import datetime
from flask import Blueprint, request
from sloy.helpers.config import load_config
from sloy.helpers.time_converter import convert_to_seconds
from sloy.helpers.validate import validate_slo_config

compute_blueprints = Blueprint('compute', __name__)

@compute_blueprints.route('/validate', methods=['POST'])
def validate():
    # Get SLO Config
    data = str(request.get_data().decode('utf-8'))
    data = yaml.safe_load(data)

    # Validate SLO Config
    try:
        validate_slo_config(data)
    except Exception:
        return {"error": "Configuration Error, unable to validate SLO config"}, 400
    
    return {"status": "ok"}, 200

@compute_blueprints.route('/compute', methods=['POST'])
def compute():
    # Track current time
    start_time = time.time()
    
    # Check what type of data is being sent using headers and get SLO Config
    if request.headers.get('Content-Type') == 'application/json':
        data = request.get_json()
    else:
        data = str(request.get_data().decode('utf-8'))
        data = yaml.safe_load(data)

    # Validate SLO Config
    try:
        validate_slo_config(data)
    except Exception:
        return {"error": "Configuration Error, unable to validate SLO config"}, 400

    # Load global config
    config_path = os.getenv('CONFIG_PATH', 'config.yaml')
    config = {}
    try:
        config = load_config(config_path)
    except Exception:
        return {"error": "Server Configuration Error, unable to load config file"}, 500

    # Load backend config
    backend_config = config["backends"]
    backend = data["backend"]
    if backend not in backend_config:
        return {"error": f"Configuration Error, Backend {backend} not found in config"}, 404
    
    # Load backend module
    backend_module = __import__(f"sloy.backends.{backend}", fromlist=[f"sloy.backends.{backend}"])
    backend_class = getattr(backend_module, f"{backend.capitalize()}Backend")
    backend_instance = backend_class(**backend_config[backend])

    # Check if exporter is defined
    exports = False
    if data.get("exporters"):
        exports = True

    # Load exporter config if it exists
    if exports:
        exporter_config = config["exporters"]
        exporters = data["exporters"]
        exporter_instances = {}
        for exporter in exporters:
            if isinstance(exporter, dict):
                exporter_name: str = list(exporter.keys())[0]
            else:
                exporter_name = exporter
            if exporter_name not in exporter_config:
                return {"error": f"Configuration Error, Exporter {exporter_name} not found in config"}, 404
        
            # Load exporter module
            exporter_module = __import__(f"sloy.exporters.{exporter_name}", fromlist=[f"sloy.exporters.{exporter_name}"])
            exporter_class = getattr(exporter_module, f"{exporter_name.capitalize()}")
            exporter_instance = exporter_class()
            if isinstance(exporter, dict):
                exporter_instances[exporter_name] = (exporter_instance, exporter[exporter_name])
            else:
                exporter_instances[exporter_name] = exporter_instance

    # Get time window and convert it to seconds
    time_window = data["time_window"]
    try:
        time_window_seconds = convert_to_seconds(time_window)
    except ValueError:
        return {"error": f"Configuration Error, {time_window} is not a valid time_window"}, 400
    
    # Compute SLO
    timestamp = int(time.time())
    try:
        slo = backend_instance.compute(timestamp, time_window_seconds, data)
    except Exception:
        return {"error": "Backend Error, unable to compute SLO"}, 500
    
    if exports:
        try:
            for exporter, exporter_instance in exporter_instances.items():
                if isinstance(exporter_instance, tuple):
                    exporter_instance, supplied_config = exporter_instance
                    exporter_instance.export(slo, data, supplied_config, **exporter_config[exporter])
                else:
                    exporter_instance.export(slo, data, None, **exporter_config[exporter])
        except Exception:
            return {"error": "Exporter Error, unable to export SLO"}, 500

    # Prepare response
    response = {
        "name": data["name"],
        "result": slo,
        "timestamp": datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S'),
        "time_window": time_window,
        "elapsed_time": round((time.time() - start_time), 5),
        "exporters": list(exporter_instances.keys()) if exports else None
    }

    return response, 200
