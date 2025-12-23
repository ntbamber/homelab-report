import os
import re
import yaml
from pathlib import Path
from dotenv import load_dotenv
from .schema import AppConfig

def load_config(config_path: str = "config/config.yaml") -> AppConfig:
    load_dotenv()

    # 1. Try the explicit Docker path first (Most reliable for Portainer)
    path = Path("/app/config/config.yaml")

    # 2. If not found, look relative to the script (For local testing)
    if not path.exists():
        # Based on your image: loader.py is inside /config/
        # So we go up 2 levels: config/ -> root/ -> then add config/config.yaml
        current_dir = Path(__file__).parent
        project_root = current_dir.parent  # Adjusted for your structure
        path = project_root / "config" / "config.yaml"

    if not path.exists():
        print(f"DEBUG: Scanned for config at: {path}")
        raise FileNotFoundError(f"Config file not found at: {path}")

    # 3. Read and expand variables
    with open(path, "r") as f:
        content = f.read()

    pattern = re.compile(r'\$\{([^}^:]+)\}')
    def replace_env(match):
        env_var = match.group(1)
        return os.getenv(env_var, match.group(0))

    expanded_content = pattern.sub(replace_env, content)
    config_data = yaml.safe_load(expanded_content)
    
    return AppConfig(**config_data)