import pytest
import os
import yaml
from src.lumber_estimator.core.config import load_project_config, ConfigError

def test_load_project_config_success(tmp_path):
    # Setup
    project_dir = tmp_path / "projects" / "test-proj"
    project_dir.mkdir(parents=True)
    yaml_content = {
        'project': {
            'name': 'Test Project',
            'files': {'parts': 'parts.csv'}
        }
    }
    with open(project_dir / "project.yaml", "w") as f:
        yaml.dump(yaml_content, f)
    
    # Execute
    config = load_project_config("test-proj", base_dir=str(tmp_path / "projects"))
    
    # Verify
    assert config['name'] == 'Test Project'
    assert config['files']['parts'] == 'parts.csv'
    assert config['dir'] == str(project_dir)

def test_load_project_config_missing_file():
    with pytest.raises(ConfigError, match="Configuration file not found"):
        load_project_config("non-existent-project", base_dir="projects")

def test_load_project_config_invalid_yaml(tmp_path):
    project_dir = tmp_path / "projects" / "bad-yaml"
    project_dir.mkdir(parents=True)
    with open(project_dir / "project.yaml", "w") as f:
        f.write("invalid: yaml: :")
    
    with pytest.raises(ConfigError, match="Error parsing YAML file"):
        load_project_config("bad-yaml", base_dir=str(tmp_path / "projects"))

def test_load_project_config_missing_root_key(tmp_path):
    project_dir = tmp_path / "projects" / "no-root"
    project_dir.mkdir(parents=True)
    with open(project_dir / "project.yaml", "w") as f:
        yaml.dump({'not_project': {}}, f)
    
    with pytest.raises(ConfigError, match="Invalid config format: missing 'project' root key"):
        load_project_config("no-root", base_dir=str(tmp_path / "projects"))
