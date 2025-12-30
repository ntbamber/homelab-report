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

    candidates = []

    # 1. Explicit Argument (if passed in code)
    if custom_path:
        candidates.append(Path(custom_path))

    # 2. Environment Variable (if set in .env or Docker)
    env_path = os.getenv("CONFIG_PATH")
    if env_path:
        candidates.append(Path(env_path))

    # 3. Standard Docker Path (Hardcoded safe bet)
    candidates.append(Path("/app/config/config.yaml"))

    # 4. Sibling Check (If config.yaml is right next to loader.py)
    #    Useful if you used the "Mount Single File" fix
    candidates.append(Path(__file__).parent / "config.yaml")

    # 5. Parent Check (If loader is in /src/config but config is in /config)
    #    Useful if you moved code into /src/ structure
    candidates.append(Path(__file__).parent.parent.parent / "config" / "config.yaml")

    # EXECUTION: Find the first one that exists
    final_path = None
    for path in candidates:
        try:
            # resolve() fixes ".." paths to make them absolute
            if path.resolve().exists() and path.resolve().is_file():
                final_path = path
                break
        except (OSError, ValueError):
            continue

    if not final_path:
        # Debug info: Print all paths we tried so you know why it failed
        checked_paths = "\n".join([str(p) for p in candidates])
        raise FileNotFoundError(
            f"Config file not found! Checked the following locations:\n{checked_paths}\n"
            f"Current working dir: {os.getcwd()}"
        )

    logger.info(f"Loading config from: {final_path}")

    # PARSING: Read and expand variables
    variable_pattern = re.compile(r'\$\{([^}^:]+)(?::([^}]*))?\}')

    def expand_vars(match):
        env_var = match.group(1)
        default_val = match.group(2) if match.group(2) is not None else match.group(0)
        return os.getenv(env_var, default_val)

    with open(final_path, "r") as f:
        raw_content = f.read()

    expanded_content = variable_pattern.sub(expand_vars, raw_content)
    
    try:
        config_data = yaml.safe_load(expanded_content)
        return AppConfig(**config_data)
    except yaml.YAMLError as e:
        raise ValueError(f"Error parsing YAML file at {final_path}: {e}")