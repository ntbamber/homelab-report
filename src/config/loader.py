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
    load_dotenv()

    # 1. Explicit Argument or Environment Variable (Docker)
    path_str = custom_path or os.getenv("CONFIG_PATH")

    if path_str:
        config_path = Path(path_str)
    else:
        # 2. Fallback: Local Development Path
        config_path = Path(__file__).resolve().parents[2] / "config" / "config.yaml"

    # Validation
    if not config_path.exists() or not config_path.is_file():
        raise FileNotFoundError(
            f"Config file not found at: {config_path}\n"
            f"Current working dir: {os.getcwd()}"
        )

    logger.info(f"Loading config from: {config_path}")

    # Parsing: Read and expand variables (Keep this exactly as is)
    variable_pattern = re.compile(r'\$\{([^}^:]+)(?::([^}]*))?\}')

    def expand_vars(match):
        env_var = match.group(1)
        default_val = match.group(2) if match.group(2) is not None else match.group(0)
        return os.getenv(env_var, default_val)

    with open(config_path, "r") as f:
        raw_content = f.read()

    expanded_content = variable_pattern.sub(expand_vars, raw_content)
    
    try:
        config_data = yaml.safe_load(expanded_content)
        return AppConfig(**config_data)
    except yaml.YAMLError as e:
        raise ValueError(f"Error parsing YAML file at {config_path}: {e}")