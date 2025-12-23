import os
import re
import yaml
from pathlib import Path
from dotenv import load_dotenv
from .schema import AppConfig

def load_config(config_path: str = "config/config.yaml") -> AppConfig:
    """
    Load configuration from YAML file with environment variable expansion.
    """
    load_dotenv()

    #check if it exists at the exact path given
    path = Path(config_path)
    
    #If not absolute, try the standard Docker path
    if not path.is_absolute():
        docker_path = Path("/app/config/config.yaml")
        if docker_path.exists():
            path = docker_path
        else:
            #Fallback: Try relative to this script (for local dev)
            # Go up until we find the folder containing 'config' or 'main.py'
            current_dir = Path(__file__).parent
            # Try 2 levels up (standard structure)
            if (current_dir.parent.parent / config_path).exists():
                path = current_dir.parent.parent / config_path
            # Try 1 level up (flat structure)
            elif (current_dir.parent / config_path).exists():
                path = current_dir.parent / config_path
            
    if not path.exists():
        # Print current directory to help debug if it fails again
        print(f"DEBUG: Current working directory: {os.getcwd()}")
        print(f"DEBUG: Script location: {__file__}")
        raise FileNotFoundError(f"Config file not found at: {path}")

    # Read the file as text
    with open(path, "r") as f:
        content = f.read()

    # Regex to find ${VAR_NAME} and replace with os.getenv('VAR_NAME')
    pattern = re.compile(r'\$\{([^}^:]+)\}')

    def replace_env(match):
        env_var = match.group(1)
        return os.getenv(env_var, match.group(0))

    expanded_content = pattern.sub(replace_env, content)

    # Parse and Validate
    config_data = yaml.safe_load(expanded_content)
    return AppConfig(**config_data)