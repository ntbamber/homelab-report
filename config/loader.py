import os
import re
import yaml
import logging
from pathlib import Path
from dotenv import load_dotenv
from .schema import AppConfig

# Logging setup
logger = logging.getLogger(__name__)

def load_config(custom_path: str = None) -> AppConfig:
    """
    Load configuration with the following priority:
    1. Path passed as argument
    2. Path in CONFIG_PATH environment variable
    3. 'config.yaml' in the same directory as this script
    """
    load_dotenv()

    # 1. Determine path
    env_path = os.getenv("CONFIG_PATH")
    
    if custom_path:
        path = Path(custom_path)
    elif env_path:
        path = Path(env_path)
    else:
        # Fallback: Look for config.yaml in the SAME folder as loader.py
        path = Path(__file__).parent / "config.yaml"

    # 2. Verify existence
    if not path.exists():
        # Debug info showing where was searched
        raise FileNotFoundError(
            f"Config file not found! Scanned path: {path.resolve()}\n"
            f"Current working dir: {os.getcwd()}"
        )

    logger.info(f"Loading config from: {path}")

    # 3. Read and expand variables (Regex)
    # Allow ${VAR} or ${VAR:default} syntax
    variable_pattern = re.compile(r'\$\{([^}^:]+)(?::([^}]*))?\}')

    def expand_vars(match):
        env_var = match.group(1)
        default_val = match.group(2) if match.group(2) is not None else match.group(0)
        return os.getenv(env_var, default_val)

    with open(path, "r") as f:
        raw_content = f.read()

    expanded_content = variable_pattern.sub(expand_vars, raw_content)
    
    # 4. Parse YAML
    try:
        config_data = yaml.safe_load(expanded_content)
        return AppConfig(**config_data)
    except yaml.YAMLError as e:
        raise ValueError(f"Error parsing YAML file: {e}")