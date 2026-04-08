import yaml
import os

class ConfigError(Exception):
    pass

def load_project_config(project_name: str, base_dir: str = "projects"):
    project_dir = os.path.join(base_dir, project_name)
    yaml_path = os.path.join(project_dir, "project.yaml")
    
    if not os.path.exists(yaml_path):
        raise ConfigError(f"Configuration file not found: {yaml_path}")
        
    with open(yaml_path, 'r') as f:
        try:
            config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ConfigError(f"Error parsing YAML file: {e}")
            
    if not config or 'project' not in config:
        raise ConfigError("Invalid config format: missing 'project' root key.")
        
    config['project']['dir'] = project_dir
        
    return config['project']
