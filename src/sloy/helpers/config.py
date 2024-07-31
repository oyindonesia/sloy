import yaml
import os
import re

def replace_env_vars(config):
    pattern = re.compile(r'\$\{(\w+)\}')
    for key, value in config.items():
        if isinstance(value, dict):
            config[key] = replace_env_vars(value)
        elif isinstance(value, str):
            matches = pattern.findall(value)
            for match in matches:
                value = value.replace(f'${{{match}}}', os.environ.get(match, ''))
            config[key] = value
    return config

def load_config(config_path):
    config = {}

    with open(config_path, 'r') as stream:
        try:
            config = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            raise exc

    # Replace environment variables in config
    config = replace_env_vars(config)

    return config
